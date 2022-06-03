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
        '--sas-token',
        type=click.STRING,
        help='The Sas token used for the requests.'
    ),
    click.option(
        '--client-id',
        type=click.STRING,
        help='The client id used for the requests.'
    ),
    click.option(
        '--client-secret',
        type=click.STRING,
        help='The client secret used for the requests.'
    ),
    click.option(
        '--subscription-id',
        type=click.STRING,
        help='The subscription id used for the requests.'
    ),
    click.option(
        '--tenant-id',
        type=click.STRING,
        help='The tenant id used for the requests.'
    ),
    click.option(
        '--active-directory-url',
        type=click.STRING,
        help='The URL for the active directory endpoint.'
    ),
    click.option(
        '--resource-manager-url',
        type=click.STRING,
        help='The URL for the resource manager endpoint.'
    ),
    click.option(
        '--active-directory-graph-res-url',
        type=click.STRING,
        help='The URL for the active directory graph resource id endpoint.'
    ),
    click.option(
        '--sql-management-url',
        type=click.STRING,
        help='The URL for the sql management endpoint.'
    ),
    click.option(
        '--gallery-url',
        type=click.STRING,
        help='The URL for the gallery endpoint.'
    ),
    click.option(
        '--management-url',
        type=click.STRING,
        help='The URL for the management endpoint.'
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
    context_obj['active_directory_graph_res_url'] = \
        kwargs.get('active_directory_graph_res_url')
    context_obj['active_directory_url'] = kwargs.get('active_directory_url')
    context_obj['client_id'] = kwargs.get('client_id')
    context_obj['client_secret'] = kwargs.get('client_secret')
    context_obj['config_dir'] = kwargs.get('config_dir')
    context_obj['credentials_file'] = kwargs.get('credentials_file')
    context_obj['gallery_url'] = kwargs.get('gallery_url')
    context_obj['log_level'] = kwargs.get('log_level')
    context_obj['management_url'] = kwargs.get('management_url')
    context_obj['no_color'] = kwargs.get('no_color')
    context_obj['profile'] = kwargs.get('profile')
    context_obj['region'] = kwargs.get('region')
    context_obj['resource_group'] = kwargs.get('resource_group')
    context_obj['resource_manager_url'] = kwargs.get('resource_manager_url')
    context_obj['sas_token'] = kwargs.get('sas_token')
    context_obj['subscription_id'] = kwargs.get('subscription_id')
    context_obj['sql_management_url'] = kwargs.get('sql_management_url')
    context_obj['tenant_id'] = kwargs.get('tenant_id')


# -----------------------------------------------------------------------------
# Check required config provided
def check_required_config_provided(config_data):
    check_authentication_data_provided(config_data)


# -----------------------------------------------------------------------------
# Check required arguments for authentication provided
def check_authentication_data_provided(config_data):
    if config_data.sas_token:
        return
    elif (
        config_data.tenant_id and
        config_data.client_id and
        config_data.client_secret and
        config_data.subscription_id and
        config_data.resource_group
    ):
        return
    elif (
        config_data.credentials_file and
        config_data.resource_group
    ):
        return
    else:
        msg = 'Required authentication data not provided. '
        msg += 'Sas-token or credentials/credentials file and '
        msg += 'resource_group is required to authenticate any operation. '
        echo_style(
            msg,
            config_data.no_color,
            fg='red'
        )
        sys.exit(1)
    return


# -----------------------------------------------------------------------------
# Build credentials from configuration data
def get_credentials_from_configuration_data(config_data):
    credentials = {}
    credentials['clientId'] = config_data.client_id
    credentials['clientSecret'] = config_data.client_secret
    credentials['subscriptionId'] = config_data.subscription_id
    credentials['tenantId'] = config_data.tenant_id
    credentials['activeDirectoryEndpointUrl'] = \
        config_data.active_directory_url
    credentials['resourceManagerEndpointUrl'] = \
        config_data.resource_manager_url
    credentials['activeDirectoryGraphResourceId'] = \
        config_data.active_directory_graph_res_url
    credentials['sqlManagementEndpointUrl'] = \
        config_data.sql_management_url
    credentials['galleryEndpointUrl'] = \
        config_data.gallery_url
    credentials['managementEndpointUrl'] = \
        config_data.management_url
    return credentials
