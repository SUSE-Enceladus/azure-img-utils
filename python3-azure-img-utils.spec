#
# spec file for package python3-azure-img-utils
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


Name:           python3-azure-img-utils
Version:        0.1.1
Release:        0
Summary:        Package that provides utilities for handling images in Azure Cloud
License:        GPL-3.0-or-later
URL:            https://github.com/SUSE-Enceladus/azure-img-utils
Source:         https://files.pythonhosted.org/packages/source/a/azure-img-utils/azure-img-utils-%{version}.tar.gz
BuildRequires:  python-rpm-macros
BuildRequires:  python3-msal
BuildRequires:  python3-azure-identity
BuildRequires:  python3-azure-mgmt-compute >= 17.0.0
BuildRequires:  python3-azure-mgmt-storage
BuildRequires:  python3-azure-storage-blob >= 12.0.0
BuildRequires:  python3-requests
BuildRequires:  python3-jmespath
BuildRequires:  python3-pytest
Requires:       python3-msal
Requires:       python3-azure-identity
Requires:       python3-azure-mgmt-compute >= 17.0.0
Requires:       python3-azure-mgmt-storage
Requires:       python3-azure-storage-blob >= 12.0.0
Requires:       python3-requests
Requires:       python3-jmespath

%description
Package that provides utilities for handling images in Azure Cloud.

%prep
%setup -q -n azure-img-utils-%{version}

%build
python3 setup.py build

%install
python3 setup.py install --prefix=%{_prefix} --root=%{buildroot}

%check
python3 -m pytest

%files
%license LICENSE
%doc python3-azure-img-utils.changes README.md
%{python3_sitelib}/*
%{_bindir}/azure-img-utils

%changelog
