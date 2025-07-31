import pytest

from unittest.mock import patch, Mock, MagicMock, call
from azure.containerregistry import ContainerRegistryClient

from azure_img_utils.azure_container import AzureContainer
from azure_img_utils.exceptions import (
    AzureCloudPartnerException,
    AzureImgUtilsException
)


class TestAzureContainer(object):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('azure_img_utils.cloud_partner.get_durable_id')
    @patch('azure_img_utils.azure_container.acquire_access_token')
    @patch('azure_img_utils.cloud_partner.get_resource_endpoint')
    @patch('azure_img_utils.cloud_partner.process_request')
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

    @patch('azure_img_utils.cloud_partner.wait_on_operation')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_upload_offer_doc(
        self,
        mock_process_request,
        mock_wait_on_operation
    ):
        azure_container = AzureContainer(
            credentials_file='tests/creds.json',
        )

        azure_container._access_token = 'dummy_access_token'

        response = {'jobId': '123'}
        mock_process_request.return_value = response

        mock_wait_on_operation.return_value = {
            'jobStatus': 'completed',
            'jobResult': 'succeeded'
        }

        doc = {'resources': [{'offer': 'doc'}]}
        resp = azure_container.upload_offer_doc(doc)
        assert resp == '123'

    @patch('azure_img_utils.cloud_partner.wait_on_operation')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_update_resource_in_offer(
        self,
        mock_process_request,
        mock_wait_on_operation
    ):
        azure_container = AzureContainer(
            credentials_file='tests/creds.json',
        )

        azure_container._access_token = 'dummy_access_token'

        response = {'jobId': '123'}
        mock_process_request.return_value = response

        mock_wait_on_operation.return_value = {
            'jobStatus': 'completed',
            'jobResult': 'succeeded'
        }

        resource_doc = {
            'dummy_key_1': 'dummy_value_1',
            'dummy_key_2': 'dummy_value_2'
        }
        resp = azure_container.update_resource_in_offer(resource_doc)
        assert resp == '123'

    @patch('azure_img_utils.azure_container.get_client_from_json')
    @patch('azure_img_utils.azure_container.cloud_partner.get_offer_doc')
    @patch('azure_img_utils.cloud_partner.get_digest_for_tag')
    @patch('azure_img_utils.azure_container.cloud_partner.submit_request')
    def test_add_cnab_version_to_offer(
        self,
        mock_submit_request,
        mock_get_digest_for_tag,
        mock_get_offer_doc,
        mock_get_client_from_json
    ):
        acr_client = MagicMock(spec=ContainerRegistryClient)
        mock_get_client_from_json.return_value = acr_client

        doc = {
            "resources": [
                {
                    "$schema": "https://schema.mp.microsoft.com/schema/plan/2022-03-01-preview3",  # NOQA
                    "id": "plan/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958",  # NOQA
                    "identity": {
                        "externalId": "payg"
                    },
                    "alias": "NeuVector Prime with 24x7 Support (non-EU and non-UK only) deprecated",  # NOQA
                    "azureRegions": [
                        "azureGlobal"
                    ],
                    "product": "product/d6605881-da06-4fb5-a326-1bd8b0843437",
                    "lifecycleState": "deprecated"
                },
                {
                    "$schema": "https://schema.mp.microsoft.com/schema/container-plan-technical-configuration/2022-03-01-preview3",  # NOQA
                    "id": "container-plan-technical-configuration/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958",  # NOQA
                    "product": "product/d6605881-da06-4fb5-a326-1bd8b0843437",
                    "plan": "plan/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958",  # NOQA
                    "payloadType": "cnab",
                    "clusterExtensionType": "suse.neuvector-prime-llc",
                    "cnabReferences": [
                        {
                            "tenantId": "c977ffe0-e8f3-4d6f-ab49-e03bbc3287b1",
                            "subscriptionId": "b297ab83-361f-424f-804c-0c44fa26e903",  # NOQA
                            "resourceGroupName": "suse-llc-marketplace-containers",  # NOQA
                            "registryName": "susellcforazuremarketplace",
                            "repositoryName": "suse.neuvector-prime-llc",
                            "tag": "50202.1.202310252",
                            "digest": "sha256:48ea065b1f85323111c970b27d5641fc54942dd8b6bb8ed87f4220f238ceb57d"  # NOQA
                        }
                    ]
                }
            ]
        }

        mock_get_offer_doc.return_value = doc
        mock_get_digest_for_tag.return_value = 'sha256:111111111'

        azure_container = AzureContainer(
            credentials_file='tests/creds.json',
        )
        azure_container._access_token = 'my_test_access_token'

        azure_container.add_cnab_version_to_offer(
            registry_name='susellcforazuremarketplace',
            repository_name='suse.neuvector-prime-llc',
            tag='50303.1.20250101',
            offer_id='my_test_offer',
            sku='payg',
            acr_client=azure_container.acr_client
        )

        assert call(
            ContainerRegistryClient,
            {
                'clientId': '12345678-1234-1234-1234-012345678910',
                'clientSecret': '12345678-1234-1234-1234-012345678910',
                'subscriptionId': '12345678-1234-1234-1234-012345678910',
                'tenantId': '12345678-1234-1234-1234-012345678910',
                'activeDirectoryEndpointUrl': 'https://login.microsoftonline.com',  # NOQA
                'resourceManagerEndpointUrl': 'https://management.azure.com/',   # NOQA
                'activeDirectoryGraphResourceId': 'https://graph.windows.net/',  # NOQA
                'sqlManagementEndpointUrl': 'https://management.core.windows.net:8443/',  # NOQA
                'galleryEndpointUrl': 'https://gallery.azure.com/',  # NOQA
                'managementEndpointUrl': 'https://management.core.windows.net/'
            }
        ) in mock_get_client_from_json.mock_calls

        mock_get_digest_for_tag.assert_called_with(
            acr_client,
            'suse.neuvector-prime-llc',
            '50303.1.20250101'
        )

        mock_submit_request.assert_called_with(
            'my_test_access_token',
            [
                {
                    '$schema': 'https://schema.mp.microsoft.com/schema/container-plan-technical-configuration/2022-03-01-preview3',  # NOQA
                    'id': 'container-plan-technical-configuration/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958',  # NOQA
                    'product': 'product/d6605881-da06-4fb5-a326-1bd8b0843437',
                    'plan': 'plan/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958',  # NOQA
                    'payloadType': 'cnab',
                    'clusterExtensionType': 'suse.neuvector-prime-llc',
                    'cnabReferences': [
                        {
                            'tenantId': 'c977ffe0-e8f3-4d6f-ab49-e03bbc3287b1',
                            'subscriptionId': 'b297ab83-361f-424f-804c-0c44fa26e903',  # NOQA
                            'resourceGroupName': 'suse-llc-marketplace-containers',  # NOQA
                            'registryName': 'susellcforazuremarketplace',
                            'repositoryName': 'suse.neuvector-prime-llc',
                            'tag': '50202.1.202310252',
                            'digest': 'sha256:48ea065b1f85323111c970b27d5641fc54942dd8b6bb8ed87f4220f238ceb57d'  # NOQA
                        },
                        {
                            'tenantId': 'c977ffe0-e8f3-4d6f-ab49-e03bbc3287b1',
                            'subscriptionId': 'b297ab83-361f-424f-804c-0c44fa26e903',  # NOQA
                            'resourceGroupName': 'suse-llc-marketplace-containers',  # NOQA
                            'registryName': 'susellcforazuremarketplace',
                            'repositoryName': 'suse.neuvector-prime-llc',
                            'tag': '50303.1.20250101',
                            'digest': 'sha256:111111111'
                        }
                    ]
                }
            ]
        )

    @patch('azure_img_utils.cloud_partner.get_durable_id')
    @patch('azure_img_utils.azure_container.cloud_partner.submit_request')
    def test_publish_offer(
        self,
        mock_submit_request,
        mock_get_durable_id
    ):

        mock_get_durable_id.return_value = 'test_durable_id'
        mock_submit_request.return_value = 'test_job_id'

        azure_container = AzureContainer(
            credentials_file='tests/creds.json',
        )
        azure_container._access_token = 'my_test_access_token'

        azure_container.publish_offer(
            offer_id='test_offer_id'
        )

        mock_submit_request.assert_called_with(
            'my_test_access_token',
            [
                {
                    '$schema': 'https://schema.mp.microsoft.com/schema/submission/2022-03-01-preview2',  # NOQA
                    'product': 'product/test_durable_id',
                    'target': {'targetType': 'preview'}
                }
            ],
            wait=False
        )
        mock_get_durable_id.assert_called_with(
            {
                'Accept': 'application/json',
                'Authorization': 'Bearer my_test_access_token'
            },
            'test_offer_id'
        )

    @patch(
        'azure_img_utils.azure_container.cloud_partner.get_offer_submissions'
    )
    @patch('azure_img_utils.cloud_partner.get_durable_id')
    @patch('azure_img_utils.azure_container.cloud_partner.submit_request')
    def test_go_live_with_offer(
        self,
        mock_submit_request,
        mock_get_durable_id,
        mock_get_offer_submissions
    ):
        mock_get_offer_submissions.return_value = {
            'value': [
                {
                    'target': {'targetType': 'preview'},
                    'id': '321'
                }
            ]
        }
        mock_get_durable_id.return_value = 'test_durable_id'
        mock_submit_request.return_value = 'test_job_id'

        azure_container = AzureContainer(
            credentials_file='tests/creds.json',
        )
        azure_container._access_token = 'my_test_access_token'

        azure_container.go_live_with_offer(
            offer_id='test_offer_id'
        )
        mock_submit_request.assert_called_with(
            'my_test_access_token',
            [
                {
                    '$schema': 'https://schema.mp.microsoft.com/schema/submission/2022-03-01-preview2',  # NOQA
                    'product': 'product/test_durable_id',
                    'id': '321',
                    'target': {'targetType': 'live'}
                }
            ],
            wait=False
        )
        mock_get_durable_id.assert_called_with(
            {
                'Accept': 'application/json',
                'Authorization': 'Bearer my_test_access_token'
            },
            'test_offer_id'
        )
        mock_get_offer_submissions.assert_called_with(
            'test_durable_id',
            {
                'Accept': 'application/json',
                'Authorization': 'Bearer my_test_access_token'
            }
        )

    @patch('azure_img_utils.azure_container.cloud_partner.get_offer_doc')
    @patch('azure_img_utils.azure_container.cloud_partner.submit_request')
    def test_remove_cnab_version_from_offer(
        self,
        mock_submit_request,
        mock_get_offer_doc,
    ):
        doc = {
            "resources": [
                {
                    "$schema": "https://schema.mp.microsoft.com/schema/plan/2022-03-01-preview3",  # NOQA
                    "id": "plan/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958",  # NOQA
                    "identity": {
                        "externalId": "payg"
                    },
                    "alias": "NeuVector Prime with 24x7 Support (non-EU and non-UK only) deprecated",  # NOQA
                    "azureRegions": [
                        "azureGlobal"
                    ],
                    "product": "product/d6605881-da06-4fb5-a326-1bd8b0843437",
                    "lifecycleState": "deprecated"
                },
                {
                    "$schema": "https://schema.mp.microsoft.com/schema/container-plan-technical-configuration/2022-03-01-preview3",  # NOQA
                    "id": "container-plan-technical-configuration/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958",  # NOQA
                    "product": "product/d6605881-da06-4fb5-a326-1bd8b0843437",
                    "plan": "plan/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958",  # NOQA
                    "payloadType": "cnab",
                    "clusterExtensionType": "suse.neuvector-prime-llc",
                    "cnabReferences": [
                        {
                            "tenantId": "c977ffe0-e8f3-4d6f-ab49-e03bbc3287b1",
                            "subscriptionId": "b297ab83-361f-424f-804c-0c44fa26e903",  # NOQA
                            "resourceGroupName": "suse-llc-marketplace-containers",  # NOQA
                            "registryName": "susellcforazuremarketplace",
                            "repositoryName": "suse.neuvector-prime-llc",
                            "tag": "50202.1.202310252",
                            "digest": "sha256:48ea065b1f85323111c970b27d5641fc54942dd8b6bb8ed87f4220f238ceb57d"  # NOQA
                        },
                        {
                            "tenantId": "c977ffe0-e8f3-4d6f-ab49-e03bbc3287b1",
                            "subscriptionId": "b297ab83-361f-424f-804c-0c44fa26e903",  # NOQA
                            "resourceGroupName": "suse-llc-marketplace-containers",  # NOQA
                            "registryName": "susellcforazuremarketplace",
                            "repositoryName": "suse.neuvector-prime-llc",
                            "tag": "50303.1.20250101",
                            "digest": "sha256:48ea065b1f85323111c970b27d5641fc54942dd8b6bb8ed87f4220f238ceb57d"  # NOQA
                        }


                    ]
                }
            ]
        }

        mock_get_offer_doc.return_value = doc

        azure_container = AzureContainer(
            credentials_file='tests/creds.json',
        )
        azure_container._access_token = 'my_test_access_token'

        azure_container.remove_cnab_version_from_offer(
            offer_id='my_test_offer',
            sku='payg',
            registry_name='susellcforazuremarketplace',
            repository_name='suse.neuvector-prime-llc',
            tag='50303.1.20250101'
        )

        mock_submit_request.assert_called_with(
            'my_test_access_token',
            [
                {
                    '$schema': 'https://schema.mp.microsoft.com/schema/container-plan-technical-configuration/2022-03-01-preview3',  # NOQA
                    'id': 'container-plan-technical-configuration/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958',  # NOQA
                    'product': 'product/d6605881-da06-4fb5-a326-1bd8b0843437',
                    'plan': 'plan/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958',  # NOQA
                    'payloadType': 'cnab',
                    'clusterExtensionType': 'suse.neuvector-prime-llc',
                    'cnabReferences': [
                        {
                            'tenantId': 'c977ffe0-e8f3-4d6f-ab49-e03bbc3287b1',
                            'subscriptionId': 'b297ab83-361f-424f-804c-0c44fa26e903',  # NOQA
                            'resourceGroupName': 'suse-llc-marketplace-containers',  # NOQA
                            'registryName': 'susellcforazuremarketplace',
                            'repositoryName': 'suse.neuvector-prime-llc',
                            'tag': '50202.1.202310252',
                            'digest': 'sha256:48ea065b1f85323111c970b27d5641fc54942dd8b6bb8ed87f4220f238ceb57d'  # NOQA
                        }
                    ]
                }
            ]
        )
