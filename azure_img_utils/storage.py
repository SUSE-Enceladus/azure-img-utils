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

from functools import singledispatch

from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import (
    BlobServiceClient,
    ContainerSasPermissions
)

from azure_img_utils.auth import create_sas_token, get_client_from_json
from azure_img_utils.exceptions import AzureImgUtilsStorageException


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
    try:
        container_client = blob_service_client.get_container_client(container)
        blob_client = container_client.get_blob_client(blob_name)
    except ValueError as error:
        raise AzureImgUtilsStorageException(error) from error

    return blob_client


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
