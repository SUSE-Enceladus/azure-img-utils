
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

Group of commands for blob management.

### exists subcommand

This subcommand allows the user to check if a blob exists in the storage
container specified. The subcommand is *azure-img-utils blob exists*.

The *required* parameters for the execution of the command (authentication
 aside):
- --storage-account
- --blob-name
- --container

Example:

```shell
$ azure-img-utils blob exists --storage-account myStorageAccount \
                              --blob-name myBlobName \
                              --container myContainerName
```

This command will output *true* or *false* depending on the existence of the
blob.

For more information about the blob exists command see the help message:

```shell
$ azure-img-utils blob exists --help
```

### upload subcommand

This subcommand allows the user to upload a file as a blob to the storage
container specified. The subcommand is *azure-img-utils blob upload*.

The *required* parameters for the execution of the command (authentication
 aside):
- --storage-account
- --blob-name
- --container
- --image-file

Some *optional* parameters for the execution of the command include:
- --force-replace-image  (defaults to False)
- --page-blob            (defaults to False)
- --expand-image         (defaults to False)
- --max-workers          (defaults to 5(no limit))
- --max-attempts   (defaults to 5(no limit))


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

The *required* parameters for the execution of the command (authentication
 aside):
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

## image command

Group of commands for image management.

### exists subcommand

This subcommand allows the user to check if an image exists.
The subcommand is *azure-img-utils image exists*.

The *required* parameters for the execution of the command (authentication
 aside):
- --image-name

Example:

```shell
$ azure-img-utils image exists --image-name myImageName
```

This command will output *true* or *false* depending on the existence of the
image.

For more information about the image exists command see the help message:

```shell
$ azure-img-utils image exists --help
```

### create subcommand

This subcommand allows the user to create an image based in one blob.
The subcommand is *azure-img-utils image create*.

The *required* parameters for the execution of the command (authentication
 aside):
- --blob-name
- --image-name
- --container
- --resource-group
- --storage-account

Some *optional* parameters for the execution of the command include:
- --force-replace-image  (defaults to False)
- --hyper-v-generation   (defaults to 'V1'(legacy bios).)
                         (Use 'V2' for uefi boot.)

Example:

```shell
$ azure-img-utils image create --blob-name myBlobName \
                               --image-name myImageName
```

For more information about the image create command see the help message:

```shell
$ azure-img-utils image create --help
```

### delete subcommand

This subcommand allows the user to delete an existing image.
The subcommand is *azure-img-utils image delete*.

The *required* parameters for the execution of the command (authentication
 aside):
- --image-name

Example:

```shell
$ azure-img-utils image delete --image-name myImageName
```

For more information about the image delete command see the help message:

```shell
$ azure-img-utils image delete --help
```

## gallery-image-version command

Group of commands for gallery image version management.

### exists subcommand

This subcommand allows the user to check if a gallery image version exists in a
 gallery.
The subcommand is *azure-img-utils gallery-image-version exists*.

The *required* parameters for the execution of the command (authentication
 aside):
- --gallery-image-name
- --gallery-name
- --gallery-image-version

Example:

```shell
$ azure-img-utils gallery-image-version exists \
                                        --gallery-image-name myImageName \
                                        --gallery-name myGalleryName \
                                        --gallery-image-version 0.0.1
```

This command will output *true* or *false* depending on the existence of the
gallery image version in the gallery.

For more information about the gallery image version exists command see the
 help message:

```shell
$ azure-img-utils gallery-image-version exists --help
```

### create subcommand

This subcommand allows the user to create a gallery image version in a gallery based
 on a blob.
The subcommand is *azure-img-utils gallery-image-version create*.

The *required* parameters for the execution of the command (authentication
 aside):
- --blob-name
- --gallery-name
- --gallery-image-name
- --gallery-image-version
- --resource-group

Some *optional* parameters for the execution of the command include:
- --force-replace-image  (defaults to False)

Example:

```shell
$ azure-img-utils gallery-image-version create \
                                        --blob-name myBlobName \
                                        --gallery-image-name myImageName \
                                        --gallery-name myGalleryName \
                                        --image-version 0.0.1 \
                                        --resource-group myResourceGroup
```

For more information about the gallery image version create command see the help
 message:

```shell
$ azure-img-utils gallery-image-version create --help
```

### delete subcommand

This subcommand allows the user to delete an existing gallery image version of
a gallery image.

The subcommand is *azure-img-utils gallery-image-version delete*.

The *required* parameters for the execution of the command (authentication
 aside):
