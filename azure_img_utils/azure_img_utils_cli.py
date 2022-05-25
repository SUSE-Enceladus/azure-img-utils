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


# -----------------------------------------------------------------------------
# Shared options

shared_options = [
    click.option(
        '-C',
        '--config-dir',
        type=click.Path(exists=True),
        help='Azure Image utils config directory to use. Default: '
             '~/.config/azure_img_utils/'
    ),
    click.option(
        '--profile',
        help='The configuration profile to use. Expected to match '
             'a config file in config directory. Example: production, '
             'for ~/.config/azure_img_utils/production.yaml. The default '
             'value is default: ~/.config/azure_img_utils/default.yaml'
    ),
    click.option(
        '--no-color',
        is_flag=True,
        help='Remove ANSI color and styling from output.'
    ),
    click.option(
        '--verbose',
        'log_level',
        flag_value=logging.DEBUG,
        help='Display debug level logging to console.'
    ),
    click.option(
        '--info',
        'log_level',
        flag_value=logging.INFO,
        default=True,
        help='Display logging info to console. (Default)'
    ),
    click.option(
        '--quiet',
        'log_level',
        flag_value=logging.ERROR,
        help='Display only errors to console.'
    ),
    click.option(
        '--subscription-id',
        type=click.STRING,
        help='Id for the azure subscription used for requests.'
    ),
    click.option(
        '--tenant-id',
        type=click.STRING,
        help='Id for the azure tenant used for requests.'
    ),
    click.option(
        '--client-id',
        type=click.STRING,
        help='Id for the azure client used for requests.'
    ),
    click.option(
        '--client-secret',
        type=click.STRING,
        help='Secret for the azure client used for requests.'
    ),
    click.option(
        '--sas-token',
        type=click.STRING,
        help='The Sas token used for the requests.'
    )
]


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options


# -----------------------------------------------------------------------------
# license function
def print_license(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('GPLv3+')
    ctx.exit()


# -----------------------------------------------------------------------------
# Blob commands function
@click.group()
def blob():
    """
    Blob commands.
    """
    click.echo('In blob!')

@click.command()
@click.option(
    '--image-file',
    type=click.Path(exists=True),
    required=True,
    help='Path to qcow2 image.'
)
#@click.option(
#    '--blob-name',
#    type=click.STRING,
#    help='Name to use for blob in the storage bucket. By default '
#         'the filename from image file will be used.'
#)
#@click.option(
#    '--container',
#    type=click.STRING,
#    help='Container that will be used'
#)
#@add_options(shared_options)
@click.pass_context
def exists(
    context,
    image_file
#    blob_name,
#    container,
#    **kwargs
):
    """
    Checks if a blob exists for the specified container
    """
    click.echo('HERE MF')
    click.echo('Here image_file is ' + image_file)


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
def main(context):
    """
    The command line interface provides aliyun image utilities.

    This includes uploading image tarballs and
    creating/publishing/deprecating framework images.
    """
    if context.obj is None:
        context.obj = {}
    click.echo('in main mf')

if __name__ == '__main__':
    blob.add_command(exists)
    main.add_command(blob)
    main()
