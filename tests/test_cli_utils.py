import io

from unittest.mock import call, patch, MagicMock

from azure_img_utils.cli.cli_utils import save_json_to_file


def test_save_json_to_file():
    fake_doc = {'this': 'is', 'a': 'fake', 'offer': 'doc'}
    file = 'tests/fake.json'

    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value = MagicMock(spec=io.IOBase)
        file_handle = mock_open.return_value.__enter__.return_value
        save_json_to_file(fake_doc, file)
        file_handle.write.assert_has_calls([
            call('{'),
            call('\n  '),
            call('"this"'),
            call(': '),
            call('"is"'),
            call(',\n  '),
            call('"a"'),
            call(': '),
            call('"fake"'),
            call(',\n  '),
            call('"offer"'),
            call(': '),
            call('"doc"'),
            call('\n'),
            call('}')
        ])
