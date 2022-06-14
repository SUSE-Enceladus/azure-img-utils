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
# Offer commands function
@click.group(name="cloud-partner-offer")
def offer():
    """
    Commands for cloud partner offer management.
    """


# -----------------------------------------------------------------------------
# status command function
@offer.command()
@click.option(
    '--offer-id',
    type=click.STRING,
    required=True,
    help='Id of the cloud partner offer to publish.'
)
@click.option(
    '--publisher-id',
    type=click.STRING,
    required=True,
    help='Id of the publisher to use for the publication.'

)
@click.option(
    '--notification-emails',
    type=click.STRING,
    required=True,
    help='Comma separated list of emails to be notified.'
         'For migrated offers this param is ignored and the notifications'
         ' will be sent to the email address set as Seller contact info '
         'section of your Account settings in Partner Center'
)
@add_options(shared_options)
@click.pass_context
def publish(
    context,
    offer_id,
    publisher_id,
    notification_emails,
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
        offer_url = az_img.publish_cloud_partner_offer(
            az_img.access_token,
            offer_id,
            publisher_id,
            notification_emails
        )

        if offer_url:
            echo_style(
                'Published cloud partner offer at ' + offer_url,
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