- --gallery-name
- --gallery-image-name
- --gallery-image-version

Example:

```shell
$ azure-img-utils gallery-image-version delete \
                                            --gallery-image-name myImageName \
                                            --gallery-name myGalleryName \
                                            --gallery-image-version 0.0.1
```

For more information about the gallery image version delete command see the
help message:

```shell
$ azure-img-utils gallery-image-version delete --help
```

## cloud-partner-offer command

Group of commands for cloud partner offer management.

### publish subcommand

This subcommand allows the user to publish a cloud partner offer.

The subcommand is *azure-img-utils cloud-partner-offer publish*.

The *required* parameters for the execution of the command (authentication
 aside):
- --offer-id
- --publisher-id
- --notification-emails

Note that 'notification-emails' parameter will be ignored for migrated offers
 and the notifications will be sent to the email address set as Seller
 contact info section of your Account settings in Partner Center.

Example:

```shell
$ azure-img-utils cloud-partner-offer publish \
        --offer-id myOfferId \
        --publisher-id myPublisherId \
        --notification-emails "myMail1@mydomain.com,myMail2@mydomain.com"
```

This command will output the URI for the published cloud partner offer
 operation if successful.

For more information about the cloud partner offer publish command see the
 help message:

```shell
$ azure-img-utils cloud-partner-offer publish --help

### go-live subcommand

This subcommand allows the user to set a cloud partner offer as go-live.

The subcommand is *azure-img-utils cloud-partner-offer go-live*.

The *required* parameters for the execution of the command (authentication
 aside):
- --offer-id
- --publisher-id

The result of the subcommand is that all new changes made to the offer are
 publicly visible.

Example:

```shell
$ azure-img-utils cloud-partner-offer go-live \
        --offer-id myOfferId \
        --publisher-id myPublisherId
```

This command will output the URI for the cloud partner offer go-live operation
if successful.

For more information about the cloud partner offer go-live command see the
 help message:

```shell
$ azure-img-utils cloud-partner-offer go-live --help
```

### upload-offer-document subcommand

This subcommand allows the user to upload an offer document to a cloud
 partner offer.

The subcommand is *azure-img-utils cloud-partner-offer upload-offer-document*.

The *required* parameters for the execution of the command (authentication
 aside):
- --offer-id
- --publisher-id
- --offer-document-file

The '--offer-document-file' parameter has to contain the path for a text file
containing the json document for the offer.

Example:

```shell
$ azure-img-utils cloud-partner-offer upload-offer-document \
        --offer-id myOfferId \
        --publisher-id myPublisherId \
        --offer-document-file /path/to/my/documentfile.json
```

This command will output only if there's any problem uploading the document for
the offer.

For more information about the cloud partner offer upload-offer-document
command see the help message:

```shell
$ azure-img-utils cloud-partner-offer upload-offer-document --help
```

### add-image-to-offer subcommand

This subcommand allows the user to add an image to a cloud partner offer.

The subcommand is *azure-img-utils cloud-partner-offer add-image-to-offer*.

The *required* parameters for the execution of the command (authentication
 aside):
- --blob-name
- --image-name
- --image-description
- --offer-id
- --publisher-id
- --label
- --sku

Some *optional* parameters for the execution of the command include:
- --blob-url  (A blob-url is generated if not provided)
- --generation-id
- --generation-suffix
- --vm-images-key

Example:

```shell
$ azure-img-utils cloud-partner-offer add-image-to-offer \
        --blob-name myBlobName \
        --image-name myImageName \
        --image-description "My image description" \
        --offer-id myOfferId \
        --publisher-id myPublisherId \
        --label myLabel \
        --sku mySKU
```

This command will output only if there's any problem adding the image
 to the offer.

For more information about the cloud partner offer add-image-to-offer
command see the help message:

```shell
$ azure-img-utils cloud-partner-offer add-image-to-offer --help
```

### remove-image-from-offer subcommand

This subcommand allows the user to remove an image from a cloud partner offer.

The subcommand is *azure-img-utils cloud-partner-offer remove-image-from-offer*.

The *required* parameters for the execution of the command (authentication
 aside):
- --image-urn

Some *optional* parameters for the execution of the command include:
- --vm-images-key

Example:

```shell
$ azure-img-utils cloud-partner-offer remove-image-to-offer \
        --image-urn myImageUrn
```

This command will output only if there's any problem removing the image
 from the offer.

For more information about the cloud partner offer remove-image-from-offer
command see the help message:

```shell
$ azure-img-utils cloud-partner-offer remove-image-from-offer --help
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
