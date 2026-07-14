%define debug_package %{nil}
%undefine __brp_remove_rpath

Name: ea-modsec30
Summary: libModSecurity v3.0
Version: 3.0.16
# Doing release_prefix this way for Release allows for OBS-proof versioning, See EA-4544 for more details
%define release_prefix 4
Release: %{release_prefix}%{?dist}.cpanel
Vendor: cPanel, Inc.
Group: System Environment/Libraries
License: Apache v2
URL: https://github.com/SpiderLabs/ModSecurity

Source0: https://github.com/SpiderLabs/ModSecurity/archive/v%{version}.tar.gz
Source1: submodules.tar.gz
Source5: modsec30.cpanel.conf.tt

# EA-13497: on cPanel's multi-tenant Apache setup (mod_ruid2), the per-day/
# per-time-bucket SecAuditLogStorageDir subdirectories are created at runtime
# by whichever account's request happens to be first, under that process's
# default umask (0022). That silently strips any group/other write bits from
# the requested directory mode before mkdir() ever sees it, so any later
# request running as a different account's UID gets a silent, default-
# verbosity-invisible "Permission denied" trying to create its own time-
# bucket subdirectory - losing that transaction's audit log entry with no
# admin-visible error. A first attempt at this fix wrapped the mkdir calls
# in umask(0)/restore; that is correct in isolation (proven live via
# strace) but was superseded here by an explicit chmod() after each
# createDir() call, which is idempotent, thread-safe regardless of MPM
# model, and self-healing on every logged transaction - it forces the
# final directory mode to the configured SecAuditLogDirMode/
# getDirectoryPermission() value every time, independent of whatever
# umask created the directory.
Patch0: 0001-Force-chmod-01733-for-audit-log-directory-creation.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
AutoReq:   no

%if 0%{?rhel} > 7
# these have ea- couterparts but there is no way to specify them in configure
BuildRequires: libnghttp2 brotli
%if 0%{?rhel} == 8
Requires: GeoIP
%endif
%endif

%if %{?rhel} == 7
BuildRequires: kernel-devel devtoolset-9
%else
BuildRequires: gcc-c++
%endif

# from https://github.com/SpiderLabs/ModSecurity/wiki/Compilation-recipes-for-v3.x#centos-7-minimal
# --with-curl does not stick in make like --with-libxml does so we can’t do ea-libcurl[-devel]
%if %{?rhel} == 9
BuildRequires: flex bison yajl yajl-devel curl-devel curl doxygen zlib-devel pcre2-devel lua lua-devel
%else
BuildRequires: flex bison yajl yajl-devel curl-devel curl GeoIP-devel doxygen zlib-devel pcre2-devel lua lua-devel
%endif
Requires: yajl lua pcre2

# the one ea- one that we can specify
BuildRequires: ea-libxml2 ea-libxml2-devel
Requires: ea-libxml2

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
%patch0 -p1

# hack in https://github.com/SpiderLabs/ModSecurity/pull/2378/commits/9d78228bf066bb24f89e36ea130c48d0ca7f719b
# to support SecGeoLookupDb having a value of /usr/local/cpanel/3rdparty/share/geoipfree/IpToCountry.dat
perl -pi -e 's/GEOIP_INDEX_CACHE/GEOIP_MEMORY_CACHE/' src/utils/geo_lookup.cc

%build
%if %{?rhel} == 7
source /opt/rh/devtoolset-9/enable
%endif

export LDFLAGS="$LDFLAGS \
    -Wl,--enable-new-dtags \
    -Wl,-rpath,/opt/cpanel/ea-libxml2/lib \
    -Wl,-rpath,/opt/cpanel/ea-libxml2/lib64"

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

mkdir -p $RPM_BUILD_ROOT/var/cpanel/templates/apache2_4
/bin/cp -rf %{SOURCE5} $RPM_BUILD_ROOT/var/cpanel/templates/apache2_4/modsec.cpanel.conf.tt

%clean
rm -rf $RPM_BUILD_ROOT

%posttrans
# EA-13497: a plain package update alone does not activate a fix shipped
# inside this package's libmodsecurity.so on an already-running httpd. The
# only restart trigger in the ea-modsec30 family is the connector's own
# post-transaction scriptlet, which calls Cpanel::HttpUtils::ApRestart's
# BgSafe path - a graceful (kill -USR1) reload. A graceful reload re-reads
# config and rule files, but it cannot make an already-running httpd
# master process re-dlopen a shared library it has held mapped since
# Apache last started. Proven end to end (master PID before/after a real
# restart, plus strace evidence) in the EA-13492 smold4r investigation -
# see work/handoffs/EA-13492-modsec-rules-investigation.md.
#
# Force a genuine full stop-then-start (not a graceful reload) so a new
# libmodsecurity.so actually gets loaded by a fresh httpd master process.
# Guarded to be a safe no-op outside a real cPanel install with Apache
# already running: restartsrv_httpd is absent in the OBS build/install
# chroot, and this must never be used to start httpd on a box where it
# was not already running (e.g. an nginx-only or httpd-disabled box).
if [ -x /usr/local/cpanel/scripts/restartsrv_httpd ] && pgrep -x httpd >/dev/null 2>&1; then
    /usr/local/cpanel/scripts/restartsrv_httpd --stop  >/dev/null 2>&1
    /usr/local/cpanel/scripts/restartsrv_httpd --start >/dev/null 2>&1
