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
from azure.mgmt.compute import ComputeManagementClient

from azure_img_utils.auth import get_client_from_json, acquire_access_token
from azure_img_utils.exceptions import AzureImgUtilsException
from azure_img_utils.storage import (
    get_blob_service,
    get_blob_url,
    blob_exists,
    delete_blob,
    upload_azure_file
)
from azure_img_utils.compute import (
    create_image,
    delete_image,
    get_image,
    image_exists
)
from azure_img_utils.cloud_partner import (
    get_cloud_partner_offer_status,
    get_cloud_partner_operation,
    request_cloud_partner_offer_doc,
    add_image_version_to_offer,
    put_cloud_partner_offer_doc,
    publish_cloud_partner_offer,
    go_live_with_cloud_partner_offer,
    remove_image_version_from_offer
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
        self._compute_client = None
        self._access_token = None
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

        return blob_name

    def image_exists(self, image_name: str) -> bool:
        """Return True if image exists, false otherwise."""
        return image_exists(self.compute_client, image_name)

    def delete_compute_image(self, image_name: str):
        """
        Delete compute image.
        """
        if not self.resource_group:
            raise AzureImgUtilsException(
                'Resource group is required to delete a compute image'
            )

        delete_image(
            self.compute_client,
            self.resource_group,
            image_name
        )

    def get_compute_image(self, image_name: str) -> dict:
        """
        Return compute image by name.

        If image is not found None is returned.
        """
        return get_image(self.compute_client, image_name)

    def create_compute_image(
        self,
        blob_name: str,
        image_name: str,
        region: str,
        force_replace_image: bool = False,
        hyper_v_generation: str = 'V1'
    ) -> str:
        """
        Create compute image from storage blob.

        If image exists and force replace is True delete
        the existing image before creation.
        """
        if not self.resource_group:
            raise AzureImgUtilsException(
                'Resource group is required to create a compute image'
            )

        exists = image_exists(self.compute_client, image_name)

        if exists and force_replace_image:
            delete_image(
                self.compute_client,
                self.resource_group,
                image_name
            )
        elif exists and not force_replace_image:
            raise AzureImgUtilsException(
                'Image already exists. To force deletion and re-create '
                'the image use "force_replace_image=True".'
            )

        return create_image(
            blob_name,
            image_name,
            self.compute_client,
            self.container,
            self.resource_group,
            self.storage_account,
            region,
            hyper_v_generation
        )

    def get_offer_doc(
        self,
        offer_id: str,
        publisher_id: str
    ) -> dict:
        """
        Return the offer doc dictionary for the given offer.
        """
        return request_cloud_partner_offer_doc(
            self.access_token,
            offer_id,
            publisher_id
        )

    def upload_offer_doc(
        self,
        offer_id: str,
        publisher_id: str,
        offer_doc: dict
    ):
        """
        Upload the offer doc for the given offer.

        offer_doc is a dictionary defining the offer details.
        """
        put_cloud_partner_offer_doc(
            self.access_token,
            offer_doc,
            offer_id,
            publisher_id
        )

    def add_image_to_offer(
        self,
        blob_name: str,
        image_name: str,
        image_description: str,
        offer_id: str,
        publisher_id: str,
        label: str,
        sku: str,
        blob_url: str = None,
        generation_id: str = None,
        generation_suffix: str = None,
        vm_images_key: str = None
    ):
        """
        Add a new image version to the given offer.

        The offer is pulled from the partner center, updated with the
        new image version and re-uploaded. To make the new image available
        the offer must be published and set to go-live.

        A blob_url is generated for the container if one is not provided.
        """
        if not blob_url:
            blob_url = get_blob_url(
                self.blob_service_client,
                blob_name,
                self.storage_account,
                self.container,
                expire_hours=24 * 92,
                start_hours=24
            )

        offer_doc = self.get_offer_doc(offer_id, publisher_id)

        kwargs = {
            'generation_id': generation_id,
            'cloud_image_name_generation_suffix': generation_suffix
        }

        if vm_images_key:
            kwargs['vm_images_key'] = vm_images_key

        offer_doc = add_image_version_to_offer(
            offer_doc,
            blob_url,
            image_description,
            image_name,
            label,
            sku,
            **kwargs
        )
        self.upload_offer_doc(
            offer_id,
            publisher_id,
            offer_doc
        )

    def remove_image_from_offer(
        self,
        image_version: str,
        offer_id: str,
        publisher_id: str,
        sku: str,
        generation_id: str = None,
        vm_images_key: str = None
    ):
        """
        Delete the given image version from the offer.

        The offer is pulled from the partner center, the old image version
        is deleted and re-uploaded. To make the new image available
        the offer must be published and set to go-live.
        """
        offer_doc = self.get_offer_doc(offer_id, publisher_id)

        kwargs = {
            'generation_id': generation_id
        }

        if vm_images_key:
            kwargs['vm_images_key'] = vm_images_key

        offer_doc = remove_image_version_from_offer(
            offer_doc,
            image_version,
            sku,
            **kwargs
        )
        self.upload_offer_doc(
            offer_id,
            publisher_id,
            offer_doc
        )

    def publish_offer(
        self,
        offer_id: str,
        publisher_id: str,
        notification_emails: str
    ) -> str:
        """
        Publish the given offer.

        notification_emails is required to be a comma separated list
        of emails. This argument is required. However, for migrated
        offers the emails are ignored. For migrated offers
        notifications will be sent to the email address set in the
        Seller contact info section of your Account settings in
        Partner Center.

        Returns the operation uri.
        """
        return publish_cloud_partner_offer(
            self.access_token,
            offer_id,
            publisher_id,
            notification_emails
        )

    def go_live_with_offer(
        self,
        offer_id: str,
        publisher_id: str
    ) -> str:
        """
        Set the offer as go-live.

        This makes all new changes to the offer publicly visible.

        Returns the operation uri.
        """
        return go_live_with_cloud_partner_offer(
            self.access_token,
            offer_id,
            publisher_id
        )

    def get_offer_status(self, offer_id, publisher_id) -> str:
        """
        Returns the status of the offer.
        """
        return get_cloud_partner_offer_status(
            self.access_token,
            offer_id,
            publisher_id
        )

    def get_operation(self, operation: str) -> dict:
        """
        Returns a dictionary status for the given operation.
        """
        return get_cloud_partner_operation(self.access_token, operation)

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
                    'resource_group is required to authenticate any '
                    'operations.'
                )

            self._blob_service_client = get_blob_service(*args)

        return self._blob_service_client

    @property
    def compute_client(self):
        """
        Lazy compute client attribute

        If compute client is not set create a new client from credentials.
        """
        if not self._compute_client:
            self._compute_client = get_client_from_json(
                ComputeManagementClient,
                self.credentials
            )

        return self._compute_client

    @property
    def access_token(self):
        if not self._access_token:
            self._access_token = acquire_access_token(
                self.credentials,
                cloud_partner=True
            )

        return self._access_token

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
        Invalidates the blob service and compute clients.
        """
        self._credentials = creds
        self._blob_service_client = None
        self._compute_client = None

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
