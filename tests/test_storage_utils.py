from unittest.mock import MagicMock, patch

from azure.storage.blob import BlobServiceClient
from azure.mgmt.storage import StorageManagementClient

from azure_img_utils.storage import (
    get_blob_service,
    get_blob_url,
    get_storage_account_key
)


class Key(object):
    def __init__(self, value) -> None:
        self.value = value


class AccountKeys(object):
    def __init__(self, key1, key2) -> None:
        self.keys = [Key(key1), Key(key2)]


creds = {'super': 'secret'}
sas_token = (
    'sp=rl&st=2021-08-27T20:23:21Z&se=2021-08-28T04:23:21Z'
    '&spr=https&sv=2020-08-04&sr=c&sig=supersecretstuffhere'
)


@patch('azure_img_utils.auth.generate_container_sas')
def test_get_blob_url(mock_generate_sas):
    bsc = MagicMock(spec=BlobServiceClient)
    bsc.credential = MagicMock()
    bsc.credential.account_key = 'supersecretstuffhere'

    mock_generate_sas.return_value = sas_token

    url = get_blob_url(
        bsc,
        'image_123.raw',
        'account',
        'images'
    )

    expected = (
        'https://account.blob.core.windows.net/images/image_123.raw?'
        'sp=rl&st=2021-08-27T20:23:21Z&se=2021-08-28T04:23:21Z&spr=https'
        '&sv=2020-08-04&sr=c&sig=supersecretstuffhere'
    )
    assert url == expected


@patch('azure_img_utils.storage.get_client_from_json')
def test_get_storage_account_key(mock_get_client):
    smc = MagicMock(spec=StorageManagementClient)
    smc.storage_accounts = MagicMock()
    smc.storage_accounts.list_keys.return_value = AccountKeys('123', '321')
    mock_get_client.return_value = smc

    result = get_storage_account_key(creds, 'group', 'account')
    assert result == '123'


@patch('azure_img_utils.storage.BlobServiceClient')
@patch('azure_img_utils.storage.get_storage_account_key')
def test_get_blob_service(mock_get_key, mock_blob_service):
    bsc = MagicMock(spec=BlobServiceClient)

    mock_get_key.return_value = '123'
    mock_blob_service.return_value = bsc

    # Get service from creds
    result = get_blob_service(creds, 'group', 'account')
    assert result == bsc

    # Get service from sas token
    result = get_blob_service(sas_token, 'account')
    assert result == bsc
