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

from azure.containerregistry import ContainerRegistryClient


def get_list_of_available_cnab_tags(
    acr_client: ContainerRegistryClient,
    repository_name: str
) -> list:
    """
    Lists the available versions of the cnab tags in the provided container
    registry.
    """
    tags = []
    for tag in acr_client.list_tag_properties(repository_name):
        tags.append(tag.name)
    return tags


def cnab_tag_is_available(
    acr_client: ContainerRegistryClient,
    repository_name: str,
    tag: str
) -> bool:
    """
    Returns True if the provided tag is available in the registry/repository
    name provided
    """
    if tag in get_list_of_available_cnab_tags(
        acr_client,
        repository_name=repository_name
    ):
        return True
    return False


def get_digest_for_tag(
    acr_client: ContainerRegistryClient,
    repository_name: str,
    tag: str
) -> str:
    """Provides the digest of a tag in the registry/repository provided"""
    properties = acr_client.get_tag_properties(repository_name, tag)
    if properties and properties.digest:
        return properties.digest
    return ''
