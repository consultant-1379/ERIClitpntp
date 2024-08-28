##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from datetime import datetime
from netaddr import IPNetwork
import re

from litp.core.plugin import Plugin
from litp.core.validators import ValidationError
from litp.core.execution_manager import ConfigTask
from litp.core.litp_logging import LitpLogger
log = LitpLogger()


class NtpPlugin(Plugin):
    """
    LITP ntp plugin
    """

    def validate_model(self, plugin_api_context):
        """
        Validation method used to check if the hostname is valid.
        The rules used for this validation are:

        - hostname is a string consisting of only alphanumeric characters \
          and dots.

        - hostname may not end in a dot.

        - hostname may not begin with a dot.

        - hostname may have multiple parts, each alphanumeric,
          and each separated by a dot.

        In case one of these rules is broken the method returns with \
        a list of errors.
        """
        errors = []

        #validate ony one ntp-service item per node
        ms = plugin_api_context.query("ms")
        nodes = plugin_api_context.query("node")
        all_nodes = ms + nodes
        for node in all_nodes:
            errors += self._validate_only_one_ntp_service(node)
        return errors

    def _services_in_initial_and_forremoval(self, node):
        # will return True if all the ntp services in that node are either in
        # initial or for_removal state
        services = node.query("ntp-service")
        if len(services) < 2:
            return False
        return services[0].is_for_removal() and services[1].is_initial() or\
            services[0].is_initial() and services[1].is_for_removal()

    def _services_in_applied_and_forremoval(self, node):
        # will return True if all the ntp services in that node are either in
        # initial or for_removal state
        services = node.query("ntp-service")
        if len(services) < 2:
            return False
        return services[0].is_for_removal() and services[1].is_applied() or\
            services[0].is_applied() and services[1].is_for_removal()

    def _validate_only_one_ntp_service(self, node):
        """Method validates that there is only one ntp service per node
        """
        errors = []
        preamble = "_validate_only_one_ntp_service: "
        ntp_services = node.query("ntp-service")
        if len(ntp_services) > 2:
            msg = self._generate_duplicate_ntp_error(preamble, ntp_services)
            errors.append(ValidationError(error_message=msg))
        elif len(ntp_services) == 2 and \
             not (self._services_in_initial_and_forremoval(node) or \
                 self._services_in_applied_and_forremoval(node)):
            msg = self._generate_duplicate_ntp_error(preamble, ntp_services)
            errors.append(ValidationError(error_message=msg))
        return errors

    @staticmethod
    def _generate_duplicate_ntp_error(preamble, ntp_services):
        v_paths = [ntp.get_vpath() for ntp \
                   in ntp_services]
        msg = "Cannot have multiple ntp-service on " \
        + "the same node/ms. See the following paths " + \
              ", ".join(v_paths) + ". "
        log.trace.debug(preamble + msg)
        return msg

    @staticmethod
    def _remove_ip_prefix(servers):
        ips_no_prefix = []
        for server in servers:
            ips_no_prefix.append(re.sub(r'\/\d+$', '', server))

        return ips_no_prefix

    def create_configuration(self, plugin_api_context):
        """
        This plugin is used to configure ntp services on a cluster of nodes.

        Parameters:

        - servers: list of all servers, which the Management Server \
          queries for synchronization.

        The plugin only works on the Initial and Update states,
        no Remove states are permitted.

        For more information, see "Introduction to NTP Configuration" \
from :ref:`LITP References <litp-references>`.

        """
        tasks = []
        ms = plugin_api_context.query("ms")
        nodes = plugin_api_context.query("node")
        all_nodes = ms + nodes
        ms_ipaddress = [
            interface.ipaddress for interface in ms[0].network_interfaces
            if interface.ipaddress is not None]
        ms_hostname = ms[0].hostname

        networks = plugin_api_context.query("network")
        networks_and_netmasks = []
        for network in networks:
            if network.subnet is not None:
                ip = IPNetwork(network.subnet)
                networks_and_netmasks.append('{net} mask {mask}'.
                                             format(net=ip.network,
                                                    mask=ip.netmask))

        for node in all_nodes:
            clients = networks_and_netmasks if node.hostname == ms_hostname \
                else []
            for ntp in node.query("ntp-service"):
                servers = [server.server for server in ntp.servers]
                #Default value if no ntp servers are defined in the model
                if not servers:
                    if node.hostname == ms_hostname:
                        servers = ['127.127.1.0']
                    else:
                        servers = ms_ipaddress
                if (self._services_in_initial_and_forremoval(node) or \
                    self._services_in_applied_and_forremoval(node)) and \
                        ntp.is_for_removal():
                    continue
                servers = NtpPlugin._remove_ip_prefix(servers)
                if ntp.is_initial():
                    msg = 'Install ntp service on node "%s"' % node.hostname
                    if self._services_in_initial_and_forremoval(node):
                        msg = 'Configure ntp service on node "%s"' \
                              % node.hostname
                    tasks.append(
                        self._create_task(node, ntp, servers, clients, msg))
                elif ntp.is_updated():
                    msg = 'Update ntp service on node "%s"' % node.hostname
                    tasks.append(
                        self._create_task(node, ntp, servers, clients, msg))
                elif ntp.is_for_removal():
                    msg = 'Remove ntp service on node "%s"' % (node.hostname)
                    if node.hostname == ms_hostname:
                        servers = ['127.127.1.0']
                    else:
                        servers = ms_ipaddress
                    tasks.append(
                        self._create_task(node, ntp, servers, clients, msg))
                elif (ntp.has_initial_dependencies() or
                      ntp.has_updated_dependencies()):
                    msg = 'Update ntp server info on node "%s"' % node.hostname
                    tasks.append(
                        self._create_task(node, ntp, servers, clients, msg))
        return tasks

    def _create_task(self, node, ntp_service, servers, clients, msg):
        task = ConfigTask(node, ntp_service, msg, call_type="ntpd::config",
                          call_id=node.hostname, clients=clients,
                          servers=servers, date=str(datetime.now()))
        # In case we configure 'ntp-service' on any node, we need to add
        # additional items (ntp-server) under the puppet task. We need to
        # make sure the status of them will be also updated to 'Applied' state
        # when the task is successfully executed. For details see: LITPCDS-7776
        task.model_items.add(ntp_service.servers)
        for server in ntp_service.servers:
            task.model_items.add(server)
        return task
