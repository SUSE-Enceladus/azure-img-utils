#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Azure img utils container_registry unit tests."""

# Copyright (c) 2025 SUSE LLC. All rights reserved.
#
# This file is part of azure_img_utils. azure_img_utils provides an
# api and command line utilities for handling images in the Azure Cloud.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest

from unittest.mock import MagicMock
from azure_img_utils.container_registry import (
    get_list_of_available_cnab_tags,
    cnab_tag_is_available,
    get_digest_for_tag
)


class TagMock:

    def __init__(self, name, digest):
        self.name = name
        self.digest = digest


class TestContaineRegistry(object):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def test_get_list_of_available_cnab_tags(self):
        acr_client = MagicMock()
        acr_client.list_tag_properties.return_value = [
            TagMock('1.0.0', 'sha256:1111111'),
            TagMock('2.0.0', 'sha256:2222222'),
            TagMock('3.0.0', 'sha256:3333333')
        ]

        expected_result = ['1.0.0', '2.0.0', '3.0.0']

        result = get_list_of_available_cnab_tags(acr_client, 'repo_name')
        assert result == expected_result

    def test_cnab_tag_is_available(self):
        acr_client = MagicMock()
        acr_client.list_tag_properties.return_value = [
            TagMock('1.0.0', 'sha256:1111111'),
            TagMock('2.0.0', 'sha256:2222222'),
            TagMock('3.0.0', 'sha256:3333333')
        ]

        tests = [
            ('1.0.0', True),
            ('3.0.0', True),
            ('1.1.0', False)
        ]

        for tag, expected_result in tests:
            assert expected_result == cnab_tag_is_available(
                acr_client,
                'repo_name',
                tag
            )

    def test_get_digest_for_tag(self):
        acr_client = MagicMock()
        acr_client.get_tag_properties.side_effect = [
            TagMock('1.0.0', 'sha256:1111111'),
            TagMock('2.0.0', 'sha256:2222222'),
            TagMock('3.0.0', '')
        ]

        tests = [
            ('1.0.0', 'sha256:1111111'),
            ('2.0.0',  'sha256:2222222'),
            ('1.1.0', '')
        ]

        for tag, expected_result in tests:
            assert expected_result == get_digest_for_tag(
                acr_client,
                'repo_name',
                tag
            )
