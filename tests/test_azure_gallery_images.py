import pytest

from unittest.mock import MagicMock

from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute._configuration import (
    ComputeManagementClientConfiguration
)

from azure_img_utils.azure_image import AzureImage
from azure_img_utils.exceptions import AzureImgUtilsException


class Image(object):
    def as_dict(self):
        return {
            'id': '123',
            'name': '2022.02.02',
            'type': 'Microsoft.Compute/galleries/images/versions',
            'location': 'westus2'
        }


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
        _config = MagicMock(spec=ComputeManagementClientConfiguration)
        _config.subscription_id = '123456789'
        self.cc._config = _config
        self.cc.gallery_image_versions.get.return_value = Image()
        self.image._compute_client = self.cc

    def test_gallery_image_version_exists(self):
        assert self.image.gallery_image_version_exists(
            'gallery1',
            'galleryimage1',
            '2022.02.02'
        )

    def test_get_gallery_image_version(self):
        image = self.image.get_gallery_image_version(
            'gallery1',
            'galleryimage1',
            '2022.02.02'
        )
        assert image['name'] == '2022.02.02'

    def test_delete_gallery_image_version(self):
        self.cc.gallery_image_versions.begin_delete.return_value = AsyncOperation()  # noqa
        self.image.delete_gallery_image_version(
            'gallery1',
            'galleryimage1',
            '2022.02.02'
        )
        assert self.cc.gallery_image_versions.begin_delete.call_count == 1

    def test_create_gallery_image_version(self):
        msg = 'Gallery image version already exists. To force deletion and ' \
              're-create the image set "force_replace_image" to True.'

        with pytest.raises(AzureImgUtilsException, match=msg):
            self.image.create_gallery_image_version(
                'image_123.vhd',
                'gallery1',
                'galleryimage1',
                '2022.02.02',
                'westus2',
            )

        image_name = self.image.create_gallery_image_version(
            'image_123.vhd',
            'gallery1',
            'galleryimage1',
            '2022.02.02',
            'westus2',
            force_replace_image=True
        )

        assert image_name == 'galleryimage1'
