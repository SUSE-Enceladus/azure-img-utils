
# Overview

**azure-img-utils** provides a command line utility and API for publishing
images in the Azure Cloud. This includes helper functions for uploading
image blobs, creating compute images and publish/share images across
all available regions.

See the [Azure docs](https://docs.microsoft.com/en-us/azure/) to get
more info on the Azure cloud.

# Requirements

The requirements for the project can be found in the following repo files:
- [requirements](requirement.txt)
- [requirements for testing](requirement-test.txt)
- [requirements for development](requirement-dev.txt)

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
- credentials_file
- resource_group
- region
- container
- storage_account


An example configuration profile may look like:

```yaml
region: westus
no_color: True
credentials_file: mycredentials.json
container: my_container
```

When running any command the profile can be chosen via the *--profile* option.
For example, *azure-img-utils image blobexists --profile production* would pull
configuration from ~/.config/azure_img_utils/production.yaml.


# CLI

The CLI is broken into multiple distinct subcommands that handle different
steps of creating and publishing images in the Azure cloud framework.

## Authentication

This cli tool expects the user to provide a json file containing the
credentials of a service principal to access his/her Azure services.

Per Azure documentation:
> An Azure service principal is an identity created for use with applications,
> hosted services, and automated tools to access Azure resources.

[Here](https://docs.microsoft.com/en-us/cli/azure/create-an-azure-service-principal
-azure-cli) you can find how to create a service principal with the azure cli.

With your subscriptionId, the resourceGroupId and the required permissions, you can
create the service principal with the following command:

```sh
az ad sp create-for-rbac \
        --sdk-auth \
        --role Contributor \
        --scopes /subscriptions/{YOUR_SUSCRI_ID}/resourceGroups/{YOUR_RES_GROUP_ID} \
        --name "YOUR_SP_NAME" > mycredentials.json
```

The expected format for the json file is the output for that *create-for-rbac* az
command. Note that the API this repo provides allows additional methods of
authentication, but these are not supported in this CLI tool.


## blob command
### exists subcommand

This subcommand allows the user to check if a blob exists in the storage
container specified. The subcommand is *azure-img-utils blob exists*.

The *required* parameters for the execution of the command:
- --storage-account
- --blob-name
- --container

Example:

```shell
$ azure-img-utils blob exists --storage-account myStorageAccount \
                              --blob-name myBlobName \
                              --container myContainerName
```

This command will output *true* or *false* depending on the existance of the
blob.

For more information about the blob exists command see the help message:

```shell
$ azure-img-utils blob exists --help
```

### upload subcommand

This subcommand allows the user to upload a file as a blob to the storage
container specified. The subcommand is *azure-img-utils blob upload*.

The *required* parameters for the execution of the command:
- --storage-account
- --blob-name
- --container
- --image-file

Some *optional* parameters for the execution of the command include:
- --force-replace-image  (defaults to False)
- --page-blob            (defaults to False)
- --expand-image         (defaults to False)
- --max-workers          (defaults to None(no limit))
- --max-retry-attempts   (defaults to None(no limit))


Example:

```shell
$ azure-img-utils blob upload --storage-account myStorageAccount \
                              --blob-name myBlobName \
                              --container myContainerName \
                              --image-file myImageFile.qcow2
```

This command will output if the upload has been successful or not.

For more information about the blob upload command see the help message:

```shell
$ azure-img-utils blob upload --help
```

### delete subcommand

This subcommand allows the user to delete a blob file from the storage
container specified. The subcommand is *azure-img-utils blob delete*.

The *required* parameters for the execution of the command:
- --storage-account
- --blob-name
- --container

Some *optional* parameters for the execution of the command:
- --yes  (avoids interactive confirmation for the deletion)

Example:

```shell
$ azure-img-utils blob delete --storage-account myStorageAccount \
                              --blob-name myBlobName \
                              --container myContainerName \
                              --yes
```

This command will output if the deletion has been successful or not.

For more information about the blob delete command see the help message:

```shell
$ azure-img-utils blob delete --help
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
    container="my_container_name",
    storage_account="my_storage_account",
    credentials=my_credentials_dict,
    credentials_file="my_credentials_file.json",
    resource_group="my_resource_group",
    sas_token="my_sas_token",
    log_level=my_log_level,
    log_callback=logger
    timeout=myTimeout
)
```

## Code examples

With an instance of AzureImage you can perform any of the image functions
which are available through the CLI.

```python
azure_image = AzureImage(
    container="my_container",
    storage_account="my_storage_account",
    credentials_file="my_credentials.json",
    resource_gropu="my_resource_group",
    sas_token="my_sas_token"
)
```

### Check if image blob exists
```python
blob_exists = azure_image.image_blob_exists("my_blob_name")
```

# Delete storage blob
```python
blob_deleted = azure_image.delete_storage_blob("my_blob_name")
```

### Upload image blob
```python
blob_name = azure_image.upload_image_blob(
    "my_image_file.qcow2",
    blob_name="my_blob_name"
)
```

### Check if image exists
```python
image_exists = azure_image.image_exists("my_image_name")
```

### Check if gallery image version exists
```python
gallery_image_version_exists = azure_image.gallery_image_version_exists(
    "my_gallery_name",
    "my_gallery_image_name",
    "my_image_version",
    gallery_resource_group="my_gallery_resource_group"
)
```

### Delete compute image
```python
azure_image.delete_compute_image("my_image_name")
```

### Delete gallery image version
```python
azure_image.delete_gallery_image_version(
    "my_gallery_name",
    "my_gallery_image_name",
    "my_image_version",
    gallery_resource_group="my_gallery_resource_group"
)
```

### Get compute image dictionary
```python
image_dict = azure_image.get_compute_image("my_image_name")
```

### Get gallery image version
```python
image_dict = azure_image.get_gallery_image_version(
    "my_gallery_name",
    "my_gallery_image_name",
    "my_image_version",
    gallery_resource_group="my_gallery_resource_group"
)
```

### Create compute image
```python
image_name = azure_image.create_compute_image(
    "my_blob_name",
    "my_image_name",
    "my_region",
    force_replace_image=True,
    hyper_v_generation='V1'
)
```

### Create gallery image version
```python
image_name = azure_image.create_gallery_image_version(
    "my_blob_name",
    "my_gallery_name",
    "my_gallery_image_name",
    "my_image_version",
    "my_region",
    force_replace_image=True,
    gallery_resource_group="my_gallery_resource_group"
)
```

### Get offer doc dictionary
```python
offer_doc = azure_image.get_offer_doc(
    "my_offer_id",
    "my_publisher_id"
)
```

### Upload offer doc
```python
azure_image.upload_offer_doc(
    "my_offer_id",
    "my_publisher_id"
    my_offer_doc_dict
)
```

### Add image to offer
```python
azure_image.add_image_to_offer(
    "my_blob_name",
    "my_image_name",
    "my image description...",
    "my_offer_id",
    "my_publisher_id",
    "my_label",
    "my_sku",
    blob_url="https://my.blob.url",
    generation_id="my_generation_id",
    generation_suffix="my_generation_suffix",
    vm_images_key="my_images_key"
)
```

### Remove image from offer
```python
azure_image.add_image_to_offer("my_image_urn")
```

### Publish offer
```python
operation_uri = azure_image.publish_offer(
    "my_offer_id",
    "my_publisher_id",
    "my_notification_emaili1@whatever.com,my_not_email2@somedomain.com'
)
```

### Go live with offer
```python
operation_uri = azure_image.go_live_with_offer(
    "my_offer_id",
    "my_publisher_id",
)
```

### Get offer status
```python
offer_status = azure_image.get_offer_status(
    "my_offer_id",
    "my_publisher_id",
)
```

### Get operation
```python
operation_status = azure_image.get_operation("my_operation")
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
