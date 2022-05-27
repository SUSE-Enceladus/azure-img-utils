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
    click.echo('In blob!')


@blob.command()
@click.option(
    '--storage-account',
    type=click.STRING,
    required=True,
    help='Storage account for the blobs.'
)
@click.option(
    '--sas-token',
    type=click.STRING,
    required=True,
    help='The Sas token used for the requests.'
)
@click.option(
    '--blob-name',
    type=click.STRING,
    required=True,
    help='Name of the blob to check.'
)
@click.option(
    '--container',
    type=click.STRING,
    required=True,
    help='Container for the blob to check.'
)
@add_options(shared_options)
@click.pass_context
def exists(
    context,
    storage_account,
    sas_token,
    blob_name,
    container,
    **kwargs
):
    """
    Checks if a blob exists for the specified container
    """
    logger = logging.getLogger('azure_img_utils')
    logger.setLevel(kwargs['log_level'])
    try:
        az_img = AzureImage(
            container,
            storage_account,
            None,
            None,
            None,
            sas_token,
            kwargs['log_level'],
            None,
            None
        )
        exists = az_img.image_blob_exists(blob_name)
        if exists:
            echo_style('True', kwargs['no_color'], fg='green')
        else:
            echo_style('False', kwargs['no_color'])

        click.echo("az_img creation looks good!" + str(az_img))
    except Exception as e:
        echo_style(
            'Unable to check blob existence',
            kwargs['no_color'],
            fg='red'
        )
        echo_style(str(e), kwargs['no_color'], fg='red')
        sys.exit(1)
