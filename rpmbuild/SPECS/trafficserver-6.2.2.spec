#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

%global install_prefix "/opt"


Name:		trafficserver
Version:	6.2.2
Release:	8182%{?dist}
Summary:	Apache Traffic Server
Vendor:		Comcast
Group:		Applications/Communications
License:	Apache License, Version 2.0
URL:		https://github.com/apache/trafficserver/tree/6.2.x
Epoch:          7079
#Source0:        %{name}-%{version}.tar.bz2
Source1:        trafficserver.service
Source2:        trafficserver.sysconfig
Source3:        trafficserver.tmpfilesd
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
Requires:	tcl, hwloc, pcre, openssl, libcap
BuildRequires:	autoconf, automake, libtool, gcc-c++, glibc-devel, openssl-devel, expat-devel, pcre, libcap-devel, pcre-devel, perl-ExtUtils-MakeMaker, tcl-devel, hwloc-devel

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
Apache Traffic Server with Comcast modifications and environment specific modifications

%prep
rm -rf %{name}
git clone --branch 6.2.2 https://github.com/apache/trafficserver.git
cd trafficserver
#git checkout tags/6.2.2
#git checkout %{commit} .
#wget https://raw.githubusercontent.com/apache/incubator-trafficcontrol/master/traffic_server/plugins/astats_over_http/astats_over_http.c -o 
cd ..
#mv trafficserver %{name}
#rm -rf trafficserver
%setup -D -n %{name} -T
autoreconf -vfi

#%setup
#%patch -p1

%build
./configure --prefix=%{install_prefix}/%{name} --with-user=ats --with-group=ats --with-build-number=%{release} --enable-experimental-plugins
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

# Remove duplicate man-pages:
rm -rf %{buildroot}%{_docdir}/trafficserver

mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
install -m 644 -p %{SOURCE2} \
   %{buildroot}%{_sysconfdir}/sysconfig/trafficserver


%if %{?fedora}0 > 140 || %{?rhel}0 > 60
install -D -m 0644 -p %{SOURCE1} \
   %{buildroot}/lib/systemd/system/trafficserver.service
install -D -m 0644 -p %{SOURCE3} \
   %{buildroot}%{_sysconfdir}/tmpfiles.d/trafficserver.conf
%else
mv %{buildroot}/usr/bin/trafficserver %{buildroot}/etc/init.d
mkdir -p %{buildroot}/etc/init.d/
%endif

mkdir -p $RPM_BUILD_ROOT%{install_prefix}/trafficserver/etc/trafficserver/snapshots

%clean
rm -rf $RPM_BUILD_ROOT

%pre
getent group ats >/dev/null || groupadd -r ats -g 176 &>/dev/null
getent passwd ats >/dev/null || \
useradd -r -u 176 -g ats -d / -s /sbin/nologin \
	-c "Apache Traffic Server" ats &>/dev/null
#id ats &>/dev/null || /usr/sbin/useradd -u 176 -r ats -s /sbin/nologin -d /

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
#/etc/init.d/%{name} stop
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
#%attr(755,-,-) /etc/init.d/trafficserver
%dir /opt/trafficserver
%if %{?fedora}0 > 140 || %{?rhel}0 > 60
/lib/systemd/system/trafficserver.service
%config(noreplace) %{_sysconfdir}/tmpfiles.d/trafficserver.conf
%else
/etc/init.d/trafficserver
%endif
/opt/trafficserver/bin
%config(noreplace) %{_sysconfdir}/sysconfig/trafficserver
/opt/trafficserver/include
/opt/trafficserver/lib
/opt/trafficserver/man
#/opt/trafficserver/lib64
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
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/cluster.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/congestion.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/hosting.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/icp.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/ip_allow.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/log_hosts.config
#%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/logging.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/logs_xml.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/metrics.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/parent.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/plugin.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/records.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/remap.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/socks.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/splitdns.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/ssl_multicert.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/storage.config
#%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/update.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/vaddrs.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/volume.config
#%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/prefetch.config
%config(noreplace) %attr(644,ats,ats) /opt/trafficserver/etc/trafficserver/stats.config.xml
