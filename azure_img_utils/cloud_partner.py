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
import re
import requests
import time

from datetime import date, datetime
from azure.containerregistry import ContainerRegistryClient

from azure_img_utils.exceptions import (
    AzureImgUtilsException,
    AzureCloudPartnerException
)
from azure_img_utils.container_registry import get_digest_for_tag
from requests.exceptions import HTTPError

INGESTION_API = 'https://graph.microsoft.com/rp/product-ingestion/'
VM_IMAGES_KEY = 'vmImageVersions'
CNAB_REFERENCES_KEY = 'cnabReferences'
PLAN_SCHEMA = 'https://schema.mp.microsoft.com/schema/plan/'
TECH_CONFIG_SCHEMA = 'virtual-machine-plan-technical-configuration'
CONTAINER_TECH_CONFIG_SCHEMA = 'container-plan-technical-configuration'


def get_resource_endpoint(
    durable_id: str,
    target_type: str = 'draft'
) -> str:
    """
    Return the endpoint URL to cloud partner API for offer and publisher.
    """
    endpoint = (
        f'{INGESTION_API}/resource-tree/{durable_id}?'
        f'targetType={target_type}'
    )
    return endpoint


def get_durable_id(
    headers: dict,
    offer_id: str,
) -> str:
    endpoint = f'{INGESTION_API}product?externalid={offer_id}'
    response = process_request(endpoint, headers)

    if not response.get('value'):
        raise AzureCloudPartnerException(
            f'Offer {offer_id} not found.'
        )

    return response['value'][0]['id'].replace('product/', '')


def get_technical_details(
    offer_doc: dict,
    plan_id: str,
    container_offer: bool = False
):
    for resource in offer_doc['resources']:
        if (
            resource['$schema'].startswith(PLAN_SCHEMA) and
            resource['identity']['externalId'] == plan_id
        ):
            durable_id = resource['id']
            break
    else:
        raise AzureCloudPartnerException(
            f'No plan found for id: {plan_id}'
        )

    if container_offer:
        tech_details_config_schema = CONTAINER_TECH_CONFIG_SCHEMA
    else:
        tech_details_config_schema = TECH_CONFIG_SCHEMA

    for resource in offer_doc['resources']:
        if (
            tech_details_config_schema in resource['$schema'] and
            resource['plan'] == durable_id
        ):
            return resource
    else:
        raise AzureCloudPartnerException(
            f'No technical details found for plan durable id: {durable_id}'
        )


def get_cloud_partner_api_headers(
    access_token: str,
    content_type: str = None,
    if_match: str = None,
    content_length: str = None
) -> dict:
    """
    Return dictionary of request headers for cloud partner API.
    """
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + access_token
    }

    if content_type:
        headers['Content-Type'] = content_type

    if if_match:
        headers['If-Match'] = if_match

    if content_length is not None:
        headers['Content-Length'] = content_length

    return headers


def process_request(
    endpoint: str,
    headers: dict,
    data: dict = None,
    method: str = 'get',
    json_response: bool = True,
    retries: int = 5
):
    """
    Build and run API request.

    If the response code is not successful raise an exception for status.

    Return the response or json content.
    """
    kwargs = {
        'headers': headers
    }

    if data:
        kwargs['data'] = json.dumps(data)

    sleep = 1
    while True:
        try:
            response = getattr(requests, method)(
                endpoint,
                **kwargs
            )
        except requests.exceptions.ConnectionError:
            if retries <= 0:
                raise
            else:
                retries -= 1
                sleep = sleep * 2
                continue

        if response.status_code in (200, 202):
            break
        elif retries <= 0:
            try:
                response.raise_for_status()
            except HTTPError as e:
                if response.text:
                    raise HTTPError(
                        '{} Error Message: {}'.format(str(e), response.text),
                        response=response
                    )
                else:
                    raise e
        else:
            retries -= 1
            sleep = sleep * 2

        time.sleep(sleep)

    if json_response:
        return response.json()
    else:
        return response


def get_offer_submissions(durable_id: str, headers: dict) -> dict:
    endpoint = f'{INGESTION_API}submission/{durable_id}'

    response = process_request(
        endpoint,
        headers
    )

    return response


def add_image_version_to_offer(
    doc: dict,
    blob_url: str,
    image_name: str,
    sku: str,
    generation_id: str = None
) -> dict:
    """
    Update the cloud partner offer doc with a new version of the given sku.
    """
    matches = re.findall(r'\d{8}', image_name)

    # If image name already has a date use it as release date.
    if matches:
        release_date = datetime.strptime(matches[0], '%Y%m%d').date()
    else:
        release_date = date.today()

    version_number = release_date.strftime('%Y.%m.%d')

    version = {
        'versionNumber': version_number,
        'vmImages': [],
        'lifecycleState': 'generallyAvailable'
    }

    image_type = get_image_type(sku, doc['skus'])
    version['vmImages'].append(
        {
            'imageType': image_type,
            'source': {
                'sourceType': 'sasUri',
                'osDisk': {
                    'uri': blob_url
                },
                'dataDisks': []
            }
        }
    )

    if generation_id:
        image_type = get_image_type(generation_id, doc['skus'])
        version['vmImages'].append(
            {
                'imageType': image_type,
                'source': {
                    'sourceType': 'sasUri',
                    'osDisk': {
                        'uri': blob_url
                    },
                    'dataDisks': []
                }
            }
        )

    doc[VM_IMAGES_KEY].append(version)
    return doc


