v2.4.0 (2025-05-20)
===================

- Migrate to new arg name for image creation
- Build for one version of python

v2.3.0 (2024-05-23)
===================

- Update spec for python 3.11 build

v2.2.0 (2024-03-08)
===================

- Add optional wait arg to submit_request
- Do not wait on publish or go live operations

v2.1.0 (2024-03-06)
===================

- Add waiter method to get status for async operations

v2.0.1 (2024-02-22)
===================

- Fix readme to match cloud partner function changes

v2.0.0 (2024-02-22)
===================

- Migrate cloud partner functions to new Graph API

v1.2.0 (2023-10-16)
===================

- Includes response body in exception in raise_for_status
- Pass scopes as a list in API call
- Add config dir override to fix test failure
- Add offer exists function
- Add get-offer-doc command for cli

v1.1.0 (2022-11-16)
===================

- Explicit error if notification emails is not present
  during publish process
- Do not delete image version if no other versions exist.
  Instead raise an exception.

v1.0.2 (2022-07-06)
===================

- Skip CLI tests

v1.0.1 (2022-07-06)
===================

- Add click requirement to spec

v1.0.0 (2022-07-06)
===================

- Raise exception if no credentials provided
- Add CLI
- Migrate utility functions to class methods where names overlap

v0.4.1 (2022-05-16)
===================

- Bump azure-mgmt-compute min version requirement for SIG
- Allow optional gallery resource group

v0.4.0 (2022-05-11)
===================

- Add endpoints for processing shared image gallery images.

v0.3.0 (2022-04-08)
===================

- Drive image removal by image URN
- Make all args optional at class instantiation of AzureImage
  + Instead catch missing args in a lazy fashion

v0.2.2 (2022-03-24)
===================

- Capitalize Hyper v default generation
- Raise exception if resource group missing when creating or
  deleting compute images.

v0.2.1 (2022-03-16)
===================

- No changes: Re-sync OBS and PyPI versions.

v0.2.0 (2022-03-16)
===================

- Add method for removing an image version from an offer.

v0.1.1 (2021-12-17)
===================

- Add rpm-macros to build requirements in spec.

v0.1.0 (2021-12-10)
===================

- Retry all failed requests

v0.0.3 (2021-10-05)
===================

- Migrate changes file.

v0.0.2 (2021-09-29)
===================

- Fix singledispatch registration of get_blob_service for py3.6
  compatibility.
- Setup CI/CT workflows.

v0.0.1 (2021-08-17)
===================

- Initial release

