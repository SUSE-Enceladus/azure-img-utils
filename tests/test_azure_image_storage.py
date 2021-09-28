import pytest

from unittest.mock import MagicMock

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient
from azure.storage.blob._container_client import ContainerClient
from azure.storage.blob._blob_client import BlobClient

from azure_img_utils.azure_image import AzureImage
from azure_img_utils.exceptions import (
    AzureImgUtilsException,
    AzureImgUtilsStorageException
)


class TestAzureImageStorage(object):
    def setup_class(self):
        self.image = AzureImage(
            container='images',
            storage_account='account',
            credentials_file='tests/creds.json',
            resource_group='group'
        )

        # Mock blob service client
        self.bsc = MagicMock(spec=BlobServiceClient)
        cc = MagicMock(spec=ContainerClient)
        self.bc = MagicMock(spec=BlobClient)

        cc.get_blob_client.return_value = self.bc
        self.bsc.get_container_client.return_value = cc
        self.image._blob_service_client = self.bsc

    def test_blob_exists(self):
        self.bc.exists.return_value = True
        assert self.image.image_blob_exists('blob123')

    def test_delete_blob_exception(self):
        self.bc.delete_blob.side_effect = ResourceNotFoundError('Not found!')
        assert self.image.delete_storage_blob('not_a_blob.txt') is False

        self.bc.delete_blob.side_effect = None
        assert self.image.delete_storage_blob('blob.txt')

    def test_upload_blob(self):
        self.bc.exists.return_value = True

        # Blob exists and no force replace
        with pytest.raises(Exception):
            self.image.upload_image_blob('tests/image.raw')

        blob = self.image.upload_image_blob(
            'tests/image.raw',
            force_replace_image=True,
            max_retry_attempts=5,
            max_workers=10
        )

        assert blob == 'image.raw'

    def test_upload_blob_exception(self):
        self.bc.exists.return_value = False

        # Blob upload file not found

        msg = 'Image file tests/not_a_image.raw not found. ' \
              'Ensure the path to the file is correct.'

        with pytest.raises(AzureImgUtilsException, match=msg):
            self.image.upload_image_blob('tests/not_a_image.raw')

        self.bc.upload_blob.side_effect = Exception('Permission denied')

        # Blob upload fails

        msg = 'Unable to upload tests/image.raw: Permission denied'

        with pytest.raises(AzureImgUtilsStorageException, match=msg):
            self.image.upload_image_blob('tests/image.raw')
