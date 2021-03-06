# -*- coding: utf-8 -*-

"""Azure image utils exceptions module."""

# Copyright (c) 2021 SUSE LLC
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


class AzureImgUtilsException(Exception):
    """Generic exception for the azure_img_utils package."""


class AzureCloudPartnerException(AzureImgUtilsException):
    """Exception for Azure Cloud Partner processes."""


class AzureImgUtilsStorageException(AzureImgUtilsException):
    """Exception for Azure Storage processes."""
