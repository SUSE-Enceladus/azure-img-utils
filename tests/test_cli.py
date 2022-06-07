#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Azure img utils cli unit tests."""

# Copyright (c) 2022 SUSE LLC. All rights reserved.
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

from unittest.mock import patch, MagicMock

from azure_img_utils.cli.cli import az_img_utils
from click.testing import CliRunner


def test_client_help():
    """Confirm azure img utils --help is successful."""
    runner = CliRunner()
    result = runner.invoke(az_img_utils, ['--help'])
    assert result.exit_code == 0
    assert 'The command line interface provides ' \
           'azure image utilities' in result.output


def test_print_license():
    runner = CliRunner()
    result = runner.invoke(az_img_utils, ['--license'])
    assert result.exit_code == 0
    assert result.output == 'GPLv3+\n'


# -------------------------------------------------
# authentication parameters tests
@patch('azure_img_utils.cli.blob.AzureImage')
def test_auth_provided_credentials_via_credentials_file(
    azure_image_mock
):
    """Confirm if authentication parameters are provided all is ok.
    """
    image_class = MagicMock()
    image_class.image_blob_exists.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--resource-group', 'myResourceGroup',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0


@patch('azure_img_utils.cli.blob.AzureImage')
def test_auth_provided_credentials_via_credentials_file_exception(
    azure_image_mock
):
    """Confirm if authentication parameters are provided all is ok.
    resource-group missing
    """

    def my_side_eff(*args):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.image_blob_exists.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert "Unable to check blob existence" in result.output
    assert "myException" in result.output


# -------------------------------------------------
# blob exists
@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_exists_ok(azure_image_mock):
    """Confirm image exists is ok"""
    image_class = MagicMock()
    image_class.image_blob_exists.return_value = False
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert 'false' in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_exists_nok_storageaccount_missing(azure_image_mock):
    """image exists test with --storage-account missing"""
    image_class = MagicMock()
    image_class.image_blob_exists.return_value = False
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--storage-account'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_exists_nok_blobname_missing(azure_image_mock):
    """image exists test with --storage-account missing"""
    image_class = MagicMock()
    image_class.image_blob_exists.return_value = False
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--container', 'myContainer',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--blob-name'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_exists_nok_container_missing(azure_image_mock):
    """image exists test with --container missing"""
    image_class = MagicMock()
    image_class.image_blob_exists.return_value = False
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--container'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_exists_exception(azure_image_mock):
    """Confirm if exception handling is ok"""
    image_class = MagicMock()

    def my_side_eff(a1):
        raise Exception('myException')

    image_class.image_blob_exists.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert 'Unable to check blob existence' in result.output
    assert 'myException' in result.output


# -------------------------------------------------
# blob upload
@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_upload_ok(azure_image_mock):
    """Confirm image upload is ok"""
    image_class = MagicMock()
    image_class.upload_image_blob.return_value = 'myBlobName'
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'upload',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--image-file', 'tests/image.raw',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert 'blob myBlobName uploaded' in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_upload_ok2(azure_image_mock):
    """Confirm image upload is ok"""
    image_class = MagicMock()
    image_class.upload_image_blob.return_value = ''
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'upload',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--image-file', 'tests/image.raw',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert 'unable to upload blob' in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_upload_nok_storageaccount_missing(azure_image_mock):
    """image upload test with --storage-account missing"""
    image_class = MagicMock()
    image_class.upload_image_blob.return_value = 'myBlobName'
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'upload',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--image-file', 'tests/image.raw',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--storage-account'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_upload_nok_blobname_missing(azure_image_mock):
    """image upload test with --storage-account missing"""
    image_class = MagicMock()
    image_class.upload_image_blob.return_value = 'myBlobName'
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'upload',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--container', 'myContainer',
        '--image-file', 'tests/image.raw',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--blob-name'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_upload_nok_container_missing(azure_image_mock):
    """image upload test with --container missing"""
    image_class = MagicMock()
    image_class.upload_image_blob.return_value = 'myBlobName'
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'upload',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--image-file', 'tests/image.raw',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--container'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_upload_nok_filename_missing(azure_image_mock):
    """image upload test with --file-name missing"""
    image_class = MagicMock()
    image_class.upload_image_blob.return_value = 'myBlobName'
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'upload',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--image-file'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_upload_nok_filename_notafile(azure_image_mock):
    """image upload test with --file-name wrong"""
    image_class = MagicMock()
    image_class.upload_image_blob.return_value = 'myBlobName'
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'upload',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--image-file', 'tests/nonexistingfile.raw',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Invalid value for '--image-file'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_upload_exception(azure_image_mock):
    """Confirm if exception handling is ok"""
    image_class = MagicMock()

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class.upload_image_blob.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'upload',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--image-file', 'tests/image.raw',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert 'Unable to upload blob' in result.output
    assert 'myException' in result.output


# -------------------------------------------------
# blob delete
@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_delete_ok(azure_image_mock):
    """Confirm image upload is ok"""
    image_class = MagicMock()
    image_class.delete_storage_blob.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--no-color',
        '--yes',
        '--verbose',
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert 'blob deleted' in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_delete_ok_confirmation(azure_image_mock):
    """Confirm image upload is ok with confirmation"""
    image_class = MagicMock()
    image_class.delete_storage_blob.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--no-color',
        '--verbose',
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args, input='y\n')
    assert result.exit_code == 0
    assert 'blob deleted' in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_delete_ok_noconfirmation(azure_image_mock):
    """Confirm image upload is ok with confirmation"""
    image_class = MagicMock()
    image_class.delete_storage_blob.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--no-color',
        '--verbose',
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args, input='n\n')
    assert result.exit_code == 1
    assert 'Aborted' in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_delete_ok2(azure_image_mock):
    """Confirm image upload is ok"""
    image_class = MagicMock()
    image_class.delete_storage_blob.return_value = False
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--yes',
        '--no-color',
        '--verbose',
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert 'blob myBlobName not found' in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_delete_nok_storageaccount_missing(azure_image_mock):
    """image delete test with --storage-account missing"""
    image_class = MagicMock()
    image_class.delete_storage_blob.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--storage-account'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_delete_nok_blobname_missing(azure_image_mock):
    """image delete test with --storage-account missing"""
    image_class = MagicMock()
    image_class.delete_storage_blob.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--container', 'myContainer',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--blob-name'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_delete_nok_container_missing(azure_image_mock):
    """image delete test with --container missing"""
    image_class = MagicMock()
    image_class.delete_storage_blob.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--container'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_delete_exception(azure_image_mock):
    """Confirm if exception handling is ok"""
    image_class = MagicMock()

    def my_side_eff(a1):
        raise Exception('myException')

    image_class.delete_storage_blob.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--yes',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert 'Unable to delete blob' in result.output
    assert 'myException' in result.output
