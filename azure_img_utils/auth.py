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

import msal

from datetime import datetime, timedelta

from azure.identity import ClientSecretCredential
from azure.storage.blob import (
    generate_container_sas,
    ContainerSasPermissions
)
from azure_img_utils.exceptions import AzureImgUtilsException


def acquire_access_token(credentials: dict, cloud_partner: bool = False):
    """
    Get an access token from msal library.

    credentials:
      A service account json dictionary.
    """
    client = msal.ConfidentialClientApplication(
        client_id=credentials.get('clientId'),
        client_credential=credentials.get('clientSecret'),
        authority='/'.join([
            credentials.get('activeDirectoryEndpointUrl'),
            credentials.get('tenantId')
        ])
    )

    if cloud_partner:
        resource = 'https://cloudpartner.azure.com/.default'
    else:
        resource = credentials['managementEndpointUrl'] + '.default'

    response = client.acquire_token_for_client(
        resource
    )

    if 'error' in response:
        raise AzureImgUtilsException(
            f'Unable to authenticate against {resource}: '
            f'{response.get("error")}'
        )

    return response.get('access_token')


def create_sas_token(
    blob_service,
    storage_account: str,
    container: str,
    permissions=ContainerSasPermissions(read=True, list=True),
    expire_hours: int = 1,
    start_hours: int = 1
):
    """
    Create a sas token for the given container.

    By default make the token valid 1 hour in the past and
    1 hour in the future with read and list permissions.
    """
    expiry_time = datetime.utcnow() + timedelta(hours=expire_hours)
    start_time = datetime.utcnow() - timedelta(hours=start_hours)

    return generate_container_sas(
        storage_account,
        container,
        permission=permissions,
        expiry=expiry_time,
        start=start_time,
        account_key=blob_service.credential.account_key
    )


def get_client_from_json(client, credentials: dict):
    """Return an authenticated client with the provided credentials."""
    credential = get_secret_credential(credentials)
    return client(
        credential,
        credentials['subscriptionId']
    )


def get_secret_credential(credentials: dict):
    """Create credentials object from credentials dictionary."""
    return ClientSecretCredential(
        tenant_id=credentials['tenantId'],
        client_id=credentials['clientId'],
        client_secret=credentials['clientSecret']
    )
