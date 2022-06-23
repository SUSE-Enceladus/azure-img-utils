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


def create_gallery_image_definition_version(
    blob_name: str,
    gallery_name: str,
    gallery_image_name: str,
    image_version: str,
    region: str,
    resource_group: str,
    storage_account: str,
    container: str,
    compute_client,
    gallery_resource_group: str = None
):
    """
    Create new gallery image definition version

    The image is replicated only in one source region.
    """
    if not gallery_resource_group:
        gallery_resource_group = resource_group

    subscription_id = compute_client._config.subscription_id
    image_profile = {
        'location': region,
        'publishing_profile': {
            'target_regions': [
                {
                    'name': region
                }
            ]
        },
        'storage_profile': {
            'os_disk_image': {
                'source': {
                    'id': f'/subscriptions/{subscription_id}/'
                          f'resourceGroups/{resource_group}/'
                          'providers/Microsoft.Storage/'
                          f'storageAccounts/{storage_account}',
                    'uri': f'https://{storage_account}.blob.core.windows.net/'
                           f'{container}/{blob_name}'
                },
                'host_caching': 'ReadWrite'
            }
        }
    }

    async_create = compute_client.gallery_image_versions.begin_create_or_update(  # noqa
        gallery_resource_group,
        gallery_name,
        gallery_image_name,
        image_version,
        image_profile
    )
    async_create.result()

    return gallery_image_name


def remove_gallery_image_version(
    gallery_name: str,
    gallery_image_name: str,
    image_version: str,
    gallery_resource_group: str,
    compute_client
):
    """
    Delete the gallery image version from the gallery definition.
    """
    async_delete_image = compute_client.gallery_image_versions.begin_delete(
        gallery_resource_group,
        gallery_name,
        gallery_image_name,
        image_version
    )
    async_delete_image.result()


def get_image(compute_client, image_name: str):
    """
    Return image if it exists based on the image name.
    """
    images = compute_client.images.list()

    for image in images:
        if image_name == image.name:
            return image


def retrieve_gallery_image_version(
    gallery_name: str,
    gallery_image_name: str,
    image_version: str,
    gallery_resource_group: str,
    compute_client
):
    """
    Return gallery image if it exists based on the gallery_image_name.

    Return None if an exception is raised. A generic exception is raised
    if the resource is not found.
    """
    try:
        image = compute_client.gallery_image_versions.get(
            gallery_resource_group,
            gallery_name,
            gallery_image_name,
            image_version
        )
    except Exception:
        # A generic exception is always raised if resource not found
        # so there's no disadvantage to return None.
        return None

    return image.as_dict()
