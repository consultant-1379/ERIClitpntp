define ntpd::config ($clients, $servers, $date = false) {

  if $puppet_master == 'true' {
    package { 'ntp':
    ensure => 'present',
    }
    file { 'ntp.conf':
      path    => '/etc/ntp.conf',
      ensure  => file,
      require => Package['ntp'],
      content => template('ntpd/ntp.conf.el'),
    }
    service { 'ntp':
      name      => 'ntpd',
      enable => true,
      ensure => 'running',
      require   => Package['ntp'],
      subscribe => File['ntp.conf'],
    }
  }
  else
  {
    package { 'ntp':
    ensure => 'present',
    }
    file { 'ntp.conf':
      path    => '/etc/ntp.conf',
      ensure  => file,
      require => Package['ntp'],
      content => template('ntpd/ntp_node.conf.el'),
    }
    service { 'ntp':
      name      => 'ntpd',
      enable => true,
      ensure => 'running',
      require   => Package['ntp'],
      subscribe => File['ntp.conf'],
    }
  }
}