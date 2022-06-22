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
# Blob commands function
@click.group()
def blob():
    """
    Commands for blob management.
    """


# -----------------------------------------------------------------------------
# blob exists commands function
@blob.command()
@click.option(
    '--blob-name',
    type=click.STRING,
    required=True,
    help='Name of the blob to check.'
)
@add_options(shared_options)
@click.pass_context
def exists(
    context,
    blob_name,
    **kwargs
):
    """
    Checks if a blob exists for the specified container
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
        exists = az_img.image_blob_exists(blob_name)

        if exists:
            echo_style('true', config_data.no_color, fg='green')
        else:
            echo_style('false', config_data.no_color)

    except Exception as e:
        echo_style(
            'Unable to check blob existence',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# blob upload command function
@blob.command()
@click.option(
    '--blob-name',
    type=click.STRING,
    required=True,
    help='Name of the blob to upload.'
)
@click.option(
    '--image-file',
    type=click.Path(exists=True),
    required=True,
    help='Path to file to upload as blob.'
)
@click.option(
    '--force-replace-image',
    is_flag=True,
    default=False,
    help='Delete the image prior to upload if it already exists.'
)
@click.option(
    '--page-blob',
    is_flag=True,
    default=False,
    help='The image to upload is of page blob type.'
)
@click.option(
    '--expand-image',
    is_flag=True,
    default=False,
    help='The image to upload should be expanded.'
)
@click.option(
    '--max-workers',
    type=click.IntRange(min=1),
    default=5,
    help='Maximum number of workers allowed for upload.'
)
@click.option(
    '--max-attempts',
    type=click.IntRange(min=1),
    default=5,
    help='Maximum number of attempts for upload.'
)
@add_options(shared_options)
@click.pass_context
def upload(
    context,
    blob_name,
    image_file,
    force_replace_image,
    page_blob,
    expand_image,
    max_workers,
    max_attempts,
    **kwargs
):
    """
    Uploads an file as blob to the specified container
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
        blob_name = az_img.upload_image_blob(
            image_file,
            max_workers=max_workers,
            max_attempts=max_attempts,
            blob_name=blob_name,
            force_replace_image=force_replace_image,
            is_page_blob=page_blob,
            expand_image=expand_image
        )

        if blob_name and config_data.log_level != logging.ERROR:
            echo_style(
                f'blob {blob_name} uploaded',
                config_data.no_color,
                fg='green'
            )

    except Exception as e:
        echo_style(
            'Unable to upload blob',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# Blob delete commands function
@blob.command()
@click.option(
    '--blob-name',
    type=click.STRING,
    required=True,
    help='Name of the blob to check.'
)
@add_options(shared_options)
@click.confirmation_option(
    help='This command will delete the specified blob. Are you sure?'
)
@click.pass_context
def delete(
    context,
    blob_name,
    **kwargs
):
    """
    Deletes the specified blob in the container
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
        deleted = az_img.delete_storage_blob(blob_name)

        if deleted and context.obj['log_level'] != logging.ERROR:
            echo_style('blob deleted', config_data.no_color, fg='green')
        elif not deleted:
            echo_style(f'blob {blob_name} not found', config_data.no_color)

    except Exception as e:
        echo_style(
            'Unable to delete blob',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)