fi

exit 0

%files
%defattr(-, root, root, -)
/opt/cpanel/ea-modsec30
/var/cpanel/templates/apache2_4/modsec.cpanel.conf.tt
/etc/cpanel/ea4/modsecurity.version

%changelog
* Tue Jul 14 2026 Cory McIntire <cory.mcintire@webpros.com> - 3.0.16-4
- EA-13497: Add a posttrans scriptlet that forces a full httpd stop-then-start on install/upgrade, guarded to be a no-op outside a real cPanel install with Apache already running - the connector's existing restart trigger is a graceful reload that cannot re-dlopen an updated libmodsecurity.so on an already-running httpd master process, so a package update alone previously left CVE/bug fixes compiled into this library silently inactive until something else eventually forced a real Apache restart

* Mon Jul 13 2026 Cory McIntire <cory.mcintire@webpros.com> - 3.0.16-3
- EA-13497: Replace the umask(0)/restore around SecAuditLogStorageDir's per-day/time-bucket mkdir() calls with an explicit chmod() to the configured directory mode after each call - idempotent, thread-safe under any MPM, and self-healing on every logged transaction, so a different account UID can always write into these directories regardless of the process's default umask

* Mon Jul 13 2026 Cory McIntire <cory.mcintire@webpros.com> - 3.0.16-2
- EA-13497: Force umask 0 around SecAuditLogStorageDir's per-day/time-bucket mkdir() calls so a configured directory mode is not silently stripped by the process's default umask, which previously left those directories unwritable by any account UID other than whichever request created them first

* Thu Jul 09 2026 EA4 Update Bot <cory.mcintire@webpros.com> - 3.0.16-1
- EA-13492: Update ea-modsec30 from v3.0.15 to v3.0.16

* Tue May 19 2026 Cory McIntire <cory.mcintire@webpros.com> - 3.0.15-2
- EA-13435: Switch pcre-devel to pcre2-devel; ModSecurity 3.0.15 requires PCRE2

* Wed May 13 2026 EA4 Update Bot <cory.mcintire@webpros.com> - 3.0.15-1
- EA-13435: Update ea-modsec30 from v3.0.14 to v3.0.15

* Thu Oct 23 2025 Chris Castillo <chris.castillo@webpros.com> - 3.0.14-1
- EA-12738: Update ea-modsec30 to v3.0.14

* Wed Feb 28 2024 Cory McIntire <cory@cpanel.net> - 3.0.12-1
- EA-11990: Update ea-modsec30 from v3.0.9 to v3.0.12

* Thu Apr 13 2023 Cory McIntire <cory@cpanel.net> - 3.0.9-1
- EA-11353: Update ea-modsec30 from v3.0.8 to v3.0.9

* Wed Oct 19 2022 Julian Brown <julian.brown@cpanel.net> - 3.0.8-3
- ZC-10394: Corrections for builds

* Thu Sep 29 2022 Julian Brown <julian.brown@cpanel.net> - 3.0.8-2
- ZC-10336: Add changes so that it builds on AlmaLinux 9

* Thu Sep 08 2022 Cory McIntire <cory@cpanel.net> - 3.0.8-1
- EA-10927: Update ea-modsec30 from v3.0.7 to v3.0.8

* Tue May 31 2022 Cory McIntire <cory@cpanel.net> - 3.0.7-1
- EA-10739: Update ea-modsec30 from v3.0.6 to v3.0.7

* Thu Dec 16 2021 Dan Muey <dan@cpanel.net> - 3.0.6-2
- ZC-9203: Update DISABLE_BUILD to match OBS

* Mon Nov 22 2021 Cory McIntire <cory@cpanel.net> - 3.0.6-1
- EA-10286: Update ea-modsec30 from v3.0.5 to v3.0.6

* Tue Nov 02 2021 Julian Brown <julian.brown@cpanel.net> - 3.0.5-2
- ZC-9451: Move modsec30 template to ea-modsec30

* Mon Oct 04 2021 Cory McIntire <cory@cpanel.net> - 3.0.5-1
- EA-10158: Update ea-modsec30 from v3.0.4 to v3.0.5

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

