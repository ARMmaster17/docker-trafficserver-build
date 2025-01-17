%global install_prefix "/opt"

Name:		trafficserver
Version:	9.2.0
Release:	%{getenv:TS_EPOCH}%{?dist}
Summary:	Apache Traffic Server
Group:		Applications/Communications
License:	Apache License, Version 2.0
URL:		https://github.com/apache/trafficserver
Epoch:          %{getenv:TS_EPOCH}
Source0:        %{name}-%{version}-%{epoch}.tar.bz2
%undefine _disable_source_fetch
#Source1:        trafficserver.service
Source2:        trafficserver.sysconfig
Source3:        trafficserver.tmpfilesd
Source4:        trafficserver-rsyslog.conf
Patch0:         trafficserver-crypto-policy.patch
Patch1:		https://patch-diff.githubusercontent.com/raw/apache/trafficserver/pull/9579.diff
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
Requires:	tcl, hwloc, pcre, openssl, libcap
Requires:       rsyslog
Requires:       logrotate
Requires:       libcap, cjose, jansson
Requires:       expat, hwloc, pcre, xz, ncurses, pkgconfig
BuildRequires:	autoconf, automake, libtool, gcc-c++, glibc-devel, openssl-devel, expat-devel, pcre, libcap-devel, pcre-devel, hwloc-devel, luajit-devel,
%if 0%{?fedora} >= 21 || 0%{?rhel} >= 8
BuildRequires: cjose-devel, jansson-devel
%endif
Requires: initscripts
%if %{?fedora}0 > 140 || %{?rhel}0 > 60
# For systemd.macros
BuildRequires: systemd
Requires: systemd
Requires(postun): systemd
%else
Requires(post): chkconfig
Requires(preun): chkconfig initscripts
Requires(postun): initscripts
%endif

%description
Apache Traffic Server for Traffic Control with astats_over_http plugin

%prep
rm -rf %{name}-%{version}
#%autosetup -p0
%setup -q
%patch0 -p0
%patch1 -p0
autoreconf -vfi

%build
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
chmod +x ./configure
./configure \
  --enable-experimental-plugins \
  --prefix=%{install_prefix}/%{name} \
  --with-user=ats --with-group=ats \
  --with-build-number=%{release} \
  --disable-unwind
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
install -m 644 -p %{SOURCE2} \
   %{buildroot}%{_sysconfdir}/sysconfig/trafficserver

mkdir -p %{buildroot}%{_sysconfdir}/rsyslog.d
install -m 644 -p %{SOURCE4} \
   %{buildroot}%{_sysconfdir}/rsyslog.d/trafficserver.conf

#install -D -m 0644 -p %{SOURCE1} \
#   %{buildroot}/lib/systemd/system/trafficserver.service
mkdir -p %{buildroot}%{_unitdir}/
cp $RPM_BUILD_DIR/%{name}-%{version}/rc/trafficserver.service %{buildroot}%{_unitdir}/
install -D -m 0644 -p %{SOURCE3} \
   %{buildroot}%{_sysconfdir}/tmpfiles.d/trafficserver.conf

mkdir -p $RPM_BUILD_ROOT%{install_prefix}/trafficserver/etc/trafficserver/snapshots

%clean
rm -rf $RPM_BUILD_ROOT

%pre
getent group ats >/dev/null || groupadd -r ats -g 176 &>/dev/null
getent passwd ats >/dev/null || \
useradd -r -u 176 -g ats -d / -s /sbin/nologin \
	-c "Apache Traffic Server" ats &>/dev/null
id ats &>/dev/null || /usr/sbin/useradd -u 176 -r ats -s /sbin/nologin -d /

%post
/sbin/ldconfig
%if %{?fedora}0 > 170 || %{?rhel}0 > 60
  %systemd_post trafficserver.service
%else
  if [ $1 -eq 1 ] ; then
  %if %{?fedora}0 > 140
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
  %else
    /sbin/chkconfig --add %{name}
  %endif
  fi
%endif

%preun
%if %{?fedora}0 > 170 || %{?rhel}0 > 60
  %systemd_preun trafficserver.service
%else
if [ $1 -eq 0 ] ; then
  /sbin/service %{name} stop > /dev/null 2>&1
  /sbin/chkconfig --del %{name}
fi
%endif


%postun
# Helpful in understanding order of operations in relation to install/uninstall/upgrade:
#     http://www.ibm.com/developerworks/library/l-rpm2/
# if 0 uninstall, if 1 upgrade

%if %{?fedora}0 > 170 || %{?rhel}0 > 60
  %systemd_postun_with_restart trafficserver.service
  id ats &>/dev/null && /usr/sbin/userdel ats
%else
if [ $1 -eq 1 ] ; then
  /sbin/service trafficserver condrestart &>/dev/null || :
fi
%endif

%files
%defattr(-,root,root)
%dir /opt/trafficserver
/usr/lib/systemd/system/trafficserver.service
%config(noreplace) %{_sysconfdir}/tmpfiles.d/trafficserver.conf
/opt/trafficserver/bin
%config(noreplace) %{_sysconfdir}/sysconfig/trafficserver
%{_sysconfdir}/rsyslog.d/trafficserver.conf
/opt/trafficserver/include
/opt/trafficserver/lib
/opt/trafficserver/libexec
/opt/trafficserver/share
%dir /opt/trafficserver/var
%attr(-,ats,ats) /opt/trafficserver/var/trafficserver
%dir /opt/trafficserver/var/log
%attr(-,ats,ats) /opt/trafficserver/var/log/trafficserver
%dir /opt/trafficserver/etc
%attr(-,ats,ats) %dir /opt/trafficserver/etc/trafficserver
%attr(-,ats,ats) %dir /opt/trafficserver/etc/trafficserver/snapshots
/opt/trafficserver/etc/trafficserver/body_factory
/opt/trafficserver/etc/trafficserver/trafficserver-release
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/cache.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/hosting.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/ip_allow.yaml
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/logging.yaml
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/parent.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/plugin.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/records.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/remap.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/socks.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/splitdns.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/ssl_multicert.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/storage.config
##%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/update.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/volume.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/sni.yaml
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/strategies.yaml
