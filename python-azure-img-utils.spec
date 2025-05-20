#
# spec file for package python-azure-img-utils
#
# Copyright (c) 2025 SUSE LLC
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

%define upstream_name azure-img-utils
%if 0%{?suse_version} >= 1600
%define pythons %{primary_python}
%else
%{?sle15_python_module_pythons}
%endif
%global _sitelibdir %{%{pythons}_sitelib}

Name:           python-azure-img-utils
Version:        2.4.0
Release:        0
Summary:        Package that provides utilities for handling images in Azure Cloud
License:        GPL-3.0-or-later
URL:            https://github.com/SUSE-Enceladus/azure-img-utils
Source:         https://files.pythonhosted.org/packages/source/a/azure-img-utils/azure-img-utils-%{version}.tar.gz
BuildRequires:  python-rpm-macros
BuildRequires:  fdupes
BuildRequires:  %{pythons}-msal
BuildRequires:  %{pythons}-azure-identity
BuildRequires:  %{pythons}-azure-mgmt-compute >= 26.1.0
BuildRequires:  %{pythons}-azure-mgmt-storage
BuildRequires:  %{pythons}-azure-storage-blob >= 12.0.1
BuildRequires:  %{pythons}-requests
BuildRequires:  %{pythons}-jmespath
BuildRequires:  %{pythons}-click
BuildRequires:  %{pythons}-pytest
BuildRequires:  %{pythons}-PyYAML
BuildRequires:  %{pythons}-pip
BuildRequires:  %{pythons}-wheel
Requires:       %{pythons}-msal
Requires:       %{pythons}-azure-identity
Requires:       %{pythons}-azure-mgmt-compute >= 26.1.0
Requires:       %{pythons}-azure-mgmt-storage
Requires:       %{pythons}-azure-storage-blob >= 12.0.1
Requires:       %{pythons}-requests
Requires:       %{pythons}-jmespath
Requires:       %{pythons}-click
Requires:       %{pythons}-PyYAML

Provides:       python3-azure-img-utils = %{version}
Obsoletes:      python3-azure-img-utils < %{version}

%description
Package that provides utilities for handling images in Azure Cloud.

%prep
%autosetup -n azure-img-utils-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%fdupes %{buildroot}%{_sitelibdir}

%check
%pytest -k "not test_cli"

%files
%license LICENSE
%doc CHANGES.md README.md
%{_sitelibdir}/azure_img_utils/
%{_sitelibdir}/azure_img_utils-*.dist-info/
%{_bindir}/azure-img-utils

%changelog
