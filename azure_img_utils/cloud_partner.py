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

import copy
import jmespath
import json
import re
import requests
import time

from datetime import date, datetime

from azure_img_utils.exceptions import AzureCloudPartnerException


def go_live_with_cloud_partner_offer(
    access_token: str,
    offer_id: str,
    publisher_id: str
) -> str:
    """
    Go live with cloud partner offer and return the operation location.
    """
    endpoint = get_cloud_partner_endpoint(
        offer_id,
        publisher_id,
        go_live=True
    )
    headers = get_cloud_partner_api_headers(
        access_token,
        content_type='application/json'
    )

    response = process_request(
        endpoint,
        headers,
        method='post',
        json_response=False
    )

    return response.headers['Location']


def get_cloud_partner_endpoint(
    offer_id: str,
    publisher_id: str,
    api_version: str = '2017-10-31',
    publish: bool = False,
    go_live: bool = False,
    status: bool = False
) -> str:
    """
    Return the endpoint URL to cloud partner API for offer and publisher.
    """
    endpoint = 'https://cloudpartner.azure.com/api/' \
               'publishers/{publisher_id}/' \
               'offers/{offer_id}' \
               '{method}' \
               '?api-version={api_version}'

    if publish:
        method = '/publish'
    elif go_live:
        method = '/golive'
    elif status:
        method = '/status'
    else:
        method = ''

    endpoint = endpoint.format(
        offer_id=offer_id,
        publisher_id=publisher_id,
        method=method,
        api_version=api_version
    )

    return endpoint


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


def get_cloud_partner_operation(access_token: str, operation: str) -> dict:
    """
    Get the status of the provided API operation.
    """
    endpoint = 'https://cloudpartner.azure.com{operation}'.format(
        operation=operation
    )

    headers = get_cloud_partner_api_headers(access_token)
    response = process_request(
        endpoint,
        headers
    )

    return response


def put_cloud_partner_offer_doc(
    access_token: str,
    doc: dict,
    offer_id: str,
    publisher_id: str
):
    """
    Put an updated cloud partner offer doc to the API.
    """
    endpoint = get_cloud_partner_endpoint(
        offer_id,
        publisher_id
    )
    headers = get_cloud_partner_api_headers(
        access_token,
        content_type='application/json',
        if_match='*'
    )

    response = process_request(
        endpoint,
        headers,
        data=doc,
        method='put'
    )

    return response


