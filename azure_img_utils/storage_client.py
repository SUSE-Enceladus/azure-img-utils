# Copyright (c) 2022 SUSE LLC
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

import json
import requests

from azure_img_utils.auth import acquire_access_token
from azure_img_utils.exceptions import (
    AzureImgUtilsException,
    ResourceNotFoundException
)


class AzureStorageClient(object):
    def __init__(
        self,
        credentials: dict,
        resource_group: str,
        api_version: str = '2022-05-01'
    ):
        self.client_id = None
        self.client_secret = None
        self.subscription_id = None
        self.target_endpoint = None
        self._access_token = None

        self.credentials = credentials
        self.resource_group = resource_group
        self.api_version = api_version
        self.resource_endpoint = 'management.azure.com'

    def generate_url(
        self,
        query: str,
        resource_group: str = None,
        api_version: str = None
    ):
        resource_group = resource_group or self.resource_group
        api_version = api_version or self.api_version

        full_url = (
            f'https://{self.resource_endpoint}/'
            f'subscriptions/{self.subscription_id}/'
            f'resourceGroups/{resource_group}/'
            f'providers/Microsoft.Storage/{query}'
            f'?api-version={api_version}'
        )

        return full_url

    def process_request(
        self,
        url: str,
        action: str = 'get',
        data: dict = None
    ):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Host': self.resource_endpoint
        }

        if data:
            data = json.dumps(data)

        method = getattr(requests, action)

        try:
            response = method(url, headers=headers, data=data)
        except requests.ConnectionError:
            raise AzureImgUtilsException(
                f'Failed to establish connection with Azure at: {url}'
            )

        if response.status_code == 202:
            return
        if response.status_code == 404:
            raise ResourceNotFoundException(
                f'Resource not found for {url}'
            )

        try:
            result = response.json()
        except json.decoder.JSONDecodeError:
            raise AzureImgUtilsException(
                f'The requested URL was not found: {url}'
            )

        if 'error' in result:
            raise AzureImgUtilsException(
                f'{result["error"]["message"]}'
            )

        return result

    def get_storage_account_keys(self, storage_account: str):
        query = f'storageAccounts/{storage_account}/listKeys'
        url = self.generate_url(query)
        return self.process_request(url, action='post').get('keys', [])

    def get_storage_accounts(self):
        query = 'storageAccounts/'
        url = self.generate_url(query)
        return self.process_request(url).get('value', [])

    @property
    def credentials(self):
        return self._credentials

    @credentials.setter
    def credentials(self, creds: dict):
        """
        Invalidates the access_token.
        """
        self._credentials = creds
        self.client_id = creds['clientId']
        self.client_secret = creds['clientSecret']
        self.subscription_id = creds['subscriptionId']
        self._access_token = None

    @property
    def access_token(self):
        if not self._access_token:
            self._access_token = acquire_access_token(
                self.credentials
            )

        return self._access_token
