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

    @patch('azure_img_utils.auth.requests')
    def test_acquire_access_token(self, mock_requests):

        my_credentials = {
            'clientId': 'myClientId',
            'clientSecret': 'myClientSecret',
            'activeDirectoryEndpointUrl': 'myADEndpointUrl',
            'managementEndpointUrl': 'myMgmtEndpointUrl',
            'tenantId': 'myTenantId'
        }

        my_response = {
            'access_token': 'mySecretAccessToken'
        }
        response = MagicMock()
        response.json.return_value = my_response
        mock_requests.post.return_value = response

        my_token = acquire_access_token(
            my_credentials,
            cloud_partner=False
        )
        assert my_token == 'mySecretAccessToken'

        # Error condidion
        my_err_response = {
            'error_description': 'myCustomError'
        }

        response.json.return_value = my_err_response

        msg = 'Unable to authenticate against ' \
              'myADEndpointUrl/myTenantId/oauth2/v2.0/token: ' \
              'myCustomError'

        with pytest.raises(AzureImgUtilsException, match=msg):
            my_token = acquire_access_token(
                my_credentials,
                cloud_partner=True
            )
