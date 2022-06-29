import logging
import pytest

from unittest.mock import MagicMock, patch
from requests import Response

from azure_img_utils.azure_image import AzureImage
from azure_img_utils.cloud_partner import deprecate_image_in_offer_doc

from azure_img_utils.exceptions import (
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

    @patch('azure_img_utils.azure_image.process_request')
    def test_get_offer_doc(self, mock_process_request):
        mock_process_request.return_value = {'offer': 'doc'}
        doc = self.image.get_offer_doc('sles', 'suse')
        assert doc['offer'] == 'doc'

    @patch('azure_img_utils.azure_image.process_request')
    def test_upload_offer_doc(self, mock_process_request):
        mock_process_request.return_value = {'offer': 'doc'}
        doc = {'offer': 'doc'}
        self.image.upload_offer_doc('sles', 'suse', doc)

    @patch('azure_img_utils.azure_image.process_request')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_add_image_to_offer(self, mock_process_request, mock_preq2):
        doc = {
            'definition': {
                'plans': [
                    {
                        'planId': 'gen1',
                        'diskGenerations': [{'planId': 'image-gen2'}]
                    }
                ]
            }
        }

        mock_process_request.return_value = doc
        mock_preq2.return_value = doc

        self.image.add_image_to_offer(
            'image.raw',
            'image123-v20111111',
            'This is a great image!',
            'sles',
            'suse',
            'suse-sles',
            'gen1',
            blob_url='bloburl',
            generation_id='image-gen2',
            generation_suffix='gen2'
        )

        vm_key = 'microsoft-azure-corevm.vmImagesPublicAzure'
        plan = doc['definition']['plans'][0]
        generation = plan['diskGenerations'][0][vm_key]['2011.11.11']

        assert plan['planId'] == 'gen1'
        assert generation['mediaName'] == 'image123-v20111111-gen2'
        assert generation['showInGui']

        msg = 'No Match found for SKU: NOTgen1. ' \
              'Offer doc not updated properly.'

        with pytest.raises(AzureCloudPartnerException, match=msg):
            self.image.add_image_to_offer(
                'image.raw',
                'image123-v20111111',
                'This is a great image!',
                'sles',
                'suse',
                'suse-sles',
                'NOTgen1',
                blob_url='bloburl',
                generation_id='image-gen2',
                generation_suffix='gen2'
            )

        msg = 'No Match found for Generation ID: NOTimage-gen2. ' \
              'Offer doc not updated properly.'

        with pytest.raises(AzureCloudPartnerException, match=msg):
            self.image.add_image_to_offer(
                'image.raw',
                'image123-v20111111',
                'This is a great image!',
                'sles',
                'suse',
                'suse-sles',
                'gen1',
                blob_url='bloburl',
                generation_id='NOTimage-gen2',
                generation_suffix='gen2'
            )

    @patch('azure_img_utils.azure_image.process_request')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_remove_image_from_offer(self, mock_process_request, mock_preq2):
        vm_key = 'microsoft-azure-corevm.vmImagesPublicAzure'
        doc = {
            'definition': {
                'plans': [
                    {
                        'planId': 'gen1',
                        vm_key: {'2011.11.11': {
                            'mediaName': 'image123-v20111111-gen2',
                            'showInGui': True
                        }},
                        'diskGenerations': [{
                            'planId': 'gen2',
                            vm_key: {'2011.11.11': {
                                'mediaName': 'image123-v20111111-gen2',
                                'showInGui': True
                            }}
                        }]
                    }
                ]
            }
        }

        mock_process_request.return_value = doc
        mock_preq2.return_value = doc
        self.image.remove_image_from_offer('suse:sles:gen1:2011.11.11')
        self.image.remove_image_from_offer('suse:sles:gen2:2011.11.11')

        plan = doc['definition']['plans'][0]
        generations = plan['diskGenerations'][0][vm_key]

        assert '2011.11.11' not in plan[vm_key]
        assert '2011.11.11' not in generations

        msg = 'No match found for version: 2011.11.12 and Plan ID: NOTgen1. ' \
              'Offer doc not updated properly.'

        with pytest.raises(AzureCloudPartnerException, match=msg):
            self.image.remove_image_from_offer('suse:sles:NOTgen1:2011.11.12')

    @patch('azure_img_utils.azure_image.process_request')
    def test_publish_offer(self, mock_process_request):

        response = MagicMock(spec=Response)
        response.headers = {'Location': '/uri/to/operation/id'}
        mock_process_request.return_value = response

        operation = self.image.publish_offer('sles', 'suse', 'test@email.com')
        assert operation == '/uri/to/operation/id'

    @patch('azure_img_utils.azure_image.process_request')
    def test_go_live_with_offer(self, mock_process_request):
        response = MagicMock(spec=Response)
        response.headers = {'Location': '/uri/to/operation/id'}
        mock_process_request.return_value = response

        operation = self.image.go_live_with_offer('sles', 'suse')
        assert operation == '/uri/to/operation/id'

    @patch('azure_img_utils.azure_image.process_request')
    def test_get_offer_status(self, mock_process_request):
        mock_process_request.return_value = {
            'status': 'running',
            'steps': [{
                'stepName': 'publisher-signoff',
                'status': 'waitingForPublisherReview'
            }]
        }

        status = self.image.get_offer_status('sles', 'suse')
        assert status == 'waitingForPublisherReview'

    @patch('azure_img_utils.azure_image.process_request')
    def test_get_operation(self, mock_process_request):
        mock_process_request.return_value = {'operation': 'info'}
        operation = self.image.get_operation('/uri/to/operation/id')
        assert operation['operation'] == 'info'

    def test_deprecate_image_in_offer_1(self):
        vm_key = 'microsoft-azure-corevm.vmImagesPublicAzure'
        doc = {
            'definition': {
                'plans': [
                    {
                        'planId': 'gen1',
                        vm_key: {'2011.11.11': {
                            'mediaName': 'image123-v20111111-gen2',
                            'showInGui': True
                        }},
                        'diskGenerations': [{
                            'planId': 'gen2',
                            vm_key: {'2011.11.11': {
                                'mediaName': 'image123-v20111111-gen2',
                                'showInGui': True
                            }}
                        }]
                    }
                ]
            }
        }

        my_response = deprecate_image_in_offer_doc(
            doc,
            'image123-v20111111-gen2',
            'gen1',
            logging.getLogger('azure_img_utils'),
            vm_images_key=vm_key
        )

        image = my_response['definition']['plans'][0][vm_key]['2011.11.11']

        assert image['showInGui'] is False

    def test_deprecate_image_in_offer_2(self):
        vm_key = 'microsoft-azure-corevm.vmImagesPublicAzure'
        simple_doc = {
            'myKey': 'myValue'
        }

        my_response = deprecate_image_in_offer_doc(
            simple_doc,
            'image123-vNOT8DIGITS-gen2',
            'gen1',
            logging.getLogger('azure_img_utils').info,
            vm_images_key=vm_key
        )

        assert my_response['myKey'] == simple_doc['myKey']

    def test_deprecate_image_in_offer_3(self):
        vm_key = 'microsoft-azure-corevm.vmImagesPublicAzure'
        doc = {
            'definition': {
                'plans': [
                    {
                        'planId': 'gen1',
                        vm_key: {'2011.11.11': {
                            'mediaName': 'image123-v20111111-gen2',
                            'showInGui': True
                        }},
                        'diskGenerations': [{
                            'planId': 'gen2',
                            vm_key: {'2011.11.11': {
                                'mediaName': 'image123-v20111111-gen2',
                                'showInGui': True
                            }}
                        }]
                    }
                ]
            }
        }

        # msg = 'No match found for version: 2011.11.12 and Plan ID: NOTgen1. '
        #      'Offer doc not updated properly.'
        with self._caplog.at_level(logging.INFO):
            deprecate_image_in_offer_doc(
                doc,
                'image123-v20111111-gen3',
                'gen1',
                logging.getLogger('azure_img_utils').info,
                vm_images_key=vm_key
            )

            msg = 'Deprecation image name, image123-v20111111-gen3 does not ' \
                  'match the mediaName attribute, image123-v20111111-gen2.'
            assert msg in self._caplog.text

    def test_deprecate_image_in_offer_4(self):
        vm_key = 'microsoft-azure-corevm.vmImagesPublicAzure'
        doc = {
            'definition': {
                'plans': []
            }
        }

        msg = 'No Match found for image in the SKU: gen1. ' \
              'Offer doc not updated properly.'
        with pytest.raises(AzureCloudPartnerException, match=msg):
            deprecate_image_in_offer_doc(
                doc,
                'image123-v20111111-gen2',
                'gen1',
                logging.getLogger('azure_img_utils'),
                vm_images_key=vm_key
            )
