import pytest

from unittest.mock import MagicMock

from azure.mgmt.compute import ComputeManagementClient

from azure_img_utils.azure_image import AzureImage
from azure_img_utils.exceptions import AzureImgUtilsException


class Image(object):
    def __init__(self, name) -> None:
        self.name = name


class AsyncOperation(object):
    def result(self):
        pass


class TestAzureImageCompute(object):
    def setup_class(self):
        self.image = AzureImage(
            container='images',
            storage_account='account',
            credentials_file='tests/creds.json',
            resource_group='group'
        )

        # Mock compute client
        self.cc = MagicMock(spec=ComputeManagementClient)
        self.cc.images.list.return_value = [Image('test-image-123')]
        self.image._compute_client = self.cc

    def test_image_exists(self):
        assert self.image.image_exists('test-image-123')

    def test_get_compute_image(self):
        image = self.image.get_compute_image('test-image-123')
        assert image.name == 'test-image-123'

    def test_delete_compute_image(self):
        self.cc.images.begin_delete.return_value = AsyncOperation()
        self.image.delete_compute_image('test-image-123')
        assert self.cc.images.begin_delete.call_count == 1

    def test_create_compute_image(self):
        msg = 'Image already exists. To force deletion and re-create ' \
              'the image use "force_replace_image=True".'

        with pytest.raises(AzureImgUtilsException, match=msg):
            self.image.create_compute_image(
                'image_123.raw',
                'test-image-123',
                'southcentralus'
            )

        image_name = self.image.create_compute_image(
            'image_123.raw',
            'test-image-123',
            'southcentralus',
            force_replace_image=True
        )

        assert image_name == 'test-image-123'
