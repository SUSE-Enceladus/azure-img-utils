import pytest

from unittest.mock import MagicMock, patch

from azure_img_utils.auth import (
   acquire_access_token,
)

from azure_img_utils.exceptions import (
    AzureImgUtilsException
)


class TestAzureAuth(object):
    def setup_class(self):
        pass

    @patch('azure_img_utils.auth.msal.ConfidentialClientApplication')
    def test_acquire_access_token(self, mock_cclient_app):

        my_credentials = {
            'clientId': 'myClientId',
            'clientSecret': 'myClientSecret',
            'activeDirectoryEndpointUrl': 'myADEndpointUrl',
            'managementEndpointUrl': 'myMgmtEndpointUrl',
            'tenantId': 'myTenantId'
        }

        my_client = MagicMock()

        my_response = {
            'access_token': 'mySecretAccessToken'
        }

        my_client.acquire_token_for_client.return_value = my_response
        mock_cclient_app.return_value = my_client

        my_token = acquire_access_token(
            my_credentials,
            cloud_partner=False
        )
        assert my_token == 'mySecretAccessToken'

        # Error condidion
        my_err_response = {
            'access_token': 'mySecretAccessToken',
            'error': 'myCustomError'
        }

        my_client.acquire_token_for_client.return_value = my_err_response

        msg = 'Unable to authenticate against ' \
              'https://cloudpartner.azure.com/.default: ' \
              'myCustomError'

        with pytest.raises(AzureImgUtilsException, match=msg):
            my_token = acquire_access_token(
                my_credentials,
                cloud_partner=True
            )
