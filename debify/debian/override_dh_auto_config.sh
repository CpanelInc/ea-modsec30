#!/bin/bash

source debian/vars.sh

set -x

tar xzf $SOURCE1

patch -p1 -b .patch-cve-2020-15598 < debian/patches/0001-Patch-ModSecurity-3.0.4-for-CVE-2020-15598.patch

# hack in https://github.com/SpiderLabs/ModSecurity/pull/2378/commits/9d78228bf066bb24f89e36ea130c48d0ca7f719b
# to support SecGeoLookupDb having a value of /usr/local/cpanel/3rdparty/share/geoipfree/IpToCountry.dat
perl -pi -e 's/GEOIP_INDEX_CACHE/GEOIP_MEMORY_CACHE/' src/utils/geo_lookup.cc

/bin/bash -x build.sh

./configure --prefix=/opt/cpanel/ea-modsec30
make

