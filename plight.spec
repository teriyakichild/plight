%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

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


%description
PasswordSafe is a secure centralized and shareable secrets storage mechanism.
This library allows you to interact with that 

%prep
%setup -q -n %{name}-%{version}


%build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root $RPM_BUILD_ROOT

%files
%doc README.md
%{python_sitelib}/%{name}
%{python_sitelib}/%{name}*.egg-info
%attr(0755,-,-) %{_bindir}/plightd
%attr(0755,-,-) %{_bindir}/plight


%changelog
* Wed Jan 22 2014 Greg Swift <gregswift@gmail.com> - 0.0.1-1
- Initial spec
