%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%{!?__initddir: %define __initddir /etc/rc.d/init.d}
%{!?_unitdir: %define _unitdir /usr/lib/systemd/system}

Name:           plight
Version:        0.1.1
Release:        2%{?dist}
Group:          Applications/Systems
Summary:        Application agnostic tool to represent node availability.

License:        ASLv2
URL:            https://github.com/rackerlabs/plight
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildRequires:  python-setuptools
Requires(pre):  shadow-utils
Requires:       python
Requires:       python-daemon
Requires:       python-setuptools

%define service_name %{name}d

%if 0%{?rhel} == 5 || 0%{?rhel} == 6
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
%else
Requires(post): systemd
Requires(preun): systemd
Requires(preun): systemd
BuildRequires: systemd
%endif

%description
Plight is a lightweight daemon providing a state machine to be
used for determining the active functionality of a machine. Such
as "in rotation" (enabled) or "in maintenance" (disabled).
The states are also configurable.


%prep
%setup -q -n %{name}-%{version}


%build

%pre
/usr/bin/getent group plight >/dev/null || /usr/sbin/groupadd -r plight
/usr/bin/getent passwd plight >/dev/null || \
    /usr/sbin/useradd -r -g plight -d /var/lib/plight -s /sbin/nologin \
    -c "System account for plight daemon" plight
exit 0

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root $RPM_BUILD_ROOT
mkdir -p %{buildroot}%{_localstatedir}/log/%{name}
mkdir -p %{buildroot}%{_localstatedir}/lib/%{name}
mkdir -p %{buildroot}%{_initddir}
mkdir -p %{buildroot}%{_unitdir}
%if 0%{?rhel} == 5 || 0%{?rhel} == 6
    mv %{buildroot}/etc/init.d/%{service_name}.init %{buildroot}%{__initddir}/%{service_name}
    rm -rf %{buildroot}%{_unitdir}
%else
    rm -rf %{buildroot}/etc/init.d
%endif



%post
%if 0%{?rhel} == 5 || 0%{?rhel} == 6
  /sbin/chkconfig --add %{service_name}
%else
  %systemd_post %{service_name}.service
%endif
if [ $1 -eq 2 ] ; then
  if [ -f /var/tmp/node_disabled ]; then
    mv /var/tmp/node_disabled /var/lib/plight/node_disabled
  fi
fi


%preun
%if 0%{?rhel} == 5 || 0%{?rhel} == 6
  if [ $1 -eq 0 ] ; then
    /sbin/service %{service_name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{service_name}
  fi
%else
  %systemd_preun %{service_name}.service
%endif

%postun
if [ "$1" -ge "1" ] ; then
%if 0%{?rhel} == 5 || 0%{?rhel} == 6
  /sbin/service %{service_name} condrestart >/dev/null 2>&1 || :
%else
  %systemd_postun_with_restart %{service_name}.service
%endif
fi

%files
%doc README.md
%{python_sitelib}/%{name}
%{python_sitelib}/%{name}*.egg-info
%config(noreplace) %attr(0644,plight,plight) %{_sysconfdir}/%{name}.conf
%attr(0755,-,-) %{_bindir}/%{name}
%dir %attr(0755,plight,plight) %{_localstatedir}/log/%{name}/
%ghost %dir %attr(0755,plight,plight) %{_localstatedir}/run/%{name}/
%dir %attr(0755,plight,plight) %{_localstatedir}/lib/%{name}/
%if 0%{?rhel} == 5 || 0%{?rhel} == 6
  %attr(0755,-,-) %{_initrddir}/%{service_name}
%else
  %{_unitdir}/%{service_name}.service
%endif

%changelog
* Fri May 29 2015 Greg Swift <greg.swift@rackspace.com> - 0.1.1-1
- Updates to syncronize with new debian package
- Use /var/lib/plight as home, not /var/run - old users will have to manually deal

* Tue May 19 2015 Greg Swift <greg.swift@rackspace.com> - 0.1.0-2
- Handle init script different to better suport debian in the project

* Mon Apr 06 2015 Greg Swift <greg.swift@rackspace.com> - 0.1.0-1
- Introduce offline mode

* Fri Jan 09 2015 Chad Wilson <chad.wilson@rackspace.com> - 0.0.4-4
- leave service restart on update to postuninstall scriptlet

* Wed Jan 07 2015 Chad Wilson <chad.wilson@rackspace.com> - 0.0.4-3
- update RPM post-install scriptlet if clauses

* Mon Jan  5 2015 Greg Swift <greg.swift@rackspace.com> - 0.0.4-2
- Typo in post scriplet performing move

* Mon Dec 29 2014 Greg Swift <greg.swift@rackspace.com> - 0.0.4-1
- Update init script to add condrestart condition (helps upgrades from 0.0.2-4)
- Updated spec to handle transition of node_disabled file path

* Fri Nov 14 2014 Chad Wilson <chad.wilson@rackspace.com> - 0.0.3-1
- Add support for HEAD requests

* Tue Apr 08 2014 Alex Schultz <alex.schultz@rackspace.com> - 0.0.2-6
- Update init script to fix error when no parameters are passed in
- Fixed spec email address

* Wed Mar 26 2014 Greg Swift <greg.swift@rackspace.com> - 0.0.2-5
- Add default value for _unitdir for older distributions without

* Tue Mar 25 2014 Greg Swift <greg.swift@rackspace.com> - 0.0.2-4
- Update to include systemd support
- Support plight specific state directory

* Tue Mar 25 2014 Greg Swift <greg.swift@rackspace.com> - 0.0.2-3
- bump of release for copr build system for el5

* Wed Feb 05 2014 Alex Schultz <alex.schultz@rackspace.com> - 0.0.2-2
- python-setuptools is required to run the plight command

* Wed Jan 29 2014 Alex Schultz <alex.schultz@rackspace.com> - 0.0.2-1
- CentOS/RHEL 5 support
- Removed cherrypy, replaced with python-daemon

* Wed Jan 22 2014 Greg Swift <gregswift@gmail.com> - 0.0.1-1
- Initial spec
