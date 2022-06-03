
# Overview

**azure-img-utils** provides a command line utility and API for publishing
images in the Azure Cloud. This includes helper functions for uploading
image blobs, creating compute images and replicating/publishing/deprecating/
images across all available regions.

See the [Azure docs](https://docs.microsoft.com/en-us/azure/) to get
more info on the Azure cloud.

# Requirements

- click
- msal
- azure-identity
- azure-mgmt-compute>=26.1.0
- azure-mgmt-storage
- azure-storage-blob>=12.0.0
- requests
- jmespath

# Installation

To install the package on openSUSE and SLES use the following commands as root:

```shell
$ zypper ar http://download.opensuse.org/repositories/Cloud:/Tools/<distribution>
$ zypper refresh
$ zypper in python3-azure-img-utils
```

To install from PyPI:

```shell
$ pip install azure-img-utils
```

# Configuration

**azure-img-utils** can be configured with yaml based profiles. The configuration
directory is `~/.config/azure_img_utils` and the default profile is default.yaml
(~/.config/azure_img_utils/default.yaml).

The following configration options are available in a configuration profile:

- no_color
- log_level
- sas_token
- client_id
- client_secret
- subscription_id
- tenant_id
- active_directory_url
- resource_manager_url
- active_directory_graph_res_url
- sql_management_url
- gallery_url
- management_url
- credentials_file
- resource_group
- region


An example configuration profile may look like:

```yaml
region: westus
no_color: True
credentials_file: mycredentials.json
```

When running any command the profile can be chosen via the *--profile* option.
For example, *azure-img-utils image blobexists --profile production* would pull
configuration from ~/.config/azure_img_utils/production.yaml.

# CLI

The CLI is broken into multiple distinct subcommands that handle different
steps of creating and publishing images in the Azure cloud framework.

## Image blob exists

This subcommand allows the user to check if a blob exists in the storage
container specified. The subcommand is *azure-img-utils image blobexists*.

The required parameters for the execution of the command:
- --storage-account
- --blob-name
- --container

Example:

```shell
$ azure-img-utils image blobexists --storage-account myStorageAccount \
                                   --blob-name myBlobName \
                                   --container myContainerName
```

This command will output *True* or *False* depending on the existance of the
blob.

For more information about the image blobexists function see the help message:

```shell
$ azure-img-utils image blobexists --help
```

## Image upload blob

This subcommand allows the user to upload the image file to the storage
container specified. The subcommand is *azure-img-utils image uploadblob*.

The required parameters for the execution of the command:
- --storage-account
- --blob-name
- --container
- --image-file

Example:

```shell
$ azure-img-utils image uploadblob --storage-account myStorageAccount \
                                   --blob-name myBlobName \
                                   --container myContainerName \
                                   --image-file myImageFile.qcow2
```

This command will output if the upload has been successful or not.

For more information about the image uploadblob function see the help message:

```shell
$ azure-img-utils image uploadblob --help
```

## Image delete blob

This subcommand allows the user to delete the image blob file from the storage
container specified. The subcommand is *azure-img-utils image deleteblob*.

The required parameters for the execution of the command:
- --storage-account
- --blob-name
- --container

Example:

```shell
$ azure-img-utils image deleteblob --storage-account myStorageAccount \
                                   --blob-name myBlobName \
                                   --container myContainerName
```

This command will output if the deletion has been successful or not.

For more information about the image deleteblob function see the help message:

```shell
$ azure-img-utils image blob --help
```

# API

The AzureImage class can be instantiated and used as an API from code.
This provides all the same functions as the CLI with a few additional
helpers. For example there are waiter functions which will wait for
a compute image to be created and/or deleted.

To create an instance of AzureImage you need a *storage_account*,
*credentials dictionary object* or *credentials file* or *sas token*
*container* and *resource group*. Optionally you can pass
in a Python log object and/or a *log_level* and/or a *timeout* value.

Note that you can provide authentication credentials in 3 different ways:
- with a sas_token
- with a dictionary of credentials containing the required key values
- with the credentials file name
Providing just one of these options is enough to perform the authentication
in the Azure API.

```python
azure_image = AzureImage(
    container,
    storage_account,
    credentials,
    credentials_file,
    resource_group,
    sas_token,
    log_level=log_level,
    log_callback=logger
    timeout=myTimeout
)
```

## Code examples

With an instance of AzureImage you can perform any of the image functions
which are available through the CLI.

```python
azure_image = AzureImage(
    'myContainer',
    'myStorageAccount',
    None,
    'myCredentialsFile',
    'myResourceGroup',
    'mySasToken
)
```

### Check if image blob exists
```python
blob_exists = azure_image.image_blob_exists('myBlobName')
```

# Delete storage blob
```python
blob_deleted = azure_image.delete_storage_blob('myBlobName')
```

### Upload image blob
```python
blob_name = azure_image.upload_image_blob(
	image_file='myImageFile.qcow2',
        blob_name='myBlobName'
	)
```

### Check if image exists
```python
image_exists = azure_image.image_exists('myImageName')
```

### Check if gallery image version exists
```python
gallery_image_version_exists = azure_image.gallery_image_version_exists(
	'myGalleryName',
        'myGalleryImageName',
        'myImageVersion',
        'myGalleryResourceGroup'
    )
```

### Delete compute image
```python
azure_image.delete_compute_image('myImageName')
```

### Delete gallery image version
```python
azure_image.delete_gallery_image_version(
	'myGalleryName',
	'myGalleryImageName',
	'myImageVersion',
	'myGalleryResourceGroup,
	)
```

### Get compute image dictionary
```python
image_dict = azure_image.get_compute_image('myImageName')
```

### Get gallery image version
```python
image_dict = azure_image.get_gallery_image_version(
	'myGalleryName',
        'myGalleryImageName',
        'myImageVersion',
        'myGalleryResourceGroup'
	)
```

### Create compute image
```python
image_name = azure_image.create_compute_image(
	'myBlobName',
        'myImageName',
        'myRegion'
	)
```

### Create gallery image version
```python
image_name = azure_image.create_gallery_image_version(
	'myBlobName',
        'myGalleryName',
        'myGalleryImageName',
        'myImageVersion',
        'myRegion'
	)
```

### Get offer doc dictionary
```python
offer_doc = azure_image.get_offer_doc(
	'myOfferId',
        'myPublisherId'
	)
```

### Upload offer doc
```python
azure_image.upload_offer_doc(
	'myOfferId',
        'myPublisherId',
        offer_doc_dict
	)
```

### Add image to offer
```python
azure_image.add_image_to_offer(
	'myBlobName',
        'myImageName',
        'myImageDescription',
        'myOfferId',
        'myPublisherId',
        'myLabel',
        'mySku'
	)
```

### Remove image from offer
```python
azure_image.add_image_to_offer('myImageUrn')
```

### Publish offer
```python
operation_uri = azure_image.publish_offer(
	'myOfferId',
        'myPublisherId',
        'myNotificationEmailList'
	)
```

### Go live with offer
```python
operation_uri = azure_image.go_live_with_offer(
	'myOfferId',
        'myPublisherId'
	)
```

### Get offer status
```python
offer_status = azure_image.get_offer_status(
	'myOfferId',
        'myPublisherId'
	)
```

### Get operation
```python
operation_status = azure_image.get_operation('myOperation')
```

# Issues/Enhancements

Please submit issues and requests to
[Github](https://github.com/SUSE-Enceladus/azure-img-utils/issues).

# Contributing

Contributions to **azure-img-utils** are welcome and encouraged. See
[CONTRIBUTING](https://github.com/SUSE-Enceladus/azure-img-utils/blob/master/CONTRIBUTING.md)
for info on getting started.

# License

Copyright (c) 2022 SUSE LLC.

Distributed under the terms of GPL-3.0+ license, see
[LICENSE](https://github.com/SUSE-Enceladus/azure-img-utils/blob/master/LICENSE)
for details.
