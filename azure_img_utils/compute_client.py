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
import time

from azure_img_utils.auth import acquire_access_token
from azure_img_utils.exceptions import (
    AzureImgUtilsException,
    ResourceNotFoundException
)


class AzureComputeClient(object):
    def __init__(
        self,
        credentials: dict,
        resource_group: str,
        api_version: str = '2022-08-01'
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
            f'providers/Microsoft.Compute/{query}'
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

    def delete_image(self, image_name: str, wait=True):
        query = f'images/{image_name}'
        url = self.generate_url(query)
        self.process_request(url, action='delete')

        if wait:
            timeout = 60
            while timeout:
                if not self.image_exists(image_name):
                    return
                else:
                    timeout -= 1
                    time.sleep(1)

            raise AzureImgUtilsException(
                '{image_name} was not deleted'
            )

    def get_image(self, image_name: str):
        query = f'images/{image_name}'
        url = self.generate_url(query)
        return self.process_request(url)

    def image_exists(self, image_name: str):
        try:
            self.get_image(image_name)
        except ResourceNotFoundException:
            return False

        return True

    def create_compute_image(
        self,
        image_name: str,
        blob_name: str,
        container: str,
        region: str,
        storage_account: str,
        force_replace_image: bool = False,
        hyper_v_generation: str = 'V1',
        wait=True
    ):
        exists = self.image_exists(image_name)

        if exists and force_replace_image:
            self.delete_image(image_name)

        elif exists and not force_replace_image:
            raise AzureImgUtilsException(
                'Image already exists. To force deletion and re-create '
                'the image use "force_replace_image=True".'
            )

        query = f'images/{image_name}'
        url = self.generate_url(query)

        data = {
            'location': region,
            'properties': {
                'hyperVGeneration': hyper_v_generation,
                'storageProfile': {
                    'osDisk': {
                        'osType': 'Linux',
                        'osState': 'Generalized',
                        'caching': 'ReadWrite',
                        'blobUri': 'https://{0}.{1}/{2}/{3}'.format(
                            storage_account,
                            'blob.core.windows.net',
                            container,
                            blob_name
                        )
                    }
                }
            }
        }

        image = self.process_request(url, action='put', data=data)

        if wait:
            timeout = 60
            while timeout:
                image = self.get_image(image_name)
                state = image['properties']['provisioningState']

                if state == 'Succeeded':
                    return image
                elif state in ('Failed', 'Canceled'):
                    break
                else:
                    timeout -= 1
                    time.sleep(1)

            raise AzureImgUtilsException(
                'Image creation failed'
            )

    def get_gallery_image_version(
        self,
        gallery_name: str,
        gallery_image_name: str,
        gallery_image_version: str,
        resource_group: str
    ):
        query = (
            f'galleries/{gallery_name}/'
            f'images/{gallery_image_name}/'
            f'versions/{gallery_image_version}'
        )
        url = self.generate_url(
            query,
            resource_group=resource_group,
            api_version='2022-03-03'
        )
        return self.process_request(url)

    def gallery_image_version_exists(
        self,
        gallery_name: str,
        gallery_image_name: str,
        gallery_image_version: str,
        resource_group: str
    ):
        try:
            self.get_gallery_image_version(
                gallery_name,
                gallery_image_name,
                gallery_image_version,
                resource_group
            )
        except ResourceNotFoundException:
            return False

        return True

    def delete_gallery_image_version(
        self,
        gallery_name: str,
        gallery_image_name: str,
        gallery_image_version: str,
        resource_group: str,
        wait=True
    ):
        query = (
            f'galleries/{gallery_name}/'
            f'images/{gallery_image_name}/'
            f'versions/{gallery_image_version}'
        )
        url = self.generate_url(
            query,
            resource_group=resource_group,
            api_version='2022-03-03'
        )
        self.process_request(url, action='delete')

        if wait:
            timeout = 60
            while timeout:
                exists = self.gallery_image_exists(
                    gallery_name,
                    gallery_image_name,
                    gallery_image_version,
                    resource_group
                )

                if not exists:
                    return
                else:
                    timeout -= 1
                    time.sleep(1)

            raise AzureImgUtilsException(
                '{query} was not deleted'
            )

    def create_gallery_image_version(
        self,
        gallery_name: str,
        gallery_image_name: str,
        gallery_image_version: str,
        gallery_resource_group: str,
        blob_name: str,
        region: str,
        blob_resource_group: str,
        storage_account: str,
        container: str,
        wait=True
    ):
        query = (
            f'galleries/{gallery_name}/'
            f'images/{gallery_image_name}/'
            f'versions/{gallery_image_version}'
        )
        url = self.generate_url(
            query,
            resource_group=gallery_resource_group,
            api_version='2022-03-03'
        )
        data = {
            'location': region,
            'properties': {
                'publishingProfile': {
                    'targetRegions': [
                        {
                            'name': region
                        }
                    ]
                },
                'storageProfile': {
                    'osDiskImage': {
                        'source': {
                            'id': f'/subscriptions/{self.subscription_id}/'
                                  f'resourceGroups/{blob_resource_group}/'
                                  'providers/Microsoft.Storage/'
                                  f'storageAccounts/{storage_account}',
                            'uri': f'https://{storage_account}.blob.core.'
                                   f'windows.net/{container}/{blob_name}'
                        },
                        'hostCaching': 'ReadWrite'
                    }
                }
            }
        }

        self.process_request(url, action='put', data=data)

        if wait:
            timeout = 1200
            while timeout:
                image = self.get_gallery_image_version(
                    gallery_name,
                    gallery_image_name,
                    gallery_image_version,
                    gallery_resource_group
                )

                state = image['properties']['provisioningState']

                if state == 'Succeeded':
                    return image
                elif state in ('Failed', 'Canceled'):
                    break
                else:
                    timeout -= 1
                    time.sleep(1)

            raise AzureImgUtilsException(
                '{query} was not created'
            )

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
