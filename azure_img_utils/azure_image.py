# -*- coding: utf-8 -*-

"""Azure image class module."""

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

import json
import logging
import os

from azure.core.exceptions import ResourceNotFoundError

from azure_img_utils.exceptions import AzureImgUtilsException
from azure_img_utils.storage import (
    get_blob_service,
    blob_exists,
    delete_blob,
    upload_azure_file
)


class AzureImage(object):
    """
    Provides methods for handling compute images in Azure.
    """

    def __init__(
        self,
        container: str,
        storage_account: str,
        credentials: dict = None,
        credentials_file: str = None,
        resource_group: str = None,
        sas_token: str = None,
        log_level=logging.INFO,
        log_callback=None,
        timeout: int = 180
    ):
        """Initialize class and setup logging."""
        self.container = container
        self.timeout = timeout
        self._blob_service_client = None
        self._credentials = credentials
        self._credentials_file = credentials_file
        self._resource_group = resource_group
        self._storage_account = storage_account
        self._sas_token = sas_token

        if log_callback:
            self.log = log_callback
        else:
            self.log = logging.getLogger('azure-img-utils')
            self.log.setLevel(log_level)

        try:
            self.log_level = self.log.level
        except AttributeError:
            self.log_level = self.log.logger.level  # LoggerAdapter

    def image_blob_exists(self, blob_name: str):
        """Return True if image blob exists in the configured container."""
        return blob_exists(
            self.blob_service_client,
            blob_name,
            self.container
        )

    def delete_storage_blob(self, blob_name: str):
        """Delete blob if it exists in the configured container."""
        try:
            delete_blob(
                self.blob_service_client,
                blob_name,
                self.container
            )
        except ResourceNotFoundError:
            self.log.debug(
                f'Blob {blob_name} not found. '
                f'Nothing has been deleted.'
            )
            return False

        return True

    def upload_image_blob(
        self,
        image_file: str,
        max_workers: int = None,
        max_retry_attempts: int = None,
        blob_name: str = None,
        force_replace_image: bool = False,
        is_page_blob: bool = True,
        expand_image: bool = True
    ):
        """
        Upload image tarball to the configured container.

        Generate blob name based on image file path if a
        name is not provided.
        """
        if not blob_name:
            blob_name = image_file.rsplit(os.sep, maxsplit=1)[-1]

        if self.image_blob_exists(blob_name) and not force_replace_image:
            raise Exception(
                f'Image {blob_name} already exists. To replace an existing '
                f'image use force_replace_image option.'
            )
        elif self.image_blob_exists(blob_name) and force_replace_image:
            self.delete_storage_blob(blob_name)

        kwargs = {
            'is_page_blob': is_page_blob,
            'expand_image': expand_image
        }

        if max_workers:
            kwargs['max_workers'] = max_workers

        if max_retry_attempts:
            kwargs['max_retry_attempts'] = max_retry_attempts

        try:
            upload_azure_file(
                blob_name,
                self.container,
                image_file,
                self.blob_service_client,
                **kwargs
            )
        except FileNotFoundError:
            raise AzureImgUtilsException(
                f'Image file {image_file} not found. Ensure the path to'
                f' the file is correct.'
            )
        except Exception as error:
            raise AzureImgUtilsException(
                f'Unable to upload image: {str(error)}'
            )

        return blob_name

    @property
    def blob_service_client(self):
        """
        Blob service client property

        Lazy blob service client initialization.
        """
        if not self._blob_service_client:
            if self.sas_token:
                args = (
                    self.sas_token,
                    self.storage_account
                )
            elif self.credentials and self.resource_group:
                args = (
                    self.credentials,
                    self.resource_group,
                    self.storage_account
                )
            else:
                raise Exception(
                    'Either an sas_token or credentials_file/credentials and '
                    'resource_group is required for storage blob functions.'
                )
            
            self._blob_service_client = get_blob_service(*args)

        return self._blob_service_client
    
    @property
    def credentials(self):
        """
        Lazy credentials attribute

        If credentials not set and a file is available attempt
        to load credentials json as dictionary.
        """
        if not self._credentials and self._credentials_file:
            creds_file = os.path.expanduser(self._credentials_file)
            
            with open(creds_file, 'r') as json_file:
                self._credentials = json.load(json_file)

        return self._credentials
    
    @credentials.setter
    def credentials(self, creds):
        """
        Invalidates the blob service client.
        """
        self._credentials = creds
        self._blob_service_client = None

    @property
    def credentials_file(self):
        return self._credentials_file

    @credentials_file.setter
    def credentials_file(self, creds_file):
        """
        Invalidates the credentials.
        """
        self._credentials_file = creds_file
        self.credentials = None
    
    @property
    def sas_token(self):
        return self._sas_token

    @sas_token.setter
    def sas_token(self, token):
        """
        Invalidates the blob service client.
        """
        self._sas_token = token
        self._blob_service_client = None

    @property
    def resource_group(self):
        return self._resource_group

    @resource_group.setter
    def resource_group(self, group):
        """
        Invalidates the blob service client.
        """
        self._resource_group = group
        self._blob_service_client = None
    
    @property
    def storage_account(self):
        return self._storage_account

    @storage_account.setter
    def storage_account(self, account):
        """
        Invalidates the blob service client.
        """
        self._storage_account = account
        self._blob_service_client = None
