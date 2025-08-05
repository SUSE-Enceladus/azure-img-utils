# -*- coding: utf-8 -*-

"""Azure gallery utils cli module."""

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

import click
import logging
import sys

from azure_img_utils.cli.cli_utils import (
    add_options,
    get_config,
    process_shared_options,
    shared_options,
    echo_style,
    save_json_to_file
)
from azure_img_utils.azure_container import AzureContainer


# -----------------------------------------------------------------------------
# Container offer commands function
@click.group(name="cloud-partner-container-offer")
def container_offer():
    """
    Commands for cloud partner offer management for container based offers.
    """


# -----------------------------------------------------------------------------
# cloud partner offer get-offer-document command function
@container_offer.command(name="get-offer-document")
@click.option(
    '--offer-id',
    type=click.STRING,
    required=True,
    help='Id of the cloud partner container offer offer to get.'
)
@click.option(
    '--offer-document-file',
    type=click.Path(),
    required=True,
    help='File where the offer document is saved as json.'
)
@click.option(
    '--retries',
    type=click.INT,
    default=0,
    help='Number of retries in case of error in doc retrieval.'
)
@click.option(
    '--target-type',
    type=click.STRING,
    default='draft',
    help='The document type to retrieve. Valid types: draft, preview, live.'
)
@add_options(shared_options)
@click.pass_context
def get_container_offer_document(
    context,
    offer_id,
    offer_document_file,
    target_type,
    retries,
    **kwargs
):
    """
    Downloads an offer json document to local file
    """

    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('azure_img_utils')
    logger.setLevel(config_data.log_level)

    try:
        az_img = AzureContainer(
            credentials_file=config_data.credentials_file,
            log_level=config_data.log_level,
            log_callback=logger
        )
        doc = az_img.get_offer_doc(
            offer_id,
            target_type,
            retries=retries
        )

        save_json_to_file(doc, offer_document_file)
    except Exception as e:
        echo_style(
            'Unable to download cloud partner offer document.',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(e), config_data.no_color, fg='red')
        sys.exit(1)
