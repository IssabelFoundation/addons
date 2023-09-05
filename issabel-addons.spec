%define modname addons

Summary: Issabel Addons
Name: issabel-addons
Version: 5.0.0
Release: 1
License: GPL
Group:   Applications/System
Source0: issabel-%{modname}-%{version}.tar.gz
#Patch0:  repo-40.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildArch: noarch
Requires(pre): issabel-framework >= 5.0.0-1
Requires(pre): chkconfig, php-soap
Requires: yum
# commands: /usr/bin/uname
Requires: coreutils

# commands: rpm
Requires: rpm

Obsoletes: elastix-addons

%description
Issabel Addons

%prep
%setup -n %{name}-%{version}
#%patch0 -p0

%install
rm -rf $RPM_BUILD_ROOT

# Files provided by all Issabel modules
mkdir -p    $RPM_BUILD_ROOT/var/www/html/
mv modules/ $RPM_BUILD_ROOT/var/www/html/

# Additional (module-specific) files that can be handled by RPM
mkdir -p $RPM_BUILD_ROOT/opt/issabel/
mv setup/issabel-moduleconf $RPM_BUILD_ROOT/opt/issabel/issabel-updater
mkdir -p $RPM_BUILD_ROOT/etc/init.d/
mv $RPM_BUILD_ROOT/opt/issabel/issabel-updater/issabel-updaterd $RPM_BUILD_ROOT/etc/init.d/
chmod +x $RPM_BUILD_ROOT/etc/init.d/issabel-updaterd
mkdir -p $RPM_BUILD_ROOT/etc/yum.repos.d/

## Add the GNU Privacy Guard for the Postgresql91 repo
mkdir -p $RPM_BUILD_ROOT/etc/pki/
mv setup/etc/pki/rpm-gpg/ $RPM_BUILD_ROOT/etc/pki/
rmdir setup/etc/pki

# The following folder should contain all the data that is required by the installer,
# that cannot be handled by RPM.
mkdir -p    $RPM_BUILD_ROOT/usr/share/issabel/module_installer/%{name}-%{version}-%{release}/
mv setup/etc/yum.repos.d/ $RPM_BUILD_ROOT/etc/

rmdir setup/etc
mv setup/   $RPM_BUILD_ROOT/usr/share/issabel/module_installer/%{name}-%{version}-%{release}/
mv menu.xml $RPM_BUILD_ROOT/usr/share/issabel/module_installer/%{name}-%{version}-%{release}/

%pre
mkdir -p /usr/share/issabel/module_installer/%{name}-%{version}-%{release}/
touch /usr/share/issabel/module_installer/%{name}-%{version}-%{release}/preversion_%{modname}.info
if [ $1 -eq 2 ]; then
    rpm -q --queryformat='%{VERSION}-%{RELEASE}' %{name} > /usr/share/issabel/module_installer/%{name}-%{version}-%{release}/preversion_%{modname}.info
fi

%post
pathModule="/usr/share/issabel/module_installer/%{name}-%{version}-%{release}"

# Run installer script to fix up ACLs and add module to Issabel menus.
issabel-menumerge /usr/share/issabel/module_installer/%{name}-%{version}-%{release}/menu.xml
pathSQLiteDB="/var/www/db"
mkdir -p $pathSQLiteDB
preversion=`cat $pathModule/preversion_%{modname}.info`
rm -f $pathModule/preversion_%{modname}.info

if [ $1 -eq 1 ]; then #install
  # The installer database
    issabel-dbprocess "install" "$pathModule/setup/db"
elif [ $1 -eq 2 ]; then #update
    # Removing addons_installed modules
    issabel-menuremove "addons_installed"
    issabel-menuremove "addons_avalaibles"
    # Removing addons_installed files
    rm -rf /var/www/html/modules/addons_installed
    issabel-dbprocess "update"  "$pathModule/setup/db" "$preversion"
    # restart daemon
    /usr/bin/systemctl daemon-reload
    /sbin/service issabel-updaterd restart
fi

ARCH=`uname -m`
CENTOSVER=`php -r 'if (preg_match("/.+?release (\d)/i", file_get_contents("/etc/redhat-release"), $regs)) print $regs[1];'`
if [ "$ARCH" != "i386" ] && [ "$ARCH" != "i686" ] && [ "$ARCH" != "x86_64" ] ; then
        echo "Incompatible architecture $ARCH , removing PostgreSQL repository..."
        rm -rf /etc/yum.repos.d/pgdg-91-centos.repo
        rm -rf /etc/pki/rpm-gpg/RPM-GPG-KEY-PGDG-91
elif [ "0$CENTOSVER" -ge 7 ] ; then
        echo "CentOS base install too new, removing PostgreSQL repository..."
        rm -rf /etc/yum.repos.d/pgdg-91-centos.repo
        rm -rf /etc/pki/rpm-gpg/RPM-GPG-KEY-PGDG-91
else
        # import the GPG-key
        echo "Importing RPM key for PostgreSQL repository..."
        /bin/rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-PGDG-91
fi

# The installer script expects to be in /tmp/new_module
mkdir -p /tmp/new_module/%{modname}
cp -r /usr/share/issabel/module_installer/%{name}-%{version}-%{release}/* /tmp/new_module/%{modname}/
chown -R asterisk.asterisk /tmp/new_module/%{modname}

php /tmp/new_module/%{modname}/setup/installer.php
rm -rf /tmp/new_module

# Install issabel-updaterd as a service
chkconfig --add issabel-updaterd
chkconfig --level 2345 issabel-updaterd on

%clean
rm -rf $RPM_BUILD_ROOT

%preun
pathModule="/usr/share/issabel/module_installer/%{name}-%{version}-%{release}"
if [ $1 -eq 0 ] ; then # Validation for desinstall this rpm
  echo "Delete Addons menus"
  issabel-menuremove "%{modname}"

  echo "Dump and delete %{name} databases"
  issabel-dbprocess "delete" "$pathModule/setup/db"
fi

%files
%defattr(-, root, root)
%{_localstatedir}/www/html/*
/usr/share/issabel/module_installer/*
/etc/init.d/issabel-updaterd
/opt/issabel/issabel-updater
/etc/pki/rpm-gpg/*
/etc/yum.repos.d/*

%changelog
