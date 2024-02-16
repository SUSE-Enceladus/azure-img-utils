import pytest

from unittest.mock import MagicMock, patch
from requests import Response

from azure_img_utils.azure_image import AzureImage
from azure_img_utils.cloud_partner import deprecate_image_in_offer_doc

from azure_img_utils.exceptions import (
    AzureImgUtilsException,
    AzureCloudPartnerException
)


class TestAzureCloudPartner(object):
    def setup_class(self):
        self.image = AzureImage(
            container='images',
            storage_account='account',
            credentials_file='tests/creds.json',
            resource_group='group'
        )

        # Mock access token
        self.image._access_token = 'supersecret'

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('azure_img_utils.azure_image.get_durable_id')
    @patch('azure_img_utils.azure_image.process_request')
    def test_get_offer_doc(self, mock_process_request, mock_get_durable_id):
        mock_process_request.return_value = {'offer': 'doc'}
        mock_get_durable_id.return_value = '123456789'
        doc = self.image.get_offer_doc('sles')
        assert doc['offer'] == 'doc'

    @patch.object(AzureImage, 'get_offer_doc')
    def test_offer_exists(self, mock_get_offer):
        exists = self.image.offer_exists('sles')
        assert exists

    @patch.object(AzureImage, 'get_offer_doc')
    def test_offer_not_exists(self, mock_get_offer):
        mock_get_offer.side_effect = AzureCloudPartnerException(
            'Failed'
        )
        exists = self.image.offer_exists('sles')
        assert not exists

    @patch('azure_img_utils.azure_image.process_request')
    def test_upload_offer_doc(self, mock_process_request):
        mock_process_request.return_value = {'offer': 'doc'}
        doc = {'offer': 'doc'}
        self.image.upload_offer_doc('sles', 'suse', doc)

    @patch('azure_img_utils.azure_image.submit_configure_request')
    @patch('azure_img_utils.azure_image.process_request')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_add_image_to_offer(
        self,
        mock_process_request,
        mock_preq2,
        mock_sub_config_req
    ):
        doc = {
            'resources': [
                {
                    '$schema': (
                        'https://schema.mp.microsoft.com/schema/'
                        'virtual-machine-plan-technical-configuration/'
                        '2022-03-01-preview5'
                    ),
                    'plan': 'plan/1234/4321',
                    'skus': [{
                        'imageType': 'x64Gen1',
                        'skuId': 'gen1'
                    }],
                    'vmImageVersions': []
                },
                {
                    '$schema': (
                        'https://schema.mp.microsoft.com/schema/plan/'
                        '2022-03-01-preview2'
                    ),
                    'id': 'plan/1234/4321',
                    'identity': {
                        'externalId': 'gen1'
                    },
                }
            ]
        }

        mock_process_request.return_value = {
            'value': [{
                'id': 'product/123456789'
            }]
        }
        mock_preq2.return_value = doc
        mock_sub_config_req.return_value = '123'

        self.image.add_image_to_offer(
            'blob.vhd',
            'image123-v20111111',
            'sles',
            'gen1',
            blob_url='bloburl'
        )

        plan = doc['resources'][0]['vmImageVersions'][0]

        assert plan['versionNumber'] == '2011.11.11'
        assert plan['lifecycleState'] == 'generallyAvailable'

        msg = 'No Match found for SKU: gen2. ' \
              'Offer doc not updated properly.'

        with pytest.raises(AzureCloudPartnerException, match=msg):
            self.image.add_image_to_offer(
                'blob.vhd',
                'image123-v20111112',
                'sles',
                'gen1',
                blob_url='bloburl',
                generation_id='gen2',
            )

    @patch('azure_img_utils.azure_image.process_request')
    def test_publish_offer(self, mock_process_request):

        response = MagicMock(spec=Response)
        response.headers = {'Location': '/uri/to/operation/id'}
        mock_process_request.return_value = response

        operation = self.image.publish_offer('sles', 'suse', 'test@email.com')
        assert operation == '/uri/to/operation/id'

    def test_publish_offer_exception(self):
        msg = 'notification_emails parameter is required for publish'

        with pytest.raises(AzureImgUtilsException, match=msg):
            self.image.publish_offer('sles', 'suse', '')

    @patch('azure_img_utils.azure_image.process_request')
    def test_go_live_with_offer(self, mock_process_request):
        response = MagicMock(spec=Response)
        response.headers = {'Location': '/uri/to/operation/id'}
        mock_process_request.return_value = response

        operation = self.image.go_live_with_offer('sles', 'suse')
        assert operation == '/uri/to/operation/id'

    @patch('azure_img_utils.azure_image.get_durable_id')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_get_offer_status_publishing(
        self,
        mock_process_request,
        mock_get_durable_id
    ):
        mock_get_durable_id.return_value = '123456789'
        mock_process_request.return_value = {
            'value': [
                {
                    'target': {'targetType': 'preview'},
                    'status': 'running',
                    'result': 'pending'
                }
            ]
        }

        status = self.image.get_offer_status('sles')
        assert status == 'running'

    @patch('azure_img_utils.azure_image.get_durable_id')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_get_offer_status_publish_failed(
        self,
        mock_process_request,
        mock_get_durable_id
    ):
        mock_get_durable_id.return_value = '123456789'
        mock_process_request.return_value = {
            'value': [
                {
                    'target': {'targetType': 'preview'},
                    'status': 'completed',
                    'result': 'failed'
                }
            ]
        }

        status = self.image.get_offer_status('sles')
        assert status == 'failed'

    @patch('azure_img_utils.azure_image.get_durable_id')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_get_offer_status_awaiting_review(
        self,
        mock_process_request,
        mock_get_durable_id
    ):
        mock_get_durable_id.return_value = '123456789'
        mock_process_request.return_value = {
            'value': [
                {
                    'target': {'targetType': 'preview'},
                    'status': 'completed',
                    'result': 'succeeded'
                }
            ]
        }

        status = self.image.get_offer_status('sles')
        assert status == 'waitingForPublisherReview'

    @patch('azure_img_utils.azure_image.get_durable_id')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_get_offer_status_succeeded(
        self,
        mock_process_request,
        mock_get_durable_id
    ):
        mock_get_durable_id.return_value = '123456789'
        mock_process_request.return_value = {
            'value': [
                {
                    'target': {'targetType': 'live'},
                    'status': 'completed',
                    'result': 'succeeded'
                }
            ]
        }

        status = self.image.get_offer_status('sles')
        assert status == 'succeeded'

    @patch('azure_img_utils.azure_image.get_durable_id')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_get_offer_status_first_go_live(
        self,
        mock_process_request,
        mock_get_durable_id
    ):
        mock_get_durable_id.return_value = '123456789'
        mock_process_request.return_value = {
            'value': [
                {
                    'target': {'targetType': 'live'},
                    'status': 'running',
                    'result': 'pending'
                }
            ]
        }

        status = self.image.get_offer_status('sles')
        assert status == 'running'

    @patch('azure_img_utils.azure_image.get_durable_id')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_get_offer_status_going_live(
        self,
        mock_process_request,
        mock_get_durable_id
    ):
        mock_get_durable_id.return_value = '123456789'
        mock_process_request.return_value = {
            'value': [
                {
                    'target': {'targetType': 'live'},
                    'status': 'completed',
                    'result': 'succeeded'
                },
                {
                    'target': {'targetType': 'live'},
                    'status': 'running',
                    'result': 'pending'
                }
            ]
        }

        status = self.image.get_offer_status('sles')
        assert status == 'running'

    @patch('azure_img_utils.azure_image.get_durable_id')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_get_offer_status_go_live_failed(
        self,
        mock_process_request,
        mock_get_durable_id
    ):
        mock_get_durable_id.return_value = '123456789'
        mock_process_request.return_value = {
            'value': [
                {
                    'target': {'targetType': 'live'},
                    'status': 'completed',
                    'result': 'succeeded'
                },
                {
                    'target': {'targetType': 'live'},
                    'status': 'completed',
                    'result': 'failed'
                }
            ]
        }

        status = self.image.get_offer_status('sles')
        assert status == 'failed'

    @patch('azure_img_utils.azure_image.process_request')
    def test_get_operation(self, mock_process_request):
        mock_process_request.return_value = {'operation': 'info'}
        operation = self.image.get_operation('/uri/to/operation/id')
        assert operation['operation'] == 'info'

    def test_deprecate_image_in_offer_1(self):
        doc = {
            'vmImageVersions': [{
                'versionNumber': '2011.11.11',
                'lifecycleState': 'generallyAvailable',
            }]
        }

        my_response = deprecate_image_in_offer_doc(
            doc,
            '2011.11.11',
        )

        image = my_response['vmImageVersions'][0]

        assert image['lifecycleState'] == 'deprecated'

    def test_deprecate_image_in_offer_4(self):
        doc = {
            'vmImageVersions': []
        }

        msg = 'No Match found for the image version: 2011.11.11. ' \
              'Offer doc not updated properly.'
        with pytest.raises(AzureCloudPartnerException, match=msg):
            deprecate_image_in_offer_doc(
                doc,
                '2011.11.11',
            )

    @patch('azure_img_utils.azure_image.submit_configure_request')
    @patch.object(AzureImage, 'get_offer_doc')
    def test_remove_image_from_offer(
        self,
        mock_get_offer,
        mock_sub_config_req
    ):
        doc = {
            'resources': [
                {
                    '$schema': (
                        'https://schema.mp.microsoft.com/schema/'
                        'virtual-machine-plan-technical-configuration/'
                        '2022-03-01-preview5'
                    ),
                    'plan': 'plan/1234/4321',
                    'skus': [{
                        'imageType': 'x64Gen1',
                        'skuId': 'gen1'
                    }],
                    'vmImageVersions': [
                        {
                            'versionNumber': '2011.11.11',
                            'vmImages': [
                                {
                                    'imageType': 'x64Gen1',
                                    'source': {
                                        'sourceType': 'sasUri',
                                        'osDisk': {
                                            'uri': 'bloburl'
                                        },
                                        'dataDisks': []
                                    }
                                }
                            ],
                            'lifecycleState': 'generallyAvailable'
                        }
                    ]
                },
                {
                    '$schema': (
                        'https://schema.mp.microsoft.com/schema/plan/'
                        '2022-03-01-preview2'
                    ),
                    'id': 'plan/1234/4321',
                    'identity': {
                        'externalId': 'gen1'
                    },
                }
            ]
        }

        mock_get_offer.return_value = doc
        mock_sub_config_req.return_value = '123'

        self.image.remove_image_from_offer(
            'suse:sles:gen1:2011.11.11',
        )

        plan = doc['resources'][0]['vmImageVersions'][0]

        assert plan['versionNumber'] == '2011.11.11'
        assert plan['lifecycleState'] == 'deprecated'
