# -*- coding: utf-8 -*-

"""Azure gallery utils cli module."""

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

import click
import logging
import sys

from azure_img_utils.cli.cli_utils import (
    add_options,
    get_config,
    process_shared_options,
    shared_options,
    echo_style
)
from azure_img_utils.azure_image import AzureImage


# -----------------------------------------------------------------------------
# Gallery commands function
@click.group(name="gallery-image-version")
def gallery_image_version():
    """
    Commands for gallery image version management.
    """


# -----------------------------------------------------------------------------
# exists command function
@gallery_image_version.command()
@click.option(
    '--gallery-image-name',
    type=click.STRING,
    required=True,
    help='Name of the gallery image to check.'
)
@click.option(
    '--gallery-name',
    type=click.STRING,
    required=True,
    help='Name of the gallery to check image existence.'
)
@click.option(
    '--gallery-image-version',
    type=click.STRING,
    required=True,
    help='Version of the gallery image to check.'
)
@add_options(shared_options)
@click.pass_context
def exists(
    context,
    gallery_image_name,
    gallery_name,
    gallery_image_version,
    **kwargs
):
    """
    Checks if a gallery image version exists
    """

    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('azure_img_utils')
    logger.setLevel(config_data.log_level)

    try:
        az_img = AzureImage(
            container=config_data.container,
            storage_account=config_data.storage_account,
            credentials_file=config_data.credentials_file,
            resource_group=config_data.resource_group,
            log_level=config_data.log_level,
            log_callback=logger
        )
        exists = az_img.gallery_image_version_exists(
            gallery_name,
            gallery_image_name,
            gallery_image_version,
            config_data.resource_group
        )

        if exists:
            echo_style('true', config_data.no_color, fg='green')
        else:
            echo_style('false', config_data.no_color)

    except Exception as e:
        echo_style(
            'Unable to check gallery image version existence',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# gallery image create command function
@gallery_image_version.command()
@click.option(
    '--blob-name',
    type=click.STRING,
    required=True,
    help='Name of the blob for the gallery image.'
)
@click.option(
    '--gallery-name',
    type=click.STRING,
    required=True,
    help='Name of the gallery where the image will be created.'
)
@click.option(
    '--gallery-image-name',
    type=click.STRING,
    required=True,
    help='Name of the gallery image to be created.'
)
@click.option(
    '--gallery-image-version',
    type=click.STRING,
    required=True,
    help='Version of the gallery image to create.'
)
@click.option(
    '--force-replace-image',
    is_flag=True,
    default=False,
    help='Delete the gallery image prior to create if it already exists.'
)
@add_options(shared_options)
@click.pass_context
def create(
    context,
    blob_name,
    gallery_name,
    gallery_image_name,
    gallery_image_version,
    force_replace_image,
    **kwargs
):
    """
    Creates a gallery image based on the already uploaded blob.
    """
    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('azure_img_utils')
    logger.setLevel(config_data.log_level)

    try:
        az_img = AzureImage(
            container=config_data.container,
            storage_account=config_data.storage_account,
            credentials_file=config_data.credentials_file,
            resource_group=config_data.resource_group,
            log_level=config_data.log_level,
            log_callback=logger
        )
        img_name = az_img.create_gallery_image_version(
            blob_name,
            gallery_name,
            gallery_image_name,
            gallery_image_version,
            config_data.region,
            force_replace_image=force_replace_image,
            gallery_resource_group=config_data.resource_group
        )

        if img_name and config_data.log_level != logging.ERROR:
            echo_style(
                f'gallery image version {img_name} created',
                config_data.no_color,
                fg='green'
            )

    except Exception as e:
        echo_style(
            'Unable to create gallery image',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# gallery image delete command function
@gallery_image_version.command()
@click.option(
    '--gallery-name',
    type=click.STRING,
    required=True,
    help='Name of the gallery where the image will be deleted.'
)
@click.option(
    '--gallery-image-name',
    type=click.STRING,
    required=True,
    help='Name of the image to delete.'
)
@click.option(
    '--gallery-image-version',
    type=click.STRING,
    required=True,
    help='Version of the gallery image to delete.'
)
@add_options(shared_options)
@click.confirmation_option(
    help='This command will delete the specified gallery image. Are you sure?'
)
@click.pass_context
def delete(
    context,
    gallery_name,
    gallery_image_name,
    gallery_image_version,
    **kwargs
):
    """
    Deletes a gallery image if the image exists in the gallery
    """

    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('azure_img_utils')
    logger.setLevel(config_data.log_level)

    try:
        az_img = AzureImage(
            container=config_data.container,
            storage_account=config_data.storage_account,
            credentials_file=config_data.credentials_file,
            resource_group=config_data.resource_group,
            log_level=config_data.log_level,
            log_callback=logger
        )
        az_img.delete_gallery_image_version(
            gallery_name,
            gallery_image_name,
            gallery_image_version,
            gallery_resource_group=config_data.resource_group
        )

    except Exception as e:
        echo_style(
            'Unable to delete gallery image version',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)
