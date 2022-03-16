from unittest.mock import MagicMock, patch
from requests import Response

from azure_img_utils.azure_image import AzureImage


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

    @patch('azure_img_utils.cloud_partner.process_request')
    def test_get_offer_doc(self, mock_process_request):
        mock_process_request.return_value = {'offer': 'doc'}
        doc = self.image.get_offer_doc('sles', 'suse')
        assert doc['offer'] == 'doc'

    @patch('azure_img_utils.cloud_partner.process_request')
    def test_upload_offer_doc(self, mock_process_request):
        doc = {'offer': 'doc'}
        self.image.upload_offer_doc('sles', 'suse', doc)

    @patch('azure_img_utils.cloud_partner.process_request')
    def test_add_image_to_offer(self, mock_process_request):
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
        self.image.add_image_to_offer(
            'image.raw',
            'image123-v20111111',
            'This is a great image!',
            'sles',
            'suse',
            'suse-sles',
            'gen1',
            'bloburl',
            'image-gen2',
            'gen2'
        )

        vm_key = 'microsoft-azure-corevm.vmImagesPublicAzure'
        plan = doc['definition']['plans'][0]
        generation = plan['diskGenerations'][0][vm_key]['2011.11.11']

        assert plan['planId'] == 'gen1'
        assert generation['mediaName'] == 'image123-v20111111-gen2'
        assert generation['showInGui']

    @patch('azure_img_utils.cloud_partner.process_request')
    def test_remove_image_from_offer(self, mock_process_request):
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
        self.image.remove_image_from_offer(
            '2011.11.11',
            'sles',
            'suse',
            'gen1',
            'gen2'
        )

        plan = doc['definition']['plans'][0]
        generations = plan['diskGenerations'][0][vm_key]

        assert '2011.11.11' not in plan[vm_key]
        assert '2011.11.11' not in generations

    @patch('azure_img_utils.cloud_partner.process_request')
    def test_publish_offer(self, mock_process_request):
        response = MagicMock(spec=Response)
        response.headers = {'Location': '/uri/to/operation/id'}
        mock_process_request.return_value = response

        operation = self.image.publish_offer('sles', 'suse', 'test@email.com')
        assert operation == '/uri/to/operation/id'

    @patch('azure_img_utils.cloud_partner.process_request')
    def test_go_live_with_offer(self, mock_process_request):
        response = MagicMock(spec=Response)
        response.headers = {'Location': '/uri/to/operation/id'}
        mock_process_request.return_value = response

        operation = self.image.go_live_with_offer('sles', 'suse')
        assert operation == '/uri/to/operation/id'

    @patch('azure_img_utils.cloud_partner.process_request')
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

    @patch('azure_img_utils.cloud_partner.process_request')
    def test_get_operation(self, mock_process_request):
        mock_process_request.return_value = {'operation': 'info'}
        operation = self.image.get_operation('/uri/to/operation/id')
        assert operation['operation'] == 'info'
