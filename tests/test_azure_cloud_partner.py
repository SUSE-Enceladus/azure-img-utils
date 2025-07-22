import pytest

from unittest.mock import patch, Mock, MagicMock

from azure_img_utils.azure_image import AzureImage
from azure_img_utils.cloud_partner import (
    deprecate_image_in_offer_doc,
    get_technical_details,
    wait_on_operation,
    submit_request,
    add_cnab_version_to_offer
)

from azure_img_utils.exceptions import (
    AzureCloudPartnerException,
    AzureImgUtilsException
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

    @patch('azure_img_utils.cloud_partner.get_durable_id')
    @patch('azure_img_utils.cloud_partner.process_request')
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

    @patch('azure_img_utils.cloud_partner.wait_on_operation')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_upload_offer_doc(
        self,
        mock_process_request,
        mock_wait_on_operation
    ):
        response = {'jobId': '123'}
        mock_process_request.return_value = response

        mock_wait_on_operation.return_value = {
            'jobStatus': 'completed',
            'jobResult': 'succeeded'
        }

        doc = {'resources': [{'offer': 'doc'}]}
        resp = self.image.upload_offer_doc(doc)
        assert resp == '123'

    @patch('azure_img_utils.cloud_partner.wait_on_operation')
    @patch('azure_img_utils.cloud_partner.submit_configure_request')
    @patch('azure_img_utils.azure_image.get_offer_doc')
    @patch('azure_img_utils.cloud_partner.process_request')
    @patch('azure_img_utils.cloud_partner.submit_request')
    def test_add_image_to_offer(
        self,
        mock_submit_request,
        mock_process_request,
        mock_get_offer,
        mock_sub_config_req,
        mock_wait_on_operation
    ):
        mock_wait_on_operation.return_value = {
            'jobStatus': 'completed',
            'jobResult': 'succeeded'
        }

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

        mock_process_request.side_effect = [
            {
                'value': [{
                    'id': 'product/123456789'
                }]
            },
            doc
        ]
        mock_get_offer.return_value = doc
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

        # unsuccessful case
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

    @patch('azure_img_utils.cloud_partner.wait_on_operation')
    @patch('azure_img_utils.azure_image.get_durable_id')
    @patch('azure_img_utils.azure_image.get_offer_submissions')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_publish_offer(
        self,
        mock_process_request,
        mock_get_submissions,
        mock_get_durable_id,
        mock_wait_on_operation
    ):
        response = {'jobId': '123'}
        mock_process_request.return_value = response

        mock_get_durable_id.return_value = '123456789'
        mock_get_submissions.return_value = {
            'value': [
                {
                    'target': {'targetType': 'preview'},
                    'id': '321'
                }
            ]
        }

        mock_wait_on_operation.return_value = {
            'jobStatus': 'completed',
            'jobResult': 'succeeded'
        }

        operation = self.image.publish_offer('sles')
        assert operation == '123'

    @patch('azure_img_utils.cloud_partner.wait_on_operation')
    @patch('azure_img_utils.azure_image.get_durable_id')
    @patch('azure_img_utils.azure_image.get_offer_submissions')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_go_live_with_offer(
        self,
        mock_process_request,
        mock_get_submissions,
        mock_get_durable_id,
        mock_wait_on_operation
    ):
        response = {'jobId': '123'}
        mock_process_request.return_value = response

        mock_get_durable_id.return_value = '123456789'
        mock_get_submissions.return_value = {
            'value': [
                {
                    'target': {'targetType': 'preview'},
                    'id': '321'
                }
            ]
        }

        mock_wait_on_operation.return_value = {
            'jobStatus': 'completed',
            'jobResult': 'succeeded'
        }

        operation = self.image.go_live_with_offer('sles')
        assert operation == '123'

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

    @patch('azure_img_utils.cloud_partner.process_request')
    def test_get_operation(self, mock_process_request):
        mock_process_request.return_value = {'operation': 'info'}
        operation = self.image.get_operation('123')
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

    @patch('azure_img_utils.cloud_partner.wait_on_operation')
    @patch('azure_img_utils.cloud_partner.submit_configure_request')
    @patch('azure_img_utils.azure_image.get_offer_doc')
    def test_remove_image_from_offer(
        self,
        mock_get_offer,
        mock_sub_config_req,
        mock_wait_on_operation
    ):
        mock_wait_on_operation.return_value = {
            'jobStatus': 'completed',
            'jobResult': 'succeeded'
        }

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

    @patch('azure_img_utils.cloud_partner.time')
    @patch('azure_img_utils.cloud_partner.process_request')
    def test_wait_on_operation(self, mock_process_request, mock_sleep):
        mock_process_request.side_effect = [
            {
                'jobStatus': 'running'
            },
            {
                'jobStatus': 'completed',
                'jobResult': 'succeeded'
            }
        ]
        operation = wait_on_operation('example_access_token', '123')
        assert operation['jobResult'] == 'succeeded'

    @patch('azure_img_utils.cloud_partner.wait_on_operation')
    @patch('azure_img_utils.cloud_partner.submit_configure_request')
    def test_submit_request(
        self,
        mock_submit_request,
        mock_wait_on_operation
    ):
        mock_submit_request.return_value = '123'
        mock_wait_on_operation.return_value = {
            'jobStatus': 'completed',
            'jobResult': 'failed'
        }

        with pytest.raises(AzureImgUtilsException):
            submit_request('test_token', Mock())

    def test_get_technical_details(self):
        # VMs successful case
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

        result = get_technical_details(doc, 'gen1')
        assert result['plan'] == 'plan/1234/4321'

        # VM unsuccessful case. Not plan found
        with pytest.raises(AzureCloudPartnerException) as error:
            get_technical_details(doc, 'gen2')
        assert 'No plan found for id: gen2' in str(error)

        # VM unsuccessful case. Not technical details found
        doc['resources'][0]['plan'] = 'different_plan'
        with pytest.raises(AzureCloudPartnerException) as error:
            get_technical_details(doc, 'gen1')
        assert (
            'No technical details found for plan durable id: plan/1234/4321'
        ) in str(error)

        # Container based product successful case

        container_doc = {
            'resources': [
                {
                    '$schema': (
                        'https://schema.mp.microsoft.com/schema/'
                        'container-plan-technical-configuration/'
                        '2022-03-01-preview5'
                    ),
                    'plan': 'plan/9876/6789',
                    'skus': [{
                        'imageType': 'x64Gen1',
                        'skuId': 'gen1'
                    }],
                    'vmImageVersions': []
                },

                {
                  "$schema": (
                    "https://schema.mp.microsoft.com/schema/plan"
                    "/2022-03-01-preview3"
                  ),
                  "id": "plan/9876/6789",
                  "identity": {
                    "externalId": "payg"
                  }
                },
            ]
        }
        result = get_technical_details(
            container_doc,
            'payg',
            container_offer=True
        )
        assert result['plan'] == 'plan/9876/6789'

    def test_add_cnab_version_to_offer(self):

        doc = {
            "$schema": "https://schema.mp.microsoft.com/schema/container-plan-technical-configuration/2022-03-01-preview3",  # NOQA
            "id": "container-plan-technical-configuration/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958",  # NOQA
            "product": "product/d6605881-da06-4fb5-a326-1bd8b0843437",
            "plan": "plan/d6605881-da06-4fb5-a326-1bd8b0843437/c9257046-f7bf-44df-8f4c-a78bc0814958",  # NOQA
            "payloadType": "cnab",
            "clusterExtensionType": "suse.neuvector-prime-llc",
            "cnabReferences": []
        }
        cnab_reference = {
            "tenantId": "c977ffe0-e8f3-4d6f-ab49-e03bbc3287b1",
            "subscriptionId": "b297ab83-361f-424f-804c-0c44fa26e903",
            "resourceGroupName": "suse-llc-marketplace-containers",
            "registryName": "susellcforazuremarketplace",
            "repositoryName": "suse.neuvector-prime-llc",
            "tag": "50202.1.202310252",
            "digest": "sha256:48ea065b1f85323111c970b27d5641fc54942dd8b6bb8ed87f4220f238ceb57d"  # NOQA
        }
        new_tag = 'YYYY.MM.DD001'
        new_digest = 'sha256:xxxxxxx...'

        test_doc = doc.copy()
        test_doc['cnabReferences'] = []
        test_doc['cnabReferences'].append(cnab_reference.copy())

        updated_doc = add_cnab_version_to_offer(
            test_doc,
            tag=new_tag,
            digest=new_digest
        )

        assert updated_doc['cnabReferences'][1]['tenantId'] == \
            cnab_reference['tenantId']
        assert updated_doc['cnabReferences'][1]['subscriptionId'] == \
            cnab_reference['subscriptionId']
        assert updated_doc['cnabReferences'][1]['resourceGroupName'] == \
            cnab_reference['resourceGroupName']
        assert updated_doc['cnabReferences'][1]['registryName'] == \
            cnab_reference['registryName']
        assert updated_doc['cnabReferences'][1]['repositoryName'] == \
            cnab_reference['repositoryName']
        assert updated_doc['cnabReferences'][1]['tag'] == new_tag
        assert updated_doc['cnabReferences'][1]['digest'] == new_digest

        # Complete overwrite case
        new_tenant_id = 'test_new_tenant_id'
        new_subscription_id = 'test_new_subscription_id'
        new_resource_group_name = 'test_new_resource_group_name'
        new_repository_name = 'test_new_repository_name'
        new_registry_name = 'test_new_registry_name'

        test_doc = doc.copy()
        test_doc['cnabReferences'] = []
        test_doc['cnabReferences'].append(cnab_reference.copy())

        updated_doc = add_cnab_version_to_offer(
            test_doc,
            tag=new_tag,
            digest=new_digest,
            tenant_id=new_tenant_id,
            subscription_id=new_subscription_id,
            resource_group_name=new_resource_group_name,
            registry_name=new_registry_name,
            repository_name=new_repository_name
        )

        assert updated_doc['cnabReferences'][1]['tenantId'] == new_tenant_id
        assert updated_doc['cnabReferences'][1]['subscriptionId'] == \
            new_subscription_id
        assert updated_doc['cnabReferences'][1]['resourceGroupName'] == \
            new_resource_group_name
        assert updated_doc['cnabReferences'][1]['registryName'] == \
            new_registry_name
        assert updated_doc['cnabReferences'][1]['repositoryName'] == \
            new_repository_name
        assert updated_doc['cnabReferences'][1]['tag'] == new_tag
        assert updated_doc['cnabReferences'][1]['digest'] == new_digest

        # Omitting tag
        test_doc = doc.copy()
        test_doc['cnabReferences'] = []
        test_doc['cnabReferences'].append(cnab_reference.copy())

        acr_client_mock = MagicMock()

        with patch(
            'azure_img_utils.cloud_partner.get_digest_for_tag'
        ) as get_digest_mock:
            get_digest_mock.return_value = 'sha256:123123123'
            updated_doc = add_cnab_version_to_offer(
                test_doc,
                tag=new_tag,
                acr_client=acr_client_mock,
                repository_name=cnab_reference['repositoryName']
            )

            assert updated_doc['cnabReferences'][1]['tenantId'] == \
                cnab_reference['tenantId']
            assert updated_doc['cnabReferences'][1]['subscriptionId'] == \
                cnab_reference['subscriptionId']
            assert updated_doc['cnabReferences'][1]['resourceGroupName'] == \
                cnab_reference['resourceGroupName']
            assert updated_doc['cnabReferences'][1]['registryName'] == \
                cnab_reference['registryName']
            assert updated_doc['cnabReferences'][1]['repositoryName'] == \
                cnab_reference['repositoryName']
            assert updated_doc['cnabReferences'][1]['tag'] == new_tag
            assert updated_doc['cnabReferences'][1]['digest'] == \
                'sha256:123123123'
