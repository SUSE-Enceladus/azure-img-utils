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


def create_image(
    blob_name: str,
    image_name: str,
    compute_client,
    container: str,
    resource_group: str,
    storage_account: str,
    region: str,
    hyper_v_generation: str = 'V1'
):
    """
    Create image in ARM from existing page blob.

    hyper v generation of V2 is uefi and V1 is legacy bios.
    """
    async_create_image = compute_client.images.begin_create_or_update(
        resource_group,
        image_name, {
            'location': region,
            'hyper_v_generation': hyper_v_generation,
            'storage_profile': {
                'os_disk': {
                    'os_type': 'Linux',
                    'os_state': 'Generalized',
                    'caching': 'ReadWrite',
                    'blob_uri': 'https://{0}.{1}/{2}/{3}'.format(
                        storage_account,
                        'blob.core.windows.net',
                        container,
                        blob_name
                    )
                }
            }
        }
    )
    async_create_image.result()

    return image_name


def delete_image(compute_client, resource_group: str, image_name: str):
    """
    Delete the image from resource group.
    """
    async_delete_image = compute_client.images.begin_delete(
        resource_group,
        image_name
    )
    async_delete_image.result()


def list_images(compute_client):
    """
    Returns a list of image names.
    """
    images = compute_client.images.list()

    names = []
    for image in images:
        names.append(image.name)

    return names


def image_exists(compute_client, image_name: str):
    """
    Return True if an image with name image_name exists.
    """
    images = list_images(compute_client)
    return image_name in images


def get_image(compute_client, image_name: str):
    """
    Return image if it exists based on the image name.
    """
    images = compute_client.images.list()

    for image in images:
        if image_name == image.name:
            return image
