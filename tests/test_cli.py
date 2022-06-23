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

    def my_side_eff(*args, **kwargs):
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
# parameter precedence tests
@patch('azure_img_utils.cli.blob.AzureImage')
def test_parameter_precedence(
    azure_image_mock
):
    """Confirm parameter precedence is OK
    """

    instance = MagicMock()
    instance.image_blob_exists.return_value = True

    def my_side_eff(*args, **kwargs):
        print("container->" + kwargs["container"])
        print("storage_account->" + kwargs["storage_account"])
        print("resource_group->" + kwargs["resource_group"])
        return instance

    azure_image_mock.side_effect = my_side_eff

    args = [
        'blob', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--config-dir', './tests',
        '--profile', 'default2',
        '--container', 'myContainer',
        '--blob-name', 'myBlobName',
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert "true" in result.output
    assert "container->myContainer" in result.output
    assert "resource_group->my_resource_group" in result.output
    assert "storage_account->my_storage_account" in result.output


# -------------------------------------------------
# unknown keyword in config file
@patch('azure_img_utils.cli.blob.AzureImage')
def test_unknown_keyword_in_config(azure_image_mock):
    """Confirm unknown keyword in config is handled ok"""
    image_class = MagicMock()
    image_class.image_blob_exists.return_value = False
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--profile', 'unknown_keyword',
        '--config-dir', 'tests',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert 'Found unknown keyword in config file' in result.output


# -------------------------------------------------
# blob exists
@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_exists_ok(azure_image_mock):
    """Confirm blob exists is ok"""
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
def test_blob_exists_ok2(azure_image_mock):
    """Confirm blob exists is ok"""
    image_class = MagicMock()
    image_class.image_blob_exists.return_value = True
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
    assert 'true' in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_exists_nok_blobname_missing(azure_image_mock):
    """blob exists test with --blob-name missing"""
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
def test_blob_exists_exception(azure_image_mock):
    """Confirm if exception handling is ok"""
    image_class = MagicMock()

    def my_side_eff(*args, **kwargs):
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
    """Confirm blob upload is ok"""
    image_class = MagicMock()
    image_class.upload_image_blob.return_value = 'myBlobName'
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'upload',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--blob-name', 'myBlobName',
        '--container', 'myContainer',
        '--max-attempts', '3',
        '--image-file', 'tests/image.raw',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert 'blob myBlobName uploaded' in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_upload_nok_blobname_missing(azure_image_mock):
    """blob upload test with --blob-name missing"""
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
def test_blob_upload_nok_filename_missing(azure_image_mock):
    """blob upload test with --file-name missing"""
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
    """blob upload test with --file-name wrong"""
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

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
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
    """Confirm blob delete is ok"""
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
def test_blob_delete_ok2(azure_image_mock):
    """Confirm blob delete is ok"""
    image_class = MagicMock()
    image_class.delete_storage_blob.return_value = False
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
    assert 'blob myBlobName not found' in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_delete_ok_confirmation(azure_image_mock):
    """Confirm blob delete is ok with confirmation"""
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
    """Confirm blob delete is ok with confirmation"""
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
def test_blob_delete_nok_blobname_missing(azure_image_mock):
    """blob delete test with --blob-name missing"""
    image_class = MagicMock()
    image_class.delete_storage_blob.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'blob', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--container', 'myContainer',
        '--no-color',
        '--yes'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--blob-name'" in result.output


@patch('azure_img_utils.cli.blob.AzureImage')
def test_blob_delete_exception(azure_image_mock):
    """Confirm if exception handling is ok"""
    image_class = MagicMock()

    def my_side_eff(*args, **kwargs):
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


# -------------------------------------------------
# image exists
@patch('azure_img_utils.cli.image.AzureImage')
def test_image_exists_ok_false(azure_image_mock):
    """Confirm image exists is ok"""
    image_class = MagicMock()
    image_class.image_exists.return_value = False
    azure_image_mock.return_value = image_class

    args = [
        'image', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--image-name', 'myBlobName',
        '--container', 'myContainer',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert 'false' in result.output


@patch('azure_img_utils.cli.image.AzureImage')
def test_image_exists_ok_true(azure_image_mock):
    """Confirm image exists is ok"""
    image_class = MagicMock()
    image_class.image_blob_exists.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'image', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--storage-account', 'myStorageAccount',
        '--image-name', 'myBlobName',
        '--container', 'myContainer',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert 'true' in result.output


@patch('azure_img_utils.cli.image.AzureImage')
def test_image_exists_nok_image_name_missing(azure_image_mock):
    """image exists test with exception"""
    image_class = MagicMock()
    image_class.image_blob_exists.return_value = False
    azure_image_mock.return_value = image_class

    args = [
        'image', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--image-name'" in result.output


@patch('azure_img_utils.cli.image.AzureImage')
def test_image_exists_nok_exc(azure_image_mock):
    """image exists test with some exception"""

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.image_exists.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'image', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--image-name', 'my_image_name',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert "myException" in result.output


# -------------------------------------------------
# image create
@patch('azure_img_utils.cli.image.AzureImage')
def test_image_create_ok(azure_image_mock):
    """Confirm image create is ok"""
    image_class = MagicMock()
    image_class.create_compute_image.return_value = 'myImageName'
    azure_image_mock.return_value = image_class

    args = [
        'image', 'create',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--image-name', 'myImageName',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert 'image myImageName created' in result.output


@patch('azure_img_utils.cli.image.AzureImage')
def test_image_create_nok_blobname_missing(azure_image_mock):
    """blob upload test with --blob-name missing"""
    image_class = MagicMock()
    image_class.create_compute_image.return_value = 'myImageName'
    azure_image_mock.return_value = image_class

    args = [
        'image', 'create',
        '--credentials-file', 'tests/creds.json',
        '--image-name', 'myImageName',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--blob-name'" in result.output


@patch('azure_img_utils.cli.image.AzureImage')
def test_image_create_nok_imagename_missing(azure_image_mock):
    """blob upload test with --image-name missing"""
    image_class = MagicMock()
    image_class.create_compute_image.return_value = 'myImageName'
    azure_image_mock.return_value = image_class

    args = [
        'image', 'create',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--image-name'" in result.output


@patch('azure_img_utils.cli.image.AzureImage')
def test_image_create_exception(azure_image_mock):
    """Confirm if exception handling is ok"""

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.create_compute_image.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'image', 'create',
        '--credentials-file', 'tests/creds.json',
        '--config-dir', 'tests/',
        '--profile', 'default2',
        '--blob-name', 'myBlobName',
        '--image-name', 'myImageName',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert 'Unable to create image' in result.output
    assert 'myException' in result.output


# -------------------------------------------------
# image delete
@patch('azure_img_utils.cli.image.AzureImage')
def test_image_delete_ok(azure_image_mock):
    """Confirm delete is ok"""
    image_class = MagicMock()
    image_class.delete_compute_image.return_value = None
    azure_image_mock.return_value = image_class

    args = [
        'image', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--image-name', 'myImageName',
        '--no-color',
        '--yes',
        '--verbose',
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0


@patch('azure_img_utils.cli.image.AzureImage')
def test_image_delete_ok_confirmation(azure_image_mock):
    """Confirm image delete is ok with confirmation"""
    image_class = MagicMock()
    image_class.delete_compute_image.return_value = None
    azure_image_mock.return_value = image_class

    args = [
        'image', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--image-name', 'myImageName',
        '--no-color',
        '--verbose',
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args, input='y\n')
    assert result.exit_code == 0


@patch('azure_img_utils.cli.image.AzureImage')
def test_image_delete_ok_noconfirmation(azure_image_mock):
    """Confirm image delete is ok answering NO to confirmation"""
    image_class = MagicMock()
    image_class.delete_compute_image.return_value = None
    azure_image_mock.return_value = image_class

    args = [
        'image', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--image-name', 'myImageName',
        '--no-color',
        '--verbose',
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args, input='n\n')
    assert result.exit_code == 1
    assert 'Aborted' in result.output


@patch('azure_img_utils.cli.image.AzureImage')
def test_image_delete_nok_exception(azure_image_mock):
    """image delete test with some exception"""

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.delete_compute_image.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'image', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--image-name', 'myImageName',
        '--no-color',
        '--yes',
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert "myException" in result.output


def test_image_delete_image_name_missing():
    """image delete without --image-name parameter"""

    args = [
        'image', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--yes',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--image-name'" in result.output


# -------------------------------------------------
# gallery image version exists
@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_exists_ok_false(azure_image_mock):
    """Confirm gallery image version exists is ok. Image does not exist."""
    image_class = MagicMock()
    image_class.gallery_image_version_exists.return_value = False
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--gallery-image-name', 'myImageName',
        '--gallery-name', 'myGalleryName',
        '--gallery-image-version', '0.0.1',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert 'false' in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_exists_ok_true(azure_image_mock):
    """Confirm gallery image version exists is ok. Image exists."""
    image_class = MagicMock()
    image_class.gallery_image_version_exists.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--gallery-image-name', 'myImageName',
        '--gallery-name', 'myGalleryName',
        '--gallery-image-version', '0.0.1',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert 'true' in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_exists_nok_image_name_missing(azure_image_mock):
    """Gallery image version exists test with exception. No
     --gallery-image-name provided.
    """
    image_class = MagicMock()
    image_class.gallery_image_version_exists.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--gallery-name', 'myGalleryName',
        '--gallery-image-version', '0.0.1',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--gallery-image-name'" in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_exists_nok_gallery_name_missing(
    azure_image_mock
):
    """Gallery image version exists test with exception. No
     --gallery-name provided
     """
    image_class = MagicMock()
    image_class.gallery_image_version_exists.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--gallery-image-name', 'myImageName',
        '--gallery-image-version', '0.0.1',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--gallery-name'" in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_exists_nok_image_version_missing(
    azure_image_mock
):
    """Gallery image version exists test with exception. No
     --gallery-image-version provided
    """
    image_class = MagicMock()
    image_class.gallery_image_version_exists.return_value = True
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--gallery-image-name', 'myImageName',
        '--gallery-name', 'myGalleryName',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--gallery-image-version'" in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_exists_nok_exc(azure_image_mock):
    """Gallery image version exists test with some exception"""

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.gallery_image_version_exists.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'exists',
        '--credentials-file', 'tests/creds.json',
        '--gallery-image-name', 'myImageName',
        '--gallery-name', 'myGalleryName',
        '--gallery-image-version', '0.0.1',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert "myException" in result.output


# -------------------------------------------------
# gallery image version create
@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_create_ok(azure_image_mock):
    """Confirm gallery image version create is ok."""
    image_class = MagicMock()
    image_class.create_gallery_image_version.return_value = 'myImageName'
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'create',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--gallery-name', 'myGalleryName',
        '--gallery-image-name', 'myImageName',
        '--gallery-image-version', '0.0.1',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    print("RES->"+result.output)
    assert result.exit_code == 0
    assert 'gallery image version myImageName created' in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_create_image_name_missing(azure_image_mock):
    """Gallery image version create test. No --gallery-image-name provided"""
    image_class = MagicMock()
    image_class.create_gallery_image_version.return_value = 'myImageName'
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'create',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--gallery-name', 'myGalleryName',
        '--gallery-image-version', '0.0.1',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--gallery-image-name'" in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_create_blob_name_missing(azure_image_mock):
    """Gallery image version create test. No --blob-name provided"""
    image_class = MagicMock()
    image_class.create_gallery_image_version.return_value = 'myImageName'
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'create',
        '--credentials-file', 'tests/creds.json',
        '--gallery-name', 'myGalleryName',
        '--gallery-image-name', 'myImageName',
        '--gallery-image-version', '0.0.1',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--blob-name'" in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_create_gallery_name_missing(azure_image_mock):
    """Gallery image version create test. No --gallery-name provided"""
    image_class = MagicMock()
    image_class.create_gallery_image_version.return_value = 'myImageName'
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'create',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--gallery-image-name', 'myImageName',
        '--gallery-image-version', '0.0.1',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--gallery-name'" in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_create_image_version_missing(azure_image_mock):
    """Gallery image version create test. No --gallery-image-version
     provided
    """
    image_class = MagicMock()
    image_class.create_gallery_image_version.return_value = 'myImageName'
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'create',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--gallery-image-name', 'myImageName',
        '--gallery-name', 'myGalleryName',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--gallery-image-version'" in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_create_nok_exc(azure_image_mock):
    """Gallery image version create test with some exception"""

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.create_gallery_image_version.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'create',
        '--credentials-file', 'tests/creds.json',
        '--gallery-image-name', 'myImageName',
        '--blob-name', 'myBlobName',
        '--gallery-name', 'myGalleryName',
        '--gallery-image-version', '0.0.1',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert "myException" in result.output


# -------------------------------------------------
# gallery image version delete
@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_delete_ok(azure_image_mock):
    """Confirm gallery image version delete is ok."""
    image_class = MagicMock()
    image_class.delete_gallery_image_version.return_value = None
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--gallery-image-name', 'myImageName',
        '--gallery-name', 'myGalleryName',
        '--gallery-image-version', '0.0.1',
        '--yes',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_delete_nok_image_name_missing(azure_image_mock):
    """Gallery image version delete test. No --gallery-image-name provided"""
    image_class = MagicMock()
    image_class.delete_gallery_image_version.return_value = None
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--gallery-name', 'myGalleryName',
        '--gallery-image-version', '0.0.1',
        '--yes',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--gallery-image-name'" in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_delete_nok_gallery_name_missing(
    azure_image_mock
):
    """Gallery image version delete test. No --gallery-name provided"""
    image_class = MagicMock()
    image_class.delete_gallery_image_version.return_value = None
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--gallery-image-name', 'myImageName',
        '--gallery-image-version', '0.0.1',
        '--yes',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--gallery-name'" in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_delete_nok_image_version_missing(
    azure_image_mock
):
    """Gallery image version delete test. No --gallery-image-version provided
    """
    image_class = MagicMock()
    image_class.delete_gallery_image_version.return_value = None
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--gallery-image-name', 'myImageName',
        '--gallery-name', 'myGalleryName',
        '--yes',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--gallery-image-version'" in result.output


@patch('azure_img_utils.cli.gallery_image_version.AzureImage')
def test_gallery_image_version_delete_nok_exc(azure_image_mock):
    """Gallery image version delete test with some exception"""

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.delete_gallery_image_version.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'gallery-image-version', 'delete',
        '--credentials-file', 'tests/creds.json',
        '--gallery-image-name', 'myImageName',
        '--gallery-name', 'myGalleryName',
        '--gallery-image-version', '0.0.1',
        '--yes',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert "myException" in result.output
    assert "Unable to delete gallery image version" in result.output


# -------------------------------------------------
# cloud-partner-offer publish tests
@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_publish_ok(azure_image_mock):
    """Confirm cloud partner offer publish is ok."""

    myUrl = "https://mytest.com/locationURL"
    image_class = MagicMock()
    image_class.publish_offer.return_value = myUrl
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'publish',
        '--credentials-file', 'tests/creds.json',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--notification-emails', '1@mail.com,2@mail.com',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert "Published cloud partner offer." in result.output
    assert "Operation URI: " + myUrl in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_publish_offer_id_not_provided(
    azure_image_mock
):
    """Cloud partner offer publish nok. --offer-id not provided"""

    myUrl = "https://mytest.com/locationURL"
    image_class = MagicMock()
    image_class.publish_offer.return_value = myUrl
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'publish',
        '--credentials-file', 'tests/creds.json',
        '--publisher-id', 'myPublisherId',
        '--notification-emails', '1@mail.com,2@mail.com',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--offer-id'" in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_publish_exc(azure_image_mock):
    """Confirm cloud partner offer publish exception handling is ok."""

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.publish_offer.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'publish',
        '--credentials-file', 'tests/creds.json',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--notification-emails', '1@mail.com,2@mail.com',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert "Unable to publish cloud partner offer" in result.output
    assert "myException" in result.output


# -------------------------------------------------
# cloud-partner-offer publish tests
@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_go_live_ok(azure_image_mock):
    """Confirm cloud partner offer go-live is ok."""

    myUrl = "https://mytest.com/locationURL"
    image_class = MagicMock()
    image_class.go_live_with_offer.return_value = myUrl
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'go-live',
        '--credentials-file', 'tests/creds.json',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0
    assert "Cloud partner offer set as go-live." in result.output
    assert "Operation URI: " + myUrl in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_go_live_offer_id_not_provided(
    azure_image_mock
):
    """Cloud partner offer go-live nok. --offer-id not provided"""

    myUrl = "https://mytest.com/locationURL"
    image_class = MagicMock()
    image_class.go_live_with_offer.return_value = myUrl
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'go-live',
        '--credentials-file', 'tests/creds.json',
        '--publisher-id', 'myPublisherId',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--offer-id'" in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_go_live_exc(azure_image_mock):
    """Confirm cloud partner offer go_live exception handling is ok."""

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.go_live_with_offer.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'go-live',
        '--credentials-file', 'tests/creds.json',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert "Unable to set cloud partner offer as go-live." in result.output
    assert "myException" in result.output


# -------------------------------------------------
# cloud-partner-offer upload-offer-document tests
@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_upload_doc_ok(azure_image_mock):
    """Confirm cloud partner offer upload-offer-document is ok."""

    image_class = MagicMock()
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'upload-offer-document',
        '--credentials-file', 'tests/creds.json',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--offer-document-file', 'tests/creds.json',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_upload_doc_offer_id_not_provided(
    azure_image_mock
):
    """Cloud partner offer upload-offer-document nok.
    --offer-id not provided
    """

    image_class = MagicMock()
    image_class.upload_offer_doc.return_value = None
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'upload-offer-document',
        '--credentials-file', 'tests/creds.json',
        '--publisher-id', 'myPublisherId',
        '--offer-document-file', 'tests/creds.json',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--offer-id'" in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_upload_doc_document_file_not_provided(
    azure_image_mock
):
    """Cloud partner offer upload-offer-document nok.
    --offer-document-file not provided
    """

    image_class = MagicMock()
    image_class.upload_offer_doc.return_value = None
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'upload-offer-document',
        '--credentials-file', 'tests/creds.json',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    print("Result"+result.output)
    assert result.exit_code == 2
    assert "Missing option '--offer-document-file'" in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_upload_doc_exc(azure_image_mock):
    """Cloud partner offer upload-offer-document nok.
    Exception
    """

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.upload_offer_doc.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'upload-offer-document',
        '--credentials-file', 'tests/creds.json',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--offer-document-file', 'tests/creds.json',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    print("Result"+result.output)
    assert result.exit_code == 1
    assert "Unable to upload cloud partner offer document." in result.output
    assert "myException" in result.output


# -------------------------------------------------
# cloud-partner-offer add-image-to-offer tests
@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_add_image_ok(azure_image_mock):
    """Confirm cloud partner offer add-image-to-offer is ok."""

    image_class = MagicMock()
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'add-image-to-offer',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--image-name', 'myImageName',
        '--image-description', 'my image description',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--label', 'myLabel',
        '--sku', 'mySku',
        '--blob-url', 'myBlobUrl',
        '--generation-id', 'V1',
        '--generation-suffix', 'mySuffix',
        '--vm-images-key', 'myKey',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_add_image_nok_blob_name_missing(azure_image_mock):
    """Confirm cloud partner offer add-image-to-offer handles params well.
    --blob-name missing"""

    image_class = MagicMock()
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'add-image-to-offer',
        '--credentials-file', 'tests/creds.json',
        '--image-name', 'myImageName',
        '--image-description', 'my image description',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--label', 'myLabel',
        '--sku', 'mySku',
        '--blob-url', 'myBlobUrl',
        '--generation-id', 'V1',
        '--generation-suffix', 'mySuffix',
        '--vm-images-key', 'myKey',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--blob-name'" in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_add_image_nok_image_name_missing(
    azure_image_mock
):
    """Confirm cloud partner offer add-image-to-offer handles params well.
    --image-name missing"""

    image_class = MagicMock()
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'add-image-to-offer',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--image-description', 'my image description',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--label', 'myLabel',
        '--sku', 'mySku',
        '--blob-url', 'myBlobUrl',
        '--generation-id', 'V1',
        '--generation-suffix', 'mySuffix',
        '--vm-images-key', 'myKey',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--image-name'" in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_add_image_nok_image_description_missing(
    azure_image_mock
):
    """Confirm cloud partner offer add-image-to-offer handles params well.
    --image-description missing"""

    image_class = MagicMock()
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'add-image-to-offer',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--image-name', 'myImageName',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--label', 'myLabel',
        '--sku', 'mySku',
        '--blob-url', 'myBlobUrl',
        '--generation-id', 'V1',
        '--generation-suffix', 'mySuffix',
        '--vm-images-key', 'myKey',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--image-description'" in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_add_image_nok_offer_id_missing(
    azure_image_mock
):
    """Confirm cloud partner offer add-image-to-offer handles params well.
    --offer-id missing"""

    image_class = MagicMock()
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'add-image-to-offer',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--image-name', 'myImageName',
        '--image-description', 'my image description',
        '--publisher-id', 'myPublisherId',
        '--label', 'myLabel',
        '--sku', 'mySku',
        '--blob-url', 'myBlobUrl',
        '--generation-id', 'V1',
        '--generation-suffix', 'mySuffix',
        '--vm-images-key', 'myKey',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--offer-id'" in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_add_image_nok_label_missing(
    azure_image_mock
):
    """Confirm cloud partner offer add-image-to-offer handles params well.
    --label missing"""

    image_class = MagicMock()
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'add-image-to-offer',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--image-name', 'myImageName',
        '--image-description', 'my image description',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--sku', 'mySku',
        '--blob-url', 'myBlobUrl',
        '--generation-id', 'V1',
        '--generation-suffix', 'mySuffix',
        '--vm-images-key', 'myKey',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--label'" in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_add_image_nok_sku_missing(
    azure_image_mock
):
    """Confirm cloud partner offer add-image-to-offer handles params well.
    --sku missing"""

    image_class = MagicMock()
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'add-image-to-offer',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--image-name', 'myImageName',
        '--image-description', 'my image description',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--label', 'myLabel',
        '--blob-url', 'myBlobUrl',
        '--generation-id', 'V1',
        '--generation-suffix', 'mySuffix',
        '--vm-images-key', 'myKey',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--sku'" in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_add_image_nok_exc(
    azure_image_mock
):
    """Confirm cloud partner offer add-image-to-offer handles params well.
    exception"""

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.add_image_to_offer.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'add-image-to-offer',
        '--credentials-file', 'tests/creds.json',
        '--blob-name', 'myBlobName',
        '--image-name', 'myImageName',
        '--image-description', 'my image description',
        '--offer-id', 'myOfferId',
        '--publisher-id', 'myPublisherId',
        '--label', 'myLabel',
        '--sku', 'mySku',
        '--blob-url', 'myBlobUrl',
        '--generation-id', 'V1',
        '--generation-suffix', 'mySuffix',
        '--vm-images-key', 'myKey',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert "Unable to add image to cloud partner offer." in result.output
    assert "myException" in result.output


