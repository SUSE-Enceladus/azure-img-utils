# -*- coding: utf-8 -*-

"""Azure image utils cli module."""

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
# Image commands function
@click.group()
def image():
    """
    Commands for image management.
    """


# -----------------------------------------------------------------------------
# image exists command function
@image.command()
@click.option(
    '--image-name',
    type=click.STRING,
    required=True,
    help='Name of the image to check.'
)
@add_options(shared_options)
@click.pass_context
def exists(
    context,
    image_name,
    **kwargs
):
    """
    Checks if a image exists
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
            log_level=config_data.log_level
        )
        exists = az_img.image_exists(image_name)

        if exists:
            echo_style('true', config_data.no_color, fg='green')
        else:
            echo_style('false', config_data.no_color)

    except Exception as e:
        echo_style(
            'Unable to check image existence',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# image create command function
@image.command()
@click.option(
    '--blob-name',
    type=click.STRING,
    required=True,
    help='Name of the blob for the image.'
)
@click.option(
    '--image-name',
    type=click.STRING,
    required=True,
    help='Name of the image to be created.'
)
@click.option(
    '--force-replace-image',
    is_flag=True,
    default=False,
    help='Delete the image prior to create if it already exists.'
)
@click.option(
    '--hyper-v-generation',
    type=click.STRING,
    default='V1',
    help='Hypervisor generation for the image. Defaults to "V1". '
         '"V2" is for uefi boot  and "V1" for legacy bios.'
)
@add_options(shared_options)
@click.pass_context
def create(
    context,
    blob_name,
    image_name,
    force_replace_image,
    hyper_v_generation,
    **kwargs
):
    """
    Creates an image based on the already uploaded blob.
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
        img_name = az_img.create_compute_image(
            blob_name,
            image_name,
            config_data.region,
            force_replace_image=force_replace_image,
            hyper_v_generation=hyper_v_generation
        )

        if img_name and config_data.log_level != logging.ERROR:
            echo_style(
                f'image {img_name} created',
                config_data.no_color,
                fg='green'
            )

    except Exception as e:
        echo_style(
            'Unable to create image',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# image delete command function
@image.command()
@click.option(
    '--image-name',
    type=click.STRING,
    required=True,
    help='Name of the image to delete.'
)
@add_options(shared_options)
@click.confirmation_option(
    help='This command will delete the specified image. Are you sure?'
)
@click.pass_context
def delete(
    context,
    image_name,
    **kwargs
):
    """
    Deletes an image if the image exists in the resource group
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
            log_level=config_data.log_level
        )
        # Result object for this async operation is always None
        # in Azure SDK.
        az_img.delete_compute_image(image_name)

    except Exception as e:
        echo_style(
            'Unable to delete image',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)
