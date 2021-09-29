# Copyright (c) 2021 SUSE LLC
#
# This file is part of azure_img_utils. azure_img_utils provides an
# api and command line utilities for handling images in the Azure Cloud.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import lzma

from functools import singledispatch

from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import (
    BlobServiceClient,
    ContainerSasPermissions
)

from azure_img_utils.auth import create_sas_token, get_client_from_json
from azure_img_utils.exceptions import AzureImgUtilsStorageException
from azure_img_utils.filetype import FileType


def delete_blob(
    blob_service_client,
    blob: str,
    container: str
):
    """
    Delete page blob in container.
    """
    blob_client = get_blob_client(blob_service_client, blob, container)
    blob_client.delete_blob()


def blob_exists(
    blob_service_client,
    blob: str,
    container: str
):
    """
    Return True if blob exists in container.
    """
    blob_client = get_blob_client(blob_service_client, blob, container)
    return blob_client.exists()


def get_blob_url(
    blob_service_client,
    blob_name: str,
    storage_account: str,
    container: str,
    permissions=ContainerSasPermissions(read=True, list=True),
    expire_hours: int = 1,
    start_hours: int = 1
):
    """
    Create a URL for the given blob with a shared access signature.

    The signature will expire based on expire_hours.
    """
    sas_token = create_sas_token(
        blob_service_client,
        storage_account,
        container,
        permissions=permissions,
        expire_hours=expire_hours,
        start_hours=start_hours
    )

    source_blob_url = (
        'https://{account}.blob.core.windows.net/'
        '{container}/{blob}?{token}'.format(
            account=storage_account,
            container=container,
            blob=blob_name,
            token=sas_token
        )
    )

    return source_blob_url


def get_storage_account_key(
    credentials: dict,
    resource_group: str,
    storage_account: str
):
    """Return the first storage account key for the provided account."""
    storage_client = get_client_from_json(
        StorageManagementClient,
        credentials
    )
    storage_key_list = storage_client.storage_accounts.list_keys(
        resource_group,
        storage_account
    )
    return storage_key_list.keys[0].value


def get_blob_client(blob_service_client, blob_name: str, container: str):
    """Return blob client based on container and blob name."""
    container_client = blob_service_client.get_container_client(container)
    return container_client.get_blob_client(blob_name)


@singledispatch
def get_blob_service(
    credentials: dict,
    resource_group: str,
    storage_account: str
):
    """
    Return authenticated blob service instance for the storage account.

    Using storage account keys.
    """
    account_key = get_storage_account_key(
        credentials,
        resource_group,
        storage_account
    )

    return BlobServiceClient(
        account_url='https://{account_name}.blob.core.windows.net'.format(
            account_name=storage_account
        ),
        credential=account_key
    )


@get_blob_service.register(str)
def _(sas_token: str, storage_account: str):
    """
    Return authenticated page blob service instance for the storage account.

    Using an sas token.
    """
    return BlobServiceClient(
        account_url='https://{account_name}.blob.core.windows.net'.format(
            account_name=storage_account
        ),
        credential=sas_token
    )


def upload_azure_file(
    blob_name: str,
    container: str,
    file_name: str,
    blob_service_client,
    max_retry_attempts: int = 5,
    max_workers: int = 5,
    is_page_blob: bool = False,
    expand_image: bool = True
):
    """
    Upload file to Azure storage container.

    Authentication can be an sas token or with storage account
    keys.

    Blob can be block or page and if the blob is an image tarball
    it can be expanded during upload.
    """
    blob_client = get_blob_client(blob_service_client, blob_name, container)

    if is_page_blob:
        blob_type = 'PageBlob'
    else:
        blob_type = 'BlockBlob'

    system_image_file_type = FileType(file_name)
    if system_image_file_type.is_xz() and expand_image:
        open_image = lzma.LZMAFile
    else:
        open_image = open

    msg = ''
    while max_retry_attempts > 0:
        with open_image(file_name, 'rb') as image_stream:
            try:
                blob_client.upload_blob(
                    image_stream,
                    blob_type=blob_type,
                    length=system_image_file_type.get_size(),
                    max_concurrency=max_workers
                )
                return
            except Exception as error:
                msg = error
                max_retry_attempts -= 1

    raise AzureImgUtilsStorageException(
        'Unable to upload {0}: {1}'.format(
            file_name,
            msg
        )
    )
