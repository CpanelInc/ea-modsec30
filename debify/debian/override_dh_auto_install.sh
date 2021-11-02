#!/bin/bash

source debian/vars.sh

set -x

mkdir -p $DEB_INSTALL_ROOT/opt/cpanel/ea-modsec30
make DESTDIR=$DEB_INSTALL_ROOT install
ln -s /opt/cpanel/ea-modsec30/lib $DEB_INSTALL_ROOT/opt/cpanel/ea-modsec30/lib64
mkdir -p $DEB_INSTALL_ROOT/etc/cpanel/ea4
echo -n $version > $DEB_INSTALL_ROOT/etc/cpanel/ea4/modsecurity.version

mkdir -p $DEB_INSTALL_ROOT/var/cpanel/templates/apache2_4
/bin/cp -rf ${SOURCE5} $DEB_INSTALL_ROOT/var/cpanel/templates/apache2_4/modsec.cpanel.conf.tt

echo "SHOWVAR"
find $DEB_INSTALL_ROOT/var/cpanel -type f -print

ls -ld /usr/src/packages/BUILD/debian
cat -n /usr/src/packages/BUILD/debian/ea-modsec30.install

echo "ENDSHOW"