def get_image_type(
    plan_id: str,
    skus: list
):
    for sku in skus:
        if plan_id == sku['skuId']:
            return sku['imageType']
    else:
        raise AzureCloudPartnerException(
            f'No Match found for SKU: {plan_id}. '
            'Offer doc not updated properly.'
        )


def deprecate_image_in_offer_doc(
    doc: dict,
    image_version: str
) -> dict:
    """
    Deprecate the image version in the cloud partner offer doc.
    """
    for doc_version in doc[VM_IMAGES_KEY]:
        if image_version == doc_version['versionNumber']:
            doc_version['lifecycleState'] = 'deprecated'
            break
    else:
        raise AzureCloudPartnerException(
            f'No Match found for the image version: {image_version}. '
            'Offer doc not updated properly.'
        )

    return doc


def submit_configure_request(
    headers: dict,
    resources: list
):
    headers['Content-Type'] = 'application/json'
    endpoint = INGESTION_API + '/configure'

    response = process_request(
        endpoint,
        headers,
        data={
            '$schema': (
                'https://schema.mp.microsoft.com/'
                'schema/configure/2022-03-01-preview2'
            ),
            'resources': resources
        },
        method='post'
    )

    return response['jobId']


def get_offer_doc(
    access_token: str,
    offer_id: str,
    target_type: str = 'draft',
    retries: int = 5
) -> dict:
    """
    Returns the offer doc dictionary for the given offer.
    """
    headers = get_cloud_partner_api_headers(access_token)
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
    access_token,
    resource,
    wait: bool = True
):
    """
    Submit a configuration request and wait for operation to finish
    If the operation fails raise an exception.
    """
    headers = get_cloud_partner_api_headers(access_token)
    job_id = submit_configure_request(headers, resource)

    if wait:
        operation = wait_on_operation(job_id)

        if operation.get('jobResult') == 'failed':
            msg = 'Failed to update resource: '
            for error in operation.get('errors', []):
                msg += error.get('message', '')
                msg += ' '
            raise AzureImgUtilsException(msg)

    return job_id


def get_operation(access_token: str, operation: str) -> dict:
    """
    Returns a dictionary status for the given operation.
    """
    headers = get_cloud_partner_api_headers(access_token)
    endpoint = '/'.join([INGESTION_API, 'configure', operation, 'status'])

    response = process_request(
        endpoint,
        headers
    )
    return response


def wait_on_operation(
    access_token: str,
    operation_id: str,
    timeout: int = 600
) -> dict:
    """
    Wait until the operation finishes then return the dictionary status
    """
    time_left = timeout
    wait = 1

    while time_left > 0:
        operation = get_operation(access_token, operation_id)

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


def add_cnab_version_to_offer(
    doc: dict,
    tag: str,
    digest: str = None,
    tenant_id: str = None,
    subscription_id: str = None,
    resource_group_name: str = None,
    registry_name: str = None,
    repository_name: str = None,
    acr_client: ContainerRegistryClient = None
) -> dict:
    """
    Update the cloud partner offer doc with a new version of the given sku.
    """

    default_cnab = doc[CNAB_REFERENCES_KEY][0]
    cnab_reference = {**default_cnab}

    cnab_reference['tag'] = tag
    if digest:
        cnab_reference['digest'] = digest
    elif acr_client and repository_name:
        cnab_reference['digest'] = get_digest_for_tag(
            acr_client,
            repository_name,
            tag
        )

    if tenant_id:
        cnab_reference['tenantId'] = tenant_id
    if subscription_id:
        cnab_reference['subscriptionId'] = subscription_id
    if resource_group_name:
        cnab_reference['resourceGroupName'] = resource_group_name
    if registry_name:
        cnab_reference['registryName'] = registry_name
    if repository_name:
        cnab_reference['repositoryName'] = repository_name

    doc[CNAB_REFERENCES_KEY].append(cnab_reference)
    return doc


def remove_cnab_version_from_offer_doc(
    doc: dict,
    registry_name: str,
    repository_name: str,
    tag: str
) -> dict:
    """
    Deprecate the image version in the cloud partner offer doc.
    """
    for cnab_ref in doc[CNAB_REFERENCES_KEY]:
        if all([
            registry_name == cnab_ref['registryName'],
            repository_name == cnab_ref['repositoryName'],
            tag == cnab_ref['tag']
        ]):
            doc[CNAB_REFERENCES_KEY].remove(cnab_ref)
            break
    else:
        raise AzureCloudPartnerException(
            'No Match found for the cnab version with '
            f'registry:{registry_name} '
            f'repository:{repository_name} '
            f'tag: {tag} .'
            'Offer doc not updated properly.'
        )

    return doc
