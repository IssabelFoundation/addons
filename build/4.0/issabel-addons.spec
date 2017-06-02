%define modname addons

Summary: Issabel Addons
Name:    issabel-%{modname}
Version: 4.0.0
Release: 1
License: GPL
Group:   Applications/System
Source0: %{modname}_%{version}-%{release}.tgz
Patch0:  repo-40.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildArch: noarch
Requires(pre): issabel-framework >= 2.5.0-2
Requires(pre): chkconfig, php-soap
Requires: yum
# commands: /usr/bin/uname
Requires: coreutils

# commands: rpm
Requires: rpm

Obsoletes: elastix-addons
Provides: elastix-addons

%description
Issabel Addons

%prep
%setup -n %{name}_%{version}-%{release}
%patch0 -p0

%install
rm -rf $RPM_BUILD_ROOT

# Files provided by all Elastix modules
mkdir -p    $RPM_BUILD_ROOT/var/www/html/
mv modules/ $RPM_BUILD_ROOT/var/www/html/

# Additional (module-specific) files that can be handled by RPM
mkdir -p $RPM_BUILD_ROOT/opt/elastix/
mv setup/elastix-moduleconf $RPM_BUILD_ROOT/opt/elastix/elastix-updater
mkdir -p $RPM_BUILD_ROOT/etc/init.d/
mv $RPM_BUILD_ROOT/opt/elastix/elastix-updater/elastix-updaterd $RPM_BUILD_ROOT/etc/init.d/
chmod +x $RPM_BUILD_ROOT/etc/init.d/elastix-updaterd
mkdir -p $RPM_BUILD_ROOT/etc/yum.repos.d/

## Add the GNU Privacy Guard for the Postgresql91 repo
mkdir -p $RPM_BUILD_ROOT/etc/pki/
mv setup/etc/pki/rpm-gpg/ $RPM_BUILD_ROOT/etc/pki/
rmdir setup/etc/pki

# The following folder should contain all the data that is required by the installer,
# that cannot be handled by RPM.
mkdir -p    $RPM_BUILD_ROOT/usr/share/elastix/module_installer/%{name}-%{version}-%{release}/
mv setup/etc/yum.repos.d/ $RPM_BUILD_ROOT/etc/

rmdir setup/etc
mv setup/   $RPM_BUILD_ROOT/usr/share/elastix/module_installer/%{name}-%{version}-%{release}/
mv menu.xml $RPM_BUILD_ROOT/usr/share/elastix/module_installer/%{name}-%{version}-%{release}/

%pre
mkdir -p /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/
touch /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/preversion_%{modname}.info
if [ $1 -eq 2 ]; then
    rpm -q --queryformat='%{VERSION}-%{RELEASE}' %{name} > /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/preversion_%{modname}.info
fi

%post
pathModule="/usr/share/elastix/module_installer/%{name}-%{version}-%{release}"

# Run installer script to fix up ACLs and add module to Elastix menus.
elastix-menumerge /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/menu.xml
pathSQLiteDB="/var/www/db"
mkdir -p $pathSQLiteDB
preversion=`cat $pathModule/preversion_%{modname}.info`
rm -f $pathModule/preversion_%{modname}.info

if [ $1 -eq 1 ]; then #install
  # The installer database
    elastix-dbprocess "install" "$pathModule/setup/db"
elif [ $1 -eq 2 ]; then #update
    # Removing addons_installed modules
    elastix-menuremove "addons_installed"
    elastix-menuremove "addons_avalaibles"
    # Removing addons_installed files
    rm -rf /var/www/html/modules/addons_installed
    elastix-dbprocess "update"  "$pathModule/setup/db" "$preversion"
    # restart daemon
    /sbin/service elastix-updaterd restart
fi

ARCH=`uname -m`
CENTOSVER=`php -r 'if (preg_match("/CentOS.+?release (\d)/i", file_get_contents("/etc/redhat-release"), $regs)) print $regs[1];'`
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
cp -r /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/* /tmp/new_module/%{modname}/
chown -R asterisk.asterisk /tmp/new_module/%{modname}

php /tmp/new_module/%{modname}/setup/installer.php
rm -rf /tmp/new_module

# Install elastix-updaterd as a service
chkconfig --add elastix-updaterd
chkconfig --level 2345 elastix-updaterd on

%clean
rm -rf $RPM_BUILD_ROOT

%preun
pathModule="/usr/share/elastix/module_installer/%{name}-%{version}-%{release}"
if [ $1 -eq 0 ] ; then # Validation for desinstall this rpm
  echo "Delete Addons menus"
  elastix-menuremove "%{modname}"

  echo "Dump and delete %{name} databases"
  elastix-dbprocess "delete" "$pathModule/setup/db"
fi

%files
%defattr(-, root, root)
%{_localstatedir}/www/html/*
/usr/share/elastix/module_installer/*
/etc/init.d/elastix-updaterd
/opt/elastix/elastix-updater
/etc/pki/rpm-gpg/*
/etc/yum.repos.d/*

%changelog
