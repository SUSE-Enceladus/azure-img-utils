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
    get_obj_from_json_file,
    process_shared_options,
    shared_options,
    echo_style
)
from azure_img_utils.azure_image import AzureImage


# -----------------------------------------------------------------------------
# Offer commands function
@click.group(name="cloud-partner-offer")
def offer():
    """
    Commands for cloud partner offer management.
    """


# -----------------------------------------------------------------------------
# cloud partner offer publish command function
@offer.command()
@click.option(
    '--offer-id',
    type=click.STRING,
    required=True,
    help='Id of the cloud partner offer to publish.'
)
@add_options(shared_options)
@click.pass_context
def publish(
    context,
    offer_id,
    **kwargs
):
    """
    Publishes a cloud partner offer
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
        operation_uri = az_img.publish_offer(
            offer_id,
            config_data.publisher_id,
            config_data.notification_emails
        )

        if operation_uri:
            echo_style(
                'Published cloud partner offer. Operation URI: ' +
                operation_uri,
                config_data.no_color,
                fg='green'
            )

    except Exception as e:
        echo_style(
            'Unable to publish cloud partner offer',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# cloud partner offer go-live command function
@offer.command(name="go-live")
@click.option(
    '--offer-id',
    type=click.STRING,
    required=True,
    help='Id of the cloud partner offer to publish.'
)
@add_options(shared_options)
@click.pass_context
def go_live(
    context,
    offer_id,
    **kwargs
):
    """
    Publishes a cloud partner offer as go-live
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
        operation_uri = az_img.go_live_with_offer(
            offer_id,
            config_data.publisher_id
        )

        if operation_uri:
            echo_style(
                'Cloud partner offer set as go-live. Operation URI: ' +
                operation_uri,
                config_data.no_color,
                fg='green'
            )

    except Exception as e:
        echo_style(
            'Unable to set cloud partner offer as go-live.',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# cloud partner offer upload-offer-document command function
@offer.command(name="upload-offer-document")
@click.option(
    '--offer-id',
    type=click.STRING,
    required=True,
    help='Id of the cloud partner offer to publish.'
)
@click.option(
    '--offer-document-file',
    type=click.Path(exists=True),
    required=True,
    help='File containing the offer document as json.'
)
@add_options(shared_options)
@click.pass_context
def upload_offer_document(
    context,
    offer_id,
    offer_document_file,
    **kwargs
):
    """
    Puts a offer json document to a cloud partner offer
    """

    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('azure_img_utils')
    logger.setLevel(config_data.log_level)

    try:
        offer_obj = get_obj_from_json_file(offer_document_file)

        az_img = AzureImage(
            container=config_data.container,
            storage_account=config_data.storage_account,
            credentials_file=config_data.credentials_file,
            resource_group=config_data.resource_group,
            log_level=config_data.log_level,
            log_callback=logger
        )
        az_img.upload_offer_doc(
            offer_id,
            config_data.publisher_id,
            offer_obj
        )

    except Exception as e:
        echo_style(
            'Unable to upload cloud partner offer document.',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# cloud partner offer add-image-to-offer command function
@offer.command(name="add-image-to-offer")
@click.option(
    '--blob-name',
    type=click.STRING,
    required=True,
    help='Name of the blob to be used for the image'
)
@click.option(
    '--image-name',
    type=click.STRING,
    required=True,
    help='Name for the image'
)
@click.option(
    '--image-description',
    type=click.STRING,
    required=True,
    help='Description for the image added to the offer'
)
@click.option(
    '--offer-id',
    type=click.STRING,
    required=True,
    help='Id of the cloud partner offer to use.'
)
@click.option(
    '--label',
    type=click.STRING,
    required=True,
    help='Label to be used for the new image'
)
@click.option(
    '--sku',
    type=click.STRING,
    required=True,
    help='SKU to be used for the image addition'
)
@click.option(
    '--blob-url',
    type=click.STRING,
    help='Blob URL to be used. (Optional. A blob url is generated '
         ' if not provided)'
)
@click.option(
    '--generation-id',
    type=click.STRING,
    help='Generation id to be used for the image addition'
)
@click.option(
    '--generation-suffix',
    type=click.STRING,
    help='Generation suffix to be used for the image addition'
)
@click.option(
    '--vm-images-key',
    type=click.STRING,
    help='SSH key to be allowed to access the image'
)
@add_options(shared_options)
@click.pass_context
def add_image_to_offer(
    context,
    blob_name,
    image_name,
    image_description,
    offer_id,
    label,
    sku,
    blob_url,
    generation_id,
    generation_suffix,
    vm_images_key,
    **kwargs
):
    """
    Adds an image to a cloud partner offer
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
        az_img.add_image_to_offer(
            blob_name,
            image_name,
            image_description,
            offer_id,
            config_data.publisher_id,
            label,
            sku,
            blob_url=blob_url,
            generation_id=generation_id,
            generation_suffix=generation_suffix,
            vm_images_key=vm_images_key
        )

    except Exception as e:
        echo_style(
            'Unable to add image to cloud partner offer.',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# cloud partner offer remove-image-from-offer command function
@offer.command(name="remove-image-from-offer")
@click.option(
    '--image-urn',
    type=click.STRING,
    required=True,
    help='Urn for the image to delete'
)
@click.option(
    '--vm-images-key',
    type=click.STRING,
    help='SSH keys to be allowed to access the image'
)
@add_options(shared_options)
@click.pass_context
def remove_image_from_offer(
    context,
    image_urn,
    vm_images_key,
    **kwargs
):
    """
    Removes an image from a cloud partner offer
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
        az_img.remove_image_from_offer(
            image_urn,
            vm_images_key=vm_images_key
        )

    except Exception as e:
        echo_style(
            'Unable to remove image from cloud partner offer.',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)