# -------------------------------------------------
# cloud-partner-offer remove-image-from-offer tests
@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_remove_image_ok(azure_image_mock):
    """Confirm cloud partner offer remove-image-from-offer is ok."""

    image_class = MagicMock()
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'remove-image-from-offer',
        '--credentials-file', 'tests/creds.json',
        '--image-urn', 'myImageUrn',
        '--vm-images-key', 'myKey',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 0


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_remove_image_nok_image_urn_missing(
    azure_image_mock
):
    """Confirm cloud partner offer remove-image-from-offer handles
    params ok. --image-urn missing"""

    image_class = MagicMock()
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'remove-image-from-offer',
        '--credentials-file', 'tests/creds.json',
        '--vm-images-key', 'myKey',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 2
    assert "Missing option '--image-urn'" in result.output


@patch('azure_img_utils.cli.offer.AzureImage')
def test_cloud_partner_offer_remove_image_nok_exc(azure_image_mock):
    """Confirm cloud partner offer remove-image-from-offer handles
    exceptions ok."""

    def my_side_eff(*args, **kwargs):
        raise Exception('myException')

    image_class = MagicMock()
    image_class.remove_image_from_offer.side_effect = my_side_eff
    azure_image_mock.return_value = image_class

    args = [
        'cloud-partner-offer', 'remove-image-from-offer',
        '--credentials-file', 'tests/creds.json',
        '--image-urn', 'myImageUrn',
        '--vm-images-key', 'myKey',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(az_img_utils, args)
    assert result.exit_code == 1
    assert "myException" in result.output
    assert "Unable to remove image from cloud partner offer." in result.output
