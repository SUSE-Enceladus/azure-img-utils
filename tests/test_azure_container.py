import pytest

from unittest.mock import patch, Mock

from azure_img_utils.azure_container import AzureContainer
# from azure_img_utils.cloud_partner import (
#     deprecate_image_in_offer_doc,
#     get_technical_details
# )

from azure_img_utils.exceptions import (
    AzureCloudPartnerException,
    AzureImgUtilsException
)


class TestAzureCcontainer(object):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('azure_img_utils.azure_container.get_durable_id')
    @patch('azure_img_utils.azure_container.acquire_access_token')
    @patch('azure_img_utils.azure_container.get_resource_endpoint')
    @patch('azure_img_utils.azure_container.process_request')
    def test_offer_exists(
        self,
        mock_process_request,
        mock_get_resource_endpoint,
        mock_acquire_access_token,
        mock_get_durable_id
    ):
        # successful case
        azure_container = AzureContainer(
            credentials_file='tests/creds.json',
        )
        mock_process_request.return_value = {'offer': 'doc'}
        mock_get_resource_endpoint.return_value = 'example_resource_endpoint'
        mock_acquire_access_token.return_value = 'access_token'
        mock_get_durable_id.return_value = 'durable_id'
        assert azure_container.offer_exists('offer_id')
        mock_process_request.assert_called_with(
            'example_resource_endpoint',
            {
                'Accept': 'application/json',
                'Authorization': 'Bearer access_token'
            },
            method='get',
            retries=0
        )
        mock_get_resource_endpoint.assert_called_with(
            'product/durable_id',
            'draft'
        )
        mock_acquire_access_token.assert_called_with(
            {
                'clientId': '12345678-1234-1234-1234-012345678910',
                'clientSecret': '12345678-1234-1234-1234-012345678910',
                'subscriptionId': '12345678-1234-1234-1234-012345678910',
                'tenantId': '12345678-1234-1234-1234-012345678910',
                'activeDirectoryEndpointUrl': 'https://login.microsoftonline.com',  # NOQA
                'resourceManagerEndpointUrl': 'https://management.azure.com/',
                'activeDirectoryGraphResourceId': 'https://graph.windows.net/',
                'sqlManagementEndpointUrl': 'https://management.core.windows.net:8443/',  # NOQA
                'galleryEndpointUrl': 'https://gallery.azure.com/',
                'managementEndpointUrl': 'https://management.core.windows.net/'
            },
            cloud_partner=True
        )
        mock_get_durable_id.assert_called_with(
            {
                'Accept': 'application/json',
                'Authorization': 'Bearer access_token'
            },
            'offer_id'
        )

        # exception
        logger = Mock()
        azure_container = AzureContainer(
            credentials_file='tests/creds.json',
            log_callback=logger
        )
        mock_process_request.side_effect = \
            AzureCloudPartnerException('example exception')
        assert not azure_container.offer_exists('offer_id')

    def test_credentials(self):
        # exception
        with pytest.raises(AzureImgUtilsException) as error:
            logger = Mock()
            azure_container = AzureContainer(
                log_callback=logger
            )
            azure_container.credentials
        assert 'No credentials dictionary' in str(error)

        # credentials setter
        creds = {
            'example_creds': 'example_value'
        }
        azure_container = AzureContainer(
            log_callback=logger
        )
        azure_container.credentials = creds
        assert azure_container.credentials == creds

        # credentials file setting
        azure_container = AzureContainer(
            log_callback=logger
        )
        azure_container.credentials_file = 'tests/creds.json'
        assert azure_container.credentials['clientId'] == \
            '12345678-1234-1234-1234-012345678910'
        assert azure_container.credentials_file == 'tests/creds.json'
