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
import time

from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.compute import ComputeManagementClient

from azure_img_utils.auth import get_client_from_json, acquire_access_token

from azure_img_utils.exceptions import (
    AzureImgUtilsException,
    AzureImgUtilsStorageException,
    AzureCloudPartnerException
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
    get_resource_endpoint,
    process_request,
    get_durable_id,
    INGESTION_API,
    get_offer_submissions,
    deprecate_image_in_offer_doc,
    submit_configure_request,
    get_technical_details
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
        headers = get_cloud_partner_api_headers(self.access_token)
        durable_id = '/'.join(['product', get_durable_id(headers, offer_id)])
        endpoint = get_resource_endpoint(durable_id, target_type)

        response = process_request(
            endpoint,
            headers,
            method='get',
            retries=retries
        )
        return response

    def submit_request(
        self,
        resource
    ):
        """
        Submit a configuration request and wait for operation to finish

        If the operation fails raise an exception.
        """
        headers = get_cloud_partner_api_headers(self.access_token)
        job_id = submit_configure_request(headers, resource)

        operation = self.wait_on_operation(job_id)

        if operation.get('jobResult') == 'failed':
            msg = 'Failed to update resource: '
            for error in operation.get('errors', []):
                msg += error.get('message', '')
                msg += ' '
            raise AzureImgUtilsException(msg)

        return job_id

    def upload_offer_doc(
        self,
        offer_doc: dict
    ):
        """
        Upload the offer doc to partner center.

        offer_doc is a dictionary defining the offer details.
        """
        job_id = self.submit_request(offer_doc['resources'])
        return job_id

    def update_resource_in_offer(
        self,
        resource_doc: dict
    ):
        """
        Update the offer using the provided resource doc.

        resource_doc is a dictionary defining the resource details.
        """
        job_id = self.submit_request([resource_doc])
        return job_id

    def add_image_to_offer(
        self,
        blob_name: str,
        image_name: str,
        offer_id: str,
        sku: str,
        blob_url: str = None,
        generation_id: str = None
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

        offer_doc = self.get_offer_doc(offer_id)
        plan_details = get_technical_details(offer_doc, sku)

        kwargs = {
            'generation_id': generation_id
        }

        plan_details = add_image_version_to_offer(
            plan_details,
            blob_url,
            image_name,
            sku,
            **kwargs
        )
        self.update_resource_in_offer(
            plan_details
        )

    def remove_image_from_offer(
        self,
        image_urn: str
    ):
        """
        Delete the given image version from the offer.

        The offer is pulled from the partner center, the old image version
        is deleted and re-uploaded. To make the new image available
        the offer must be published and set to go-live.
        """
        publisher_id, offer_id, plan_id, image_version = image_urn.split(':')
        offer_doc = self.get_offer_doc(offer_id)
        plan_details = get_technical_details(offer_doc, plan_id)

        plan_details = deprecate_image_in_offer_doc(
            plan_details,
            image_version
        )
        self.update_resource_in_offer(
            plan_details
        )

    def publish_offer(
        self,
        offer_id: str
    ) -> str:
        """
        Publish the given offer.

        Returns the operation uri.
        """
        headers = get_cloud_partner_api_headers(self.access_token)
        durable_id = get_durable_id(headers, offer_id)

        resources = [
            {
                '$schema': (
                    'https://schema.mp.microsoft.com/'
                    'schema/submission/2022-03-01-preview2'
                ),
                'product': '/'.join(['product', durable_id]),
                'target': {'targetType': 'preview'}
            }
        ]

        job_id = self.submit_request(resources)
        return job_id

    def go_live_with_offer(
        self,
        offer_id: str
    ) -> str:
        """
        Set the offer as go-live.

        This makes all new changes to the offer publicly visible.

        Returns the operation uri.
        """
        headers = get_cloud_partner_api_headers(self.access_token)
        durable_id = get_durable_id(headers, offer_id)
        submissions = get_offer_submissions(durable_id, headers)

        operation_id = jmespath.search(
            "value[?target.targetType=='preview'] | [0].id",
            submissions
        )

        resources = [
            {
                '$schema': (
                    'https://schema.mp.microsoft.com/'
                    'schema/submission/2022-03-01-preview2'
                ),
                'product': '/'.join(['product', durable_id]),
                'id': operation_id,
                'target': {'targetType': 'live'}
            }
        ]

        job_id = self.submit_request(resources)
        return job_id

    def get_offer_status(self, offer_id: str) -> str:
        """
        Returns the status of the offer.
        """
        headers = get_cloud_partner_api_headers(self.access_token)
        durable_id = get_durable_id(headers, offer_id)
        submissions = get_offer_submissions(durable_id, headers)

        prev_ops = jmespath.search(
            "value[?target.targetType=='preview']"
            ".{status: status, result: result}",
            submissions
        )

        if prev_ops:
            operation = prev_ops[0]
            status = operation.get('status', 'unknown')
            result = operation.get('result', 'unknown')

            if status == 'running':
                # Offer publishing
                return status
            elif status == 'completed' and result == 'failed':
                # Publish failed
                return result
            elif status == 'completed' and result == 'succeeded':
                # Waiting for review
                return 'waitingForPublisherReview'

        live_ops = jmespath.search(
            "value[?target.targetType=='live']"
            ".{status: status, result: result}",
            submissions
        )

        if live_ops and len(live_ops) == 1:
            operation = live_ops[0]
            status = operation.get('status', 'unknown')
            result = operation.get('result', 'unknown')

            if status == 'completed':
                return result
            elif status == 'running':
                # Initial go live
                return status
        elif live_ops and len(live_ops) == 2:
            for operation in live_ops:
                status = operation.get('status', 'unknown')
                result = operation.get('result', 'unknown')

                if status == 'running':
                    # New version going live
                    return status
                elif status == 'completed' and result == 'failed':
                    # Go live failed
                    return result

        return 'unkown'

    def wait_on_operation(
        self,
        operation_id: str,
        timeout: int = 600
    ) -> dict:
        """
        Wait until the operation finishes then return the dictionary status
        """
        time_left = timeout
        wait = 1

        while time_left > 0:
            operation = self.get_operation(operation_id)

            status = operation.get('jobStatus', 'unknown')
            if status in ('completed', 'unkown'):
                return operation

            sleep_time = min(wait, time_left)
            time.sleep(sleep_time)
            time_left -= sleep_time
            wait *= 2

        raise AzureImgUtilsException(
            f'Timeout waiting for operation {operation_id} to finish. '
            f'Current status is {status}.'
        )

    def get_operation(self, operation: str) -> dict:
        """
        Returns a dictionary status for the given operation.
        """
        headers = get_cloud_partner_api_headers(self.access_token)
        endpoint = '/'.join([INGESTION_API, 'configure', operation, 'status'])

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
