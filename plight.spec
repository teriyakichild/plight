%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%{!?__initrddir: %define __initrddir /etc/rc.d/init.d}

Name:           plight
Version:        0.0.1
Release:        1%{?dist}
Summary:        Load balancer agnostic node state control service

License:        ASLv2
URL:            https://github.com/rackerlabs/plight
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python-setuptools
Requires:       python
Requires:       python-cherrypy

%define service_name %{name}d

%if 0%{?rhel} == 5 || 0%{?rhel} == 6
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
%endif

%description
PasswordSafe is a secure centralized and shareable secrets storage mechanism.
This library allows you to interact with that 

%prep
%setup -q -n %{name}-%{version}


%build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root $RPM_BUILD_ROOT
%if 0%{?rhel} == 5 || 0%{?rhel} == 6
    mv %{buildroot}%{__initrddir}/%{service_name}.init %{buildroot}%{__initrddir}/%{service_name}
    #TODO: Delete unit file when we have one
%else
    #TODO: Rename unit file
    rm -f %{buildroot}%{__initrddir}/%{service_name}.init
%endif

%if 0%{?rhel} == 5 || 0%{?rhel} == 6
# Manage the init scripts if el5/6
%post
# This adds the proper /etc/rc*.d links for the script
/sbin/chkconfig --add %{service_name}

%preun
if [ $1 -eq 0 ] ; then
    /sbin/service %{service_name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{service_name}
fi

%postun
if [ "$1" -ge "1" ] ; then
    /sbin/service %{service_name} condrestart >/dev/null 2>&1 || :
fi
%endif

%files
%doc README.md
%{python_sitelib}/%{name}
%{python_sitelib}/%{name}*.egg-info
%config(noreplace) %attr(0644,-,-) %{_sysconfdir}/%{name}.conf
%attr(0755,-,-) %{_bindir}/%{name}
%if 0%{?rhel} == 5 || 0%{?rhel} == 6
  %attr(0755,-,-) %{_initrddir}/%{service_name}
%endif

%changelog
* Wed Jan 22 2014 Greg Swift <gregswift@gmail.com> - 0.0.1-1
- Initial spec
