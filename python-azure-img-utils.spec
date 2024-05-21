#
# spec file for package python-azure-img-utils
#
# Copyright (c) 2021 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#

%{?sle15_python_module_pythons}
%global skip_python2 1

%if 0%{?suse_version} > 1500
%bcond_without libalternatives
%else
%bcond_with libalternatives
%endif

Name:           python-azure-img-utils
Version:        2.2.0
Release:        0
Summary:        Package that provides utilities for handling images in Azure Cloud
License:        GPL-3.0-or-later
URL:            https://github.com/SUSE-Enceladus/azure-img-utils
Source:         https://files.pythonhosted.org/packages/source/a/azure-img-utils/azure-img-utils-%{version}.tar.gz
BuildRequires:  python-rpm-macros
BuildRequires:  %{python_module msal}
BuildRequires:  %{python_module azure-identity}
BuildRequires:  %{python_module azure-mgmt-compute >= 26.1.0}
BuildRequires:  %{python_module azure-mgmt-storage}
BuildRequires:  %{python_module azure-storage-blob >= 12.0.1}
BuildRequires:  %{python_module requests}
BuildRequires:  %{python_module jmespath}
BuildRequires:  %{python_module click}
BuildRequires:  %{python_module pytest}
BuildRequires:  %{python_module PyYAML}
BuildRequires:  %{python_module pip}
BuildRequires:  %{python_module wheel}
Requires:       python-msal
Requires:       python-azure-identity
Requires:       python-azure-mgmt-compute >= 26.1.0
Requires:       python-azure-mgmt-storage
Requires:       python-azure-storage-blob >= 12.0.1
Requires:       python-requests
Requires:       python-jmespath
Requires:       python-click
Requires:       python-PyYAML
%if %{with libalternatives}
BuildRequires:  alts
Requires:       alts
%else
Requires(post): update-alternatives
Requires(postun): update-alternatives
%endif

Provides:       python3-azure-img-utils = %{version}
Obsoletes:      python3-azure-img-utils < %{version}
%python_subpackages

%description
Package that provides utilities for handling images in Azure Cloud.

%prep
%autosetup -n azure-img-utils-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%python_clone -a %{buildroot}%{_bindir}/azure-img-utils

%check
%pytest -k "not test_cli"

%pre
%python_libalternatives_reset_alternative azure-img-utils

%post
%{python_install_alternative azure-img-utils}

%postun
%{python_uninstall_alternative azure-img-utils}

%files %{python_files}
%license LICENSE
%doc CHANGES.md README.md
%{python_sitelib}/*
%python_alternative %{_bindir}/azure-img-utils

%changelog

