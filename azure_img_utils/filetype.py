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

import os
import re
import lzma
import subprocess


class FileType(object):
    """
    map file magic information to type methods
    """
    def __init__(self, file_name: str):
        self.file_name = file_name
        file_info = subprocess.Popen(
            ['file', file_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.filetype = file_info.communicate()[0].decode()

    def is_xz(self):
        if re.match('.*: XZ compressed', self.filetype):
            return True
        return False

    def get_size(self):
        if self.is_xz():
            with lzma.open(self.file_name) as lzma_stream:
                lzma_stream.seek(0, os.SEEK_END)
                return lzma_stream.tell()
        else:
            return os.path.getsize(self.file_name)
