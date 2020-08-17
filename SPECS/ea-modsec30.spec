Name: ea-modsec3
Summary: libModSecurity v3.0
Version: 3.0.4
# Doing release_prefix this way for Release allows for OBS-proof versioning, See EA-4544 for more details
%define release_prefix 1
Release: %{release_prefix}%{?dist}.cpanel
Vendor: cPanel, Inc.
Group: System Environment/Libraries
License: Apache v2
URL: https://github.com/SpiderLabs/ModSecurity

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
AutoReq:   no
BuildRequires: gcc-c++ flex bison yajl yajl-devel curl-devel curl GeoIP-devel doxygen zlib-devel pcre-devel

%description

Libmodsecurity is one component of the ModSecurity v3 project. The library
 codebase serves as an interface to ModSecurity Connectors taking in
 web traffic and applying traditional ModSecurity processing. In general,
 it provides the capability to load/interpret rules written in the ModSecurity
 SecRules format and apply them to HTTP content provided by your application
 via Connectors.

%prep
git clone https://github.com/SpiderLabs/ModSecurity
cd ModSecurity
git checkout -b v3/master origin/v3/master
git fetch  --tags
git checkout tags/v%{version} -b v%{version}-branch
./build.sh
git submodule init
git submodule update

%build
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/cpanel/ea-modsec3
./configure --prefix=$RPM_BUILD_ROOT/opt/cpanel/ea-modsec3
make

%install
make install DESTDIR=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, root, root, -)
/opt/cpanel/ea-modsec3

%changelog
* Mon Aug 17 2020 Daniel Muey <dan@cpanel.net> - 3.0.4-1
- ZC-7365: initial release

