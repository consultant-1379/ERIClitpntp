<% if @date -%>
# HEADER: This file was autogenerated at <%= @date %>
# HEADER: by LITP.  While it can still be managed manually, it
<% else -%>
# HEADER: This file was autogenerated by LITP.
# HEADER: While it can still be managed manually, it
<% end -%>
# HEADER: is definitely not recommended.
# Permit time synchronization with our time source, but do not
# permit the source to query or modify the service on this system.
restrict default kod nomodify notrap nopeer noquery
restrict -6 default kod nomodify notrap nopeer noquery

# Permit all access over the loopback interface.  This could
# be tightened as well, but to do so would effect some of
# the administrative functions.
restrict 127.0.0.1
restrict -6 ::1

# Hosts on local network are less restricted.
<% [@clients].flatten.each do |client| -%>
restrict <%= client %> nomodify notrap
<% end -%>

<% [@servers].flatten.each do |server| -%>
server <%= server %>
<% end -%>

# Undisciplined Local Clock. This is a fake driver intended for backup
# and when no outside source of synchronized time is available.
# server 127.127.1.0 # local clock
# fudge	 127.127.1.0 stratum 10

# Drift file.  Put this in a directory which the daemon can write to.
# No symbolic links allowed, either, since the daemon updates the file
# by creating a temporary in the same directory and then rename()'ing
# it to the file.
driftfile /var/lib/ntp/drift

# Key file containing the keys and key identifiers used when operating
# with symmetric key cryptography.
keys /etc/ntp/keys

# Specify the key identifiers which are trusted.
#trustedkey 4 8 42

# Specify the key identifier to use with the ntpdc utility.
#requestkey 8

# Specify the key identifier to use with the ntpq utility.
#controlkey 8

# Disable the monitoring facility to prevent amplification attacks using ntpdc
# monlist command
disable monitor
