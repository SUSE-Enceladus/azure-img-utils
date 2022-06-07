# -*- coding: utf-8 -*-

"""Azure image utils cli module utils."""

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
import os
import sys
import yaml

from collections import namedtuple, ChainMap


default_config_dir = os.path.expanduser('~/.config/azure_img_utils/')
default_profile = 'default'

config_defaults = {
    'config_dir': default_config_dir,
    'profile': default_profile,
    'log_level': logging.INFO,
    'no_color': False,
    'sas_token': None,
    'tenant_id': None,
    'client_id': None,
    'client_secret': None,
    'subscription_id': None,
    'active_directory_url': 'https://login.microsoftonline.com',
    'resource_manager_url': 'https://management.azure.com/',
    'active_directory_graph_res_url': 'https://graph.windows.net/',
    'sql_management_url': 'https://gallery.azure.com/',
    'gallery_url': 'https://management.core.windows.net:8443/',
    'management_url': 'https://management.core.windows.net/',
    'credentials_file': None,
    'resource_group': None,
}

azure_img_utils_config = namedtuple(
    'az_img_utils_config',
    sorted(config_defaults)
)

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
        '--credentials-file',
        type=click.Path(exists=True),
        help='Azure Image utils credentials file to use.'
    ),
    click.option(
        '--resource-group',
        type=click.STRING,
        help='Azure Image utils resource group to use.'
    ),
    click.option(
        '--region',
        type=click.STRING,
        help='The region to use for the image requests.'
    )
]


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options


# -------------------------------------------------
# Get Config
def get_config(cli_context):
    """
    Process Azure Image utils config.
    Use ChainMap to build config values based on
    command line args, config and defaults.
    """
    config_dir = cli_context['config_dir'] or default_config_dir
    profile = cli_context['profile'] or default_profile

    config_values = {}
    config_file_path = os.path.join(config_dir, profile + '.yaml')

    try:
        with open(config_file_path) as config_file:
            config_values = yaml.safe_load(config_file)
    except FileNotFoundError:
        echo_style(
            f'Config file: {config_file_path} not found. Using default '
            f'configuration values.',
            no_color=True
        )

    cli_values = {
        key: value for key, value in cli_context.items() if value is not None
    }
    data = ChainMap(cli_values, config_values, config_defaults)

    try:
        config_data = azure_img_utils_config(**data)
    except TypeError as e:
        echo_style(
            f'Found unknow keyword in config file {config_file_path}',
            no_color=True
        )
        echo_style(str(e), no_color=True)
        sys.exit(1)
    return config_data


# -----------------------------------------------------------------------------
# Printing options
def echo_style(message, no_color, fg='yellow'):
    """
    Echo stylized output to terminal depending on no_color.
    """
    if no_color:
        click.echo(message)
    else:
        click.secho(message, fg=fg)


# -----------------------------------------------------------------------------
# Process shared options to all commands
def process_shared_options(context_obj, kwargs):
    """
    Update context with values for shared options.
    """
    context_obj['config_dir'] = kwargs.get('config_dir')
    context_obj['credentials_file'] = kwargs.get('credentials_file')
    context_obj['log_level'] = kwargs.get('log_level')
    context_obj['no_color'] = kwargs.get('no_color')
    context_obj['profile'] = kwargs.get('profile')
    context_obj['region'] = kwargs.get('region')
    context_obj['resource_group'] = kwargs.get('resource_group')
