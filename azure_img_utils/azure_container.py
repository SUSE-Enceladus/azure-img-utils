# -*- coding: utf-8 -*-

"""Azure container class module."""

# Copyright (c) 2025 SUSE LLC
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

from azure.containerregistry import ContainerRegistryClient

from azure_img_utils.auth import get_client_from_json, acquire_access_token
from azure_img_utils.exceptions import (
    AzureCloudPartnerException,
    AzureImgUtilsException
)

from azure_img_utils import cloud_partner


class AzureContainer(object):
    """
    Provides methods for handling Azure container based products in Azure.
    """

    def __init__(
        self,
        credentials: dict = None,
        credentials_file: str = None,
        log_level=logging.INFO,
        log_callback=None,
        timeout: int = 180
    ):
        """Initialize class and setup logging."""
        self.timeout = timeout
        self._credentials = credentials
        self._credentials_file = credentials_file
        self._access_token = None
        self._acr_client = None

        if log_callback:
            self.log = log_callback
        else:
            self.log = logging.getLogger('azure-img-utils')
            self.log.setLevel(log_level)

        try:
            self.log_level = self.log.level
        except AttributeError:
            self.log_level = self.log.logger.level  # LoggerAdapter

    def offer_exists(
        self,
        offer_id: str
    ) -> dict:
        """
        Return boolean result if offer exists for publisher.
        """
        try:
            self.get_offer_doc(offer_id, retries=0)
        except AzureCloudPartnerException:
            return False
        else:
            return True

    def get_offer_doc(
        self,
        offer_id: str,
        target_type: str = 'draft',
        retries: int = 5
    ) -> dict:
        """
        Return the offer doc dictionary for the given offer.
        """
        return cloud_partner.get_offer_doc(
            self.access_token,
            offer_id,
            target_type,
            retries
        )

    @property
    def credentials(self):
        """
        Lazy credentials attribute

        If credentials not set and a file is available attempt
        to load credentials json as dictionary.
        """
        if not self._credentials and not self._credentials_file:
            raise AzureImgUtilsException(
                'No credentials dictionary or credentials file provided. '
                'Unable to authenticate with Azure.'
            )

        if not self._credentials:
            creds_file = os.path.expanduser(self._credentials_file)

            with open(creds_file, 'r') as json_file:
                self._credentials = json.load(json_file)

        return self._credentials

    @credentials.setter
    def credentials(self, creds):
        """
        Invalidates the blob service and compute clients.
        """
        self._credentials = creds
        self._acr_client = None

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
    def access_token(self):
        if not self._access_token:
            self._access_token = acquire_access_token(
                self.credentials,
                cloud_partner=True
            )

        return self._access_token

    def get_operation(self, operation: str) -> dict:
        """
        Returns a dictionary status for the given operation.
        """
        return cloud_partner.get_operation(self.access_token, operation)

    def update_resource_in_offer(self, resource_doc: dict):
        """
        Updates the offer using the provided resource doc.

        resource_doc is a dictionary defining the resource details.
        """
        job_id = cloud_partner.submit_request(
            self.access_token, [resource_doc]
        )
        return job_id

    def upload_offer_doc(self, offer_doc: dict):
        """
        Upload the offer doc to partner center.

        offer_doc is a dictionary defining the offer details.
        """
        job_id = cloud_partner.submit_request(
            self.access_token, offer_doc['resources']
        )
        return job_id

    @property
    def acr_client(self):
        """
        Lazy Azure container registry client attribute

        If acr client is not set create a new client from credentials.
        """
        if not self._acr_client:
            self._acr_client = get_client_from_json(
                ContainerRegistryClient,
                self.credentials
            )

        return self._acr_client

    def add_cnab_version_to_offer(
        self,
        registry_name: str,
        repository_name: str,
        tag: str,
        offer_id: str,
        sku: str,
        acr_client: ContainerRegistryClient
    ):
        """
        Adds a new cnab version to the given offer.

        The offer is pulled from the partner center, updated with the
        new cnab version and re-uploaded. To make the new cnab available
        the offer must be published and set to go-live.
        """
        offer_doc = self.get_offer_doc(offer_id)
        plan_details = cloud_partner.get_technical_details(
            offer_doc,
            sku,
            container_offer=True
        )

        updated_plan_details = cloud_partner.add_cnab_version_to_offer(
            plan_details,
            tag,
            registry_name=registry_name,
            repository_name=repository_name,
            acr_client=self.acr_client
        )
        self.update_resource_in_offer(
            updated_plan_details
        )
