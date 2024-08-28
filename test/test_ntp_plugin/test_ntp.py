##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import unittest

from litp.extensions.core_extension import CoreExtension
from litp.core.execution_manager import ExecutionManager
from litp.core.model_manager import ModelManager
from litp.core.plugin_manager import PluginManager
from litp.core.puppet_manager import PuppetManager
from litp.core.model_type import ItemType, Child
from litp.core.plugin_context_api import PluginApiContext
from litp.core.validators import ValidationError

from ntp_plugin.ntp_plugin import NtpPlugin
from ntp_extension.ntp_extension import NtpExtension


class TestNtpPlugin(unittest.TestCase):

    def setUp(self):
        self.model = ModelManager()
        self.context = PluginApiContext(self.model)
        self.puppet_manager = PuppetManager(self.model)
        self.plugin_manager = PluginManager(self.model)
        self.execution = ExecutionManager(self.model,
                                          self.puppet_manager,
                                          self.plugin_manager)
        self.plugin_manager.add_property_types(
            CoreExtension().define_property_types())
        self.plugin_manager.add_item_types(
            CoreExtension().define_item_types())

        # Add types we defined in our model extension
        self.plugin_manager.add_property_types(
            NtpExtension().define_property_types())
        self.plugin_manager.add_item_types(
            NtpExtension().define_item_types())

        self.plugin_manager.add_default_model()

        self.plugin = NtpPlugin()
        self.plugin_manager.add_plugin('NtpPlugin',
                                       'ntp_plugin.ntp_plugin',
                                       '1.0.1-SNAPSHOT',
                                       self.plugin)

        # remove the original root item (mock the model)
        self.model.item_types.pop('root')
        self.model.register_item_type(ItemType("root",
                                               ms1=Child("ms"),
                                               node1=Child("node"),
                                               software=Child("software")))
        self.model.create_root_item("root", "/")

    def _setup_correct_model(self):
        self.node1 = self.model.create_item("node",
                               "/node1",
                               hostname="node1")

        self.model.create_item("network-interface",
                               "/ms/network_interfaces/if0",
                               ipaddress="192.168.135.129",
                               network_name="ms_external")

        self.model.create_item("network-interface",
                               "/node1/network_interfaces/if0",
                               ipaddress="10.46.71.10",
                               network_name="nodes")

        ntp = self.model.create_item("ntp-service",
                                     "/software/items/ntp1")
        self.model.create_item("ntp-server",
                               "/software/items/ntp1/servers/s0",
                               server="100.100.100.100")

        self.model.create_inherited(ntp.get_vpath(),
                                    "/node1/items/ntp1")

        self.model.create_inherited(ntp.get_vpath(),
                                    "/ms/items/ntp1")

        self.model.create_item("network",
                               "/infrastructure/networking"
                               "/networks/traffic1",
                               subnet="172.16.100.0/24",
                               name="traffic1",
                               litp_management='false')

        self.model.create_item("network",
                               "/infrastructure/networking"
                               "/networks/dhcp_network",
                               subnet="10.10.14.0/24",
                               name="dhcp_network",
                               litp_management='false')

    def _create_two_ntp_services_per_node(self):
        """
        This method is used to create multiple
        ntp services
        """
        self._setup_correct_model()

        ntp_service2 = self.model.create_item("ntp-service",
                                              "/software/items/ntp2")

        self.model.create_item("ntp-server",
                               "software/items/ntp2/servers/s0",
                               server="2.2.2.2")

        self.model.create_inherited(ntp_service2.get_vpath(),
                                    "/ms/items/ntp2")

        self.model.create_inherited(ntp_service2.get_vpath(),
                                    "/node1/items/ntp2")

    def _setup_model_for_different_ntp_services(self):
        self.node1 = self.model.create_item("node",
                               "/node1",
                               hostname="node1")

        self.model.create_item("network-interface",
                               "/ms/network_interfaces/if0",
                               ipaddress="192.168.135.129",
                               network_name="ms_external")

        self.model.create_item("network-interface",
                               "/node1/network_interfaces/if0",
                               ipaddress="10.46.71.10",
                               network_name="nodes")

        ntp1 = self.model.create_item("ntp-service",
                                     "/software/items/ntp1")

        self.model.create_item("ntp-server",
                               "/software/items/ntp1/servers/s0",
                               server="100.100.100.100")

        self.model.create_item("ntp-server",
                               "/software/items/ntp1/servers/s1",
                               server="100.100.100.101")

        self.model.create_inherited(ntp1.get_vpath(),
                                    "/ms/items/ntp1")

        ntp2 = self.model.create_item("ntp-service",
                                     "/software/items/ntp2")

        self.model.create_item("ntp-server",
                               "/software/items/ntp2/servers/s0",
                               server="101.100.100.100")

        self.model.create_item("ntp-server",
                               "/software/items/ntp2/servers/s1",
                               server="101.100.100.101")

        self.model.create_item("ntp-server",
                               "/software/items/ntp2/servers/s2",
                               server="101.100.100.102")

        self.model.create_inherited(ntp2.get_vpath(),
                                    "/node1/items/ntp1")

        self.model.create_item("network",
                               "/infrastructure/networking"
                               "/networks/traffic1",
                               subnet="172.16.100.0/24",
                               name="traffic1",
                               litp_management='false')

        self.model.create_item("network",
                               "/infrastructure/networking"
                               "/networks/dhcp_network",
                               subnet="10.10.14.0/24",
                               name="dhcp_network",
                               litp_management='false')

    def query(self, item_type=None, **kwargs):
        return self.context.query(item_type, **kwargs)

    def test_validate_correct_model(self):
        """
        This test tests the correct model, in this case no errors are raised
        """
        self._setup_correct_model()
        errors = self.plugin.validate_model(self)
        self.assertEquals(0, len(errors))

    def test_only_one_ntp_service_pre_node(self):
        """
        Test that inheriting multi ntp services on one node results
        in errors being raised
        """
        self._create_two_ntp_services_per_node()
        errors = self.plugin.validate_model(self)
        self.assertEquals(2, len(errors))
        expected_errors = [
            ValidationError(
                error_message="Cannot have multiple ntp-service on " \
                + "the same node/ms. See the following paths " \
                + "/ms/items/ntp1, /ms/items/ntp2. "
            ),
            ValidationError(
                error_message="Cannot have multiple ntp-service on " \
                + "the same node/ms. See the following paths "
                + "/node1/items/ntp1, /node1/items/ntp2. "
            )
        ]
        self.assertEquals(errors[0], expected_errors[0])
        self.assertEquals(errors[1], expected_errors[1])

    def test_validate_model_with_multi_services(self):
        """
        Test that multi ntp services can be created in the model
        """
        self._setup_model_for_different_ntp_services()
        errors = self.plugin.validate_model(self)
        self.assertEquals(0, len(errors))

    def test_create_configuration(self):
        """
        Test the correct configuration, in this case we expect
        to have 2 tasks
        """
        self._setup_correct_model()
        tasks = self.plugin.create_configuration(self)
        self.assertEquals(2, len(tasks))

    def test_config_servers_on_ms_and_peer_nodes(self):
        """
        Test that both ms and peer nodes can be configured with one or more servers
        """
        self._setup_model_for_different_ntp_services()
        tasks = self.plugin.create_configuration(self)
        self.assertEquals(2, len(tasks[0].kwargs['servers']))
        self.assertEquals(3, len(tasks[1].kwargs['servers']))
        servers_ms = ["100.100.100.100", "100.100.100.101"]
        self.assertTrue(all(x in tasks[0].kwargs['servers'] for x in servers_ms))
        servers_n1 = ["101.100.100.100", "101.100.100.101", "101.100.100.102"]
        self.assertTrue(all(x in tasks[1].kwargs['servers'] for x in servers_n1))

    def test_default_value(self):
        self.node1 = self.model.create_item("node",
                                            "/node1",
                                            hostname="node1")

        self.model.create_item("network-interface",
                               "/ms/network_interfaces/if0",
                               ipaddress="192.168.135.129",
                               network_name="ms_external")

        ntp = self.model.create_item("ntp-service",
                                     "/software/items/ntp1")

        self.model.create_inherited(ntp.get_vpath(),
                                    "/node1/items/ntp1")
        self.model.create_inherited(ntp.get_vpath(),
                                    "/ms/items/ntp2")

        tasks = self.plugin.create_configuration(self)
        self.assertEquals(2, len(tasks))
        self.assertEquals(['127.127.1.0'], tasks[0].kwargs['servers'])
        self.assertEquals(['192.168.135.129'], tasks[1].kwargs['servers'])

    def test_correct_networks_and_netmasks(self):
        """
        Test the correct networks, in this case we expect
        to have two: traffic1 and dhcp_network
        """
        self._setup_correct_model()

        tasks = self.plugin.create_configuration(self)

        for task in tasks:
            if task.kwargs['clients']:
                expected_networks = ['10.10.14.0 mask 255.255.255.0',
                                     '172.16.100.0 mask 255.255.255.0']
                self.assertEquals(expected_networks, task.kwargs['clients'])

    def test_only_one_network_and_netmask(self):
        """
        Test the correct networks, in this case we expect
        to have one network; the dhcp_network
        """
        self._setup_correct_model()

        self.model.remove_item("/infrastructure/networking"
                               "/networks/traffic1")

        tasks = self.plugin.create_configuration(self)

        for task in tasks:
            if task.kwargs['clients']:
                expected_networks = ['10.10.14.0 mask 255.255.255.0']
                self.assertEquals(expected_networks, task.kwargs['clients'])

    def test_remove_ntp_service(self):
        """
        Test remove ntp-service functionality
        """
        self._setup_model_for_different_ntp_services()
        self.model.set_all_applied()
        self.model.remove_item("/node1/items/ntp1")
        tasks = self.plugin.create_configuration(self)
        self.assertEquals(len(tasks), 1)
        self.assertEquals(['192.168.135.129'], tasks[0].kwargs['servers'])

    def test_remove_and_add_one_ntp_service(self):
        """
        Test remove the existing ntp-service and add another one ntp-service
        """

        self._setup_model_for_different_ntp_services()
        self.model.set_all_applied()
        self.model.remove_item("/node1/items/ntp1")
        self.model.create_inherited("/software/items/ntp1",
                                    "/node1/items/ntp2")
        errors = self.plugin.validate_model(self)
        self.assertEquals(0, len(errors))
        tasks = self.plugin.create_configuration(self)
        self.assertEquals(len(tasks), 1)
        servers_n1 = ["100.100.100.100", "100.100.100.101"]
        self.assertTrue(all(x in tasks[0].kwargs['servers'] for x in servers_n1))

    def test_remove_and_add_multi_ntp_service(self):
        """
        Test remove the existing ntp-service and add another multiple ntp-services
        """
        self._setup_model_for_different_ntp_services()
        self.model.set_all_applied()
        self.model.remove_item("/node1/items/ntp1")
        self.model.create_inherited("/software/items/ntp1",
                                    "/node1/items/ntp2")
        self.model.create_inherited("/software/items/ntp2",
                                    "/node1/items/ntp3")
        errors = self.plugin.validate_model(self)
        self.assertEquals(1, len(errors))

    def test_remove_and_add_one_ntp_service_failed_midway(self):
        """
        Test remove the existing ntp-service and add another one ntp-service,
        but the plan fails in the midway, in which case ntp2 becomes "Applied",
        ntp1 would still be in "ForRemoval"
        """
        self._setup_model_for_different_ntp_services()
        self.model.set_all_applied()
        self.model.remove_item("/node1/items/ntp1")
        ntp2 = self.model.create_inherited("/software/items/ntp1",
                                    "/node1/items/ntp2")
        ntp2.set_applied()
        errors = self.plugin.validate_model(self)
        self.assertEquals(0, len(errors))
        tasks = self.plugin.create_configuration(self)
        self.assertEquals(len(tasks), 1)
        servers_n1 = ["100.100.100.100", "100.100.100.101"]
        self.assertTrue(all(x in tasks[0].kwargs['servers'] for x in servers_n1))
