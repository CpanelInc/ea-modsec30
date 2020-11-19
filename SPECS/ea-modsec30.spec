%define debug_package %{nil}

Name: ea-modsec30
Summary: libModSecurity v3.0
Version: 3.0.4
# Doing release_prefix this way for Release allows for OBS-proof versioning, See EA-4544 for more details
%define release_prefix 6
Release: %{release_prefix}%{?dist}.cpanel
Vendor: cPanel, Inc.
Group: System Environment/Libraries
License: Apache v2
URL: https://github.com/SpiderLabs/ModSecurity

Source0: https://github.com/SpiderLabs/ModSecurity/archive/v%{version}.tar.gz
Source1: submodules.tar.gz

Patch0: 0001-Patch-ModSecurity-3.0.4-for-CVE-2020-15598.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
AutoReq:   no

%if 0%{?rhel} > 7
# these have ea- couterparts but there is no way to specify them in configure
BuildRequires: libnghttp2 brotli
Requires: GeoIP
%endif

# from https://github.com/SpiderLabs/ModSecurity/wiki/Compilation-recipes-for-v3.x#centos-7-minimal
# --with-curl does not stick in make like --with-libxml does so we can’t do ea-libcurl[-devel]
BuildRequires: gcc-c++ flex bison yajl yajl-devel curl-devel curl GeoIP-devel doxygen zlib-devel pcre-devel lua lua-devel
Requires: yajl lua

# the one ea- one that we can specify
BuildRequires: ea-libxml2 ea-libxml2-devel

Provides: mod_security
Conflicts: mod_security

# WHM only factors in real package names so:
Conflicts: ea-apache24-mod_security2 ea-modsec31

%description

Libmodsecurity is one component of the ModSecurity v3 project. The library
 codebase serves as an interface to ModSecurity Connectors taking in
 web traffic and applying traditional ModSecurity processing. In general,
 it provides the capability to load/interpret rules written in the ModSecurity
 SecRules format and apply them to HTTP content provided by your application
 via Connectors.

%prep
%setup -q -n ModSecurity-%{version}
tar xzf %{SOURCE1}

%patch0 -p1 -b .patch-cve-2020-15598

# hack in https://github.com/SpiderLabs/ModSecurity/pull/2378/commits/9d78228bf066bb24f89e36ea130c48d0ca7f719b
# to support SecGeoLookupDb having a value of /usr/local/cpanel/3rdparty/share/geoipfree/IpToCountry.dat
perl -pi -e 's/GEOIP_INDEX_CACHE/GEOIP_MEMORY_CACHE/' src/utils/geo_lookup.cc

%build
./build.sh
./configure --prefix=/opt/cpanel/ea-modsec30 --with-libxml=/opt/cpanel/ea-libxml2

make

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/cpanel/ea-modsec30
make DESTDIR=$RPM_BUILD_ROOT install

ln -s /opt/cpanel/ea-modsec30/lib $RPM_BUILD_ROOT/opt/cpanel/ea-modsec30/lib64
mkdir -p $RPM_BUILD_ROOT/etc/cpanel/ea4
echo -n %{version} > $RPM_BUILD_ROOT/etc/cpanel/ea4/modsecurity.version

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, root, root, -)
/opt/cpanel/ea-modsec30
/etc/cpanel/ea4/modsecurity.version

%changelog
* Thu Nov 19 2020 Daniel Muey <dan@cpanel.net> - 3.0.4-6
- ZC-7925: Install /etc/cpanel/ea4/modsecurity.version

* Wed Sep 30 2020 Daniel Muey <dan@cpanel.net> - 3.0.4-5
- ZC-7669: Ensure lib64 works

* Tue Sep 15 2020 Tim Mullin <tim@cpanel.net> - 3.0.4-4
- EA-9302: Patch modsec30 for CVE-2020-15598

* Thu Sep 10 2020 Daniel Muey <dan@cpanel.net> - 3.0.4-3
- ZC-7506: Support `/usr/local/cpanel/3rdparty/share/geoipfree/IpToCountry.dat` as a value for `SecGeoLookupDb`
- ZC-7507: Add lua support

* Tue Sep 01 2020 Daniel Muey <dan@cpanel.net> - 3.0.4-2
- ZC-7376: Add explicit package name conflicts for non-yum resolution

* Mon Aug 17 2020 Daniel Muey <dan@cpanel.net> - 3.0.4-1
- ZC-7365: initial release

