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

from azure_img_utils.cli.image import image


# -----------------------------------------------------------------------------
# license function
def print_license(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('GPLv3+')
    ctx.exit()


# -----------------------------------------------------------------------------
# Main function
@click.group()
@click.version_option()
@click.option(
    '--license',
    is_flag=True,
    callback=print_license,
    expose_value=False,
    is_eager=True,
    help='Show license information.'
)
@click.pass_context
def az_img_utils(context):
    """
    The command line interface provides azure image utilities.

    This includes uploading image tarballs and
    creating/publishing/deprecating framework images.
    """
    if context.obj is None:
        context.obj = {}
    pass


az_img_utils.add_command(image)
