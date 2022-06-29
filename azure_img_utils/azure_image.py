# -*- coding: utf-8 -*-

"""Azure image class module."""

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

import jmespath
import json
import logging
import lzma
import os

from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.compute import ComputeManagementClient

from azure_img_utils.auth import get_client_from_json, acquire_access_token

from azure_img_utils.exceptions import (
    AzureImgUtilsException,
    AzureImgUtilsStorageException,
)

from azure_img_utils.filetype import FileType

from azure_img_utils.storage import (
    get_blob_client,
    get_blob_service,
    get_blob_url,
)

from azure_img_utils.compute import (
    create_gallery_image_definition_version,
    get_image,
    remove_gallery_image_version,
    retrieve_gallery_image_version
)

from azure_img_utils.cloud_partner import (
    add_image_version_to_offer,
    get_cloud_partner_api_headers,
    get_cloud_partner_endpoint,
    process_request,
    remove_image_version_from_offer
)


class AzureImage(object):
    """
    Provides methods for handling compute images in Azure.
    """

    def __init__(
        self,
        container: str = None,
        storage_account: str = None,
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
        blob_client = get_blob_client(
            self.blob_service_client,
            blob_name,
            self.container
        )
        return blob_client.exists()

    def delete_storage_blob(self, blob_name: str):
        """Delete blob if it exists in the configured container."""
        try:
            blob_client = get_blob_client(
                self.blob_service_client,
                blob_name,
                self.container
            )
            blob_client.delete_blob()

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
        max_workers: int = 5,
        max_attempts: int = 5,
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

        if max_attempts <= 0:
            raise Exception(
                f'max_attempts parameter value has to be >0, '
                f'{max_attempts} provided.'
            )

        try:
            blob_client = get_blob_client(
                self.blob_service_client,
                blob_name,
                self.container
            )

            if is_page_blob:
                blob_type = 'PageBlob'
            else:
                blob_type = 'BlockBlob'

            system_image_file_type = FileType(image_file)
            if system_image_file_type.is_xz() and expand_image:
                open_image = lzma.LZMAFile
            else:
                open_image = open

            msg = ''
            while max_attempts > 0:
                with open_image(image_file, 'rb') as image_stream:
                    try:
                        blob_client.upload_blob(
                            image_stream,
                            blob_type=blob_type,
                            length=system_image_file_type.get_size(),
                            max_concurrency=max_workers
                        )
                        return blob_name

                    except Exception as error:
                        msg = error
                        max_attempts -= 1

            raise AzureImgUtilsStorageException(
                'Unable to upload {0}: {1}'.format(image_file, msg)
            )

        except FileNotFoundError:
            raise AzureImgUtilsException(
                f'Image file {image_file} not found. Ensure the path to'
                f' the file is correct.'
            )

    def image_exists(self, image_name: str) -> bool:
        """Return True if image exists, false otherwise."""
        images = self.compute_client.images.list()
        for image in images:
            if image.name == image_name:
                return True
        return False

    def gallery_image_version_exists(
        self,
        gallery_name: str,
        gallery_image_name: str,
        image_version: str,
        gallery_resource_group: str = None
    ) -> bool:
        """
        Return True if gallery image version exists, false otherwise.
        """
        gallery_image_version = self.get_gallery_image_version(
            gallery_name,
            gallery_image_name,
            image_version,
            gallery_resource_group
        )
        return gallery_image_version is not None

    def delete_compute_image(self, image_name: str):
        """
        Delete compute image.
        """
        if not self.resource_group:
            raise AzureImgUtilsException(
                'Resource group is required to delete a compute image'
            )

        async_delete_image = self.compute_client.images.begin_delete(
            self.resource_group,
            image_name
        )
        async_delete_image.result()

    def delete_gallery_image_version(
        self,
        gallery_name: str,
        gallery_image_name: str,
        image_version: str,
        gallery_resource_group: str = None
    ):
        """
        Delete gallery image version.
        """
        if not self.resource_group and not gallery_resource_group:
            raise AzureImgUtilsException(
                'Resource group is required to delete a gallery image'
            )

        if not gallery_resource_group:
            gallery_resource_group = self.resource_group

        remove_gallery_image_version(
            gallery_name,
            gallery_image_name,
            image_version,
            gallery_resource_group,
            self.compute_client
        )

    def get_compute_image(self, image_name: str) -> dict:
        """
        Return compute image by name.

        If image is not found None is returned.
        """
        return get_image(self.compute_client, image_name)

    def get_gallery_image_version(
        self,
        gallery_name: str,
        gallery_image_name: str,
        image_version: str,
        gallery_resource_group: str = None
    ) -> dict:
        """
        Return gallery image by gallery_image_name.

        If image is not found None is returned.
        """
        if not self.resource_group and not gallery_resource_group:
            raise AzureImgUtilsException(
                'Resource group is required to retrieve a gallery image'
            )

        if not gallery_resource_group:
            gallery_resource_group = self.resource_group

        return retrieve_gallery_image_version(
            gallery_name,
            gallery_image_name,
            image_version,
            gallery_resource_group,
            self.compute_client
        )

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

        hyper v generation of V2 is uefi and V1 is legacy bios.
        """
        if not self.container:
            raise AzureImgUtilsException(
                'Container is required to create a compute image'
            )

        if not self.resource_group:
            raise AzureImgUtilsException(
                'Resource group is required to create a compute image'
            )

        if not self.storage_account:
            raise AzureImgUtilsException(
                'Storage account is required to create a compute image'
            )

        exists = self.image_exists(image_name)

        if exists and force_replace_image:
            self.delete_compute_image(image_name)

        elif exists and not force_replace_image:
            raise AzureImgUtilsException(
                'Image already exists. To force deletion and re-create '
                'the image use "force_replace_image=True".'
            )

        async_create_image = self.compute_client.images.begin_create_or_update(
            self.resource_group,
            image_name,
            {
                'location': region,
                'hyper_v_generation': hyper_v_generation,
                'storage_profile': {
                    'os_disk': {
                        'os_type': 'Linux',
                        'os_state': 'Generalized',
                        'caching': 'ReadWrite',
                        'blob_uri': 'https://{0}.{1}/{2}/{3}'.format(
                            self.storage_account,
                            'blob.core.windows.net',
                            self.container,
                            blob_name
                        )
                    }
                }
            }
        )
        async_create_image.result()
        return image_name

    def create_gallery_image_version(
        self,
        blob_name: str,
        gallery_name: str,
        gallery_image_name: str,
        image_version: str,
        region: str,
        force_replace_image: bool = False,
        gallery_resource_group: str = None
    ) -> str:
        """
        Create gallery image version from storage blob.

        If gallery image version exists and force replace is True
        then delete the existing image before creation. Otherwise
        an error is raised.
        """
        if not self.container:
            raise AzureImgUtilsException(
                'Container is required to create a gallery image'
            )

        if not self.resource_group:
            raise AzureImgUtilsException(
                'Resource group is required to create a gallery image'
            )

        if not self.storage_account:
            raise AzureImgUtilsException(
                'Storage account is required to create a gallery image'
            )

        exists = self.gallery_image_version_exists(
            gallery_name,
            gallery_image_name,
            image_version,
            gallery_resource_group
        )

        if exists and force_replace_image:
            self.delete_gallery_image_version(
                gallery_name,
                gallery_image_name,
                image_version,
                gallery_resource_group
            )
        elif exists and not force_replace_image:
            raise AzureImgUtilsException(
                'Gallery image version already exists. To force deletion and '
                're-create the image set "force_replace_image" to True.'
            )

        return create_gallery_image_definition_version(
            blob_name,
            gallery_name,
            gallery_image_name,
            image_version,
            region,
            self.resource_group,
            self.storage_account,
            self.container,
            self.compute_client,
            gallery_resource_group
        )

    def get_offer_doc(
        self,
        offer_id: str,
        publisher_id: str
    ) -> dict:
        """
        Return the offer doc dictionary for the given offer.
        """
        endpoint = get_cloud_partner_endpoint(
            offer_id,
            publisher_id
        )

        headers = get_cloud_partner_api_headers(self.access_token)

        response = process_request(
            endpoint,
            headers,
            method='get'
        )
        return response

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
        endpoint = get_cloud_partner_endpoint(
            offer_id,
            publisher_id
        )
        headers = get_cloud_partner_api_headers(
            self.access_token,
            content_type='application/json',
            if_match='*'
        )

        process_request(
            endpoint,
            headers,
            data=offer_doc,
            method='put'
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
        if not self.container:
            raise AzureImgUtilsException(
                'Container is required to add an image to an offer'
            )

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
        image_urn: str,
        vm_images_key: str = None
    ):
        """
        Delete the given image version from the offer.

        The offer is pulled from the partner center, the old image version
        is deleted and re-uploaded. To make the new image available
        the offer must be published and set to go-live.
        """
        publisher_id, offer_id, plan_id, image_version = image_urn.split(':')
        offer_doc = self.get_offer_doc(offer_id, publisher_id)

        kwargs = {}
        if vm_images_key:
            kwargs['vm_images_key'] = vm_images_key

        offer_doc = remove_image_version_from_offer(
            offer_doc,
            image_version,
            plan_id,
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
        endpoint = get_cloud_partner_endpoint(
            offer_id,
            publisher_id,
            publish=True
        )

        headers = get_cloud_partner_api_headers(
            self.access_token,
            content_type='application/json'
        )

        response = process_request(
            endpoint,
            headers,
            data={'metadata': {'notification-emails': notification_emails}},
            method='post',
            json_response=False
        )

        return response.headers['Location']

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
        endpoint = get_cloud_partner_endpoint(
            offer_id,
            publisher_id,
            go_live=True
        )
        headers = get_cloud_partner_api_headers(
            self.access_token,
            content_type='application/json'
        )

        response = process_request(
            endpoint,
            headers,
            method='post',
            json_response=False
        )

        return response.headers['Location']

    def get_offer_status(self, offer_id, publisher_id) -> str:
        """
        Returns the status of the offer.
        """
        endpoint = get_cloud_partner_endpoint(
            offer_id,
            publisher_id,
            status=True
        )
        headers = get_cloud_partner_api_headers(self.access_token)

        response = process_request(
            endpoint,
            headers,
            method='get'
        )

        status = response.get('status', 'unkown')

        if status == 'running':
            signoff_status = jmespath.search(
                "steps[?stepName=='publisher-signoff'].status | [0]",
                response
            )
            if signoff_status == 'waitingForPublisherReview':
                status = 'waitingForPublisherReview'

        return status

    def get_operation(self, operation: str) -> dict:
        """
        Returns a dictionary status for the given operation.
        """
        endpoint = 'https://cloudpartner.azure.com{operation}'.format(
            operation=operation
        )

        headers = get_cloud_partner_api_headers(self.access_token)
        response = process_request(
            endpoint,
            headers
        )

        return response

    @property
    def blob_service_client(self):
        """
        Blob service client property

        Lazy blob service client initialization.
        """
        if not self.storage_account:
            raise AzureImgUtilsException(
                'Storage account is required to authenticate storage '
                'blob operations.'
            )

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
