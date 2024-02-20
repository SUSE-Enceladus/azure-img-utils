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

from azure_img_utils.exceptions import AzureCloudPartnerException
from requests.exceptions import HTTPError

INGESTION_API = 'https://graph.microsoft.com/rp/product-ingestion/'
VM_IMAGES_KEY = 'vmImageVersions'
PLAN_SCHEMA = 'https://schema.mp.microsoft.com/schema/plan/'
TECH_CONFIG_SCHEMA = 'virtual-machine-plan-technical-configuration'


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
    plan_id: str
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

    for resource in offer_doc['resources']:
        if (
            TECH_CONFIG_SCHEMA in resource['$schema'] and
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