def publish_cloud_partner_offer(
    access_token: str,
    offer_id: str,
    publisher_id: str,
    notification_emails: str
):
    """
    Publish the cloud partner offer and return the operation location.
    """
    endpoint = get_cloud_partner_endpoint(
        offer_id,
        publisher_id,
        publish=True
    )
    headers = get_cloud_partner_api_headers(
        access_token,
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
            response.raise_for_status()
        else:
            retries -= 1
            sleep = sleep * 2

        time.sleep(sleep)

    if json_response:
        return response.json()
    else:
        return response


def request_cloud_partner_offer_doc(
    access_token: str,
    offer_id: str,
    publisher_id: str
) -> dict:
    """
    Request a Cloud Partner Offer doc for the provided publisher and offer.
    """
    endpoint = get_cloud_partner_endpoint(
        offer_id,
        publisher_id
    )
    headers = get_cloud_partner_api_headers(access_token)

    response = process_request(
        endpoint,
        headers,
        method='get'
    )

    return response


def get_cloud_partner_offer_status(
    access_token: str,
    offer_id: str,
    publisher_id: str
) -> dict:
    """
    Returns the status of a Cloud Partner Offer based on id and publisher.

    If status is not found "unkown" is returned. If offer is publishing
    and publisher-signoff step is waitingForPublisherReview then this
    is the offer status. The offer is waiting for publisher to trigger
    go-live.
    """
    endpoint = get_cloud_partner_endpoint(
        offer_id,
        publisher_id,
        status=True
    )
    headers = get_cloud_partner_api_headers(access_token)

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


def add_image_version_to_offer(
    doc: dict,
    blob_url: str,
    description: str,
    image_name: str,
    label: str,
    sku: str,
    vm_images_key: str = 'microsoft-azure-corevm.vmImagesPublicAzure',
    generation_id: str = None,
    cloud_image_name_generation_suffix: str = None
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

    version = {
        'osVhdUrl': blob_url,
        'label': label,
        'mediaName': image_name,
        'publishedDate': release_date.strftime("%m/%d/%Y"),
        'description': description,
        'showInGui': True,
        'lunVhdDetails': []
    }

    for doc_sku in doc['definition']['plans']:
        if doc_sku['planId'] == sku:
            release = release_date.strftime("%Y.%m.%d")

            if vm_images_key not in doc_sku:
                doc_sku[vm_images_key] = {}

            doc_sku[vm_images_key][release] = version

            if generation_id:
                for plan in doc_sku['diskGenerations']:
                    if plan['planId'] == generation_id:
                        generation_version = copy.deepcopy(version)
                        generation_version['mediaName'] = '-'.join([
                            image_name,
                            cloud_image_name_generation_suffix or generation_id
                        ])

                        if vm_images_key not in plan:
                            plan[vm_images_key] = {}

                        plan[vm_images_key][release] = generation_version
                        break
                else:
                    raise AzureCloudPartnerException(
                        'No Match found for Generation ID: {gen}. '
                        'Offer doc not updated properly.'.format(
                            gen=generation_id
                        )
                    )

            break
    else:
        raise AzureCloudPartnerException(
            'No Match found for SKU: {sku}. '
            'Offer doc not updated properly.'.format(
                sku=sku
            )
        )

    return doc


def remove_image_version_from_offer(
    doc: dict,
    image_version: str,
    sku: str,
    generation_id: str = None,
    vm_images_key: str = 'microsoft-azure-corevm.vmImagesPublicAzure'
) -> dict:
    """
    Remove the given image version from the cloud partner offer doc.
    """
    for doc_sku in doc['definition']['plans']:
        if doc_sku['planId'] == sku:
            if image_version in doc_sku[vm_images_key]:
                del doc_sku[vm_images_key][image_version]

            if generation_id:
                for plan in doc_sku['diskGenerations']:
                    if plan['planId'] == generation_id:
                        if image_version in plan[vm_images_key]:
                            del plan[vm_images_key][image_version]
                            break
                else:
                    raise AzureCloudPartnerException(
                        'No Match found for Generation ID: {gen}. '
                        'Offer doc not updated properly.'.format(
                            gen=generation_id
                        )
                    )

            break
    else:
        raise AzureCloudPartnerException(
            'No Match found for SKU: {sku}. '
            'Offer doc not updated properly.'.format(
                sku=sku
            )
        )

    return doc


def deprecate_image_in_offer_doc(
    doc: dict,
    image_name: str,
    sku: str,
    log_callback,
    vm_images_key: str = 'microsoft-azure-corevm.vmImagesPublicAzure'
) -> dict:
    """
    Deprecate the image in the cloud partner offer doc.

    The image is set to not show in gui.
    """
    matches = re.findall(r'\d{8}', image_name)

    if matches:
        release_date = datetime.strptime(matches[0], '%Y%m%d').date()
        release = release_date.strftime("%Y.%m.%d")
    else:
        # image name must have a date to generate release key
        return doc

    for doc_sku in doc['definition']['plans']:
        if doc_sku['planId'] == sku \
                and doc_sku.get(vm_images_key) \
                and doc_sku[vm_images_key].get(release):

            image = doc_sku[vm_images_key][release]

            if image['mediaName'] == image_name:
                image['showInGui'] = False
            else:
                log_callback(
                    'Deprecation image name, {0} does match the mediaName '
                    'attribute, {1}.'.format(
                        image_name,
                        image['mediaName']
                    )
                )

            break
    else:
        raise AzureCloudPartnerException(
            f'No Match found for image in the SKU: {sku}. '
            'Offer doc not updated properly.'
        )

    return doc
