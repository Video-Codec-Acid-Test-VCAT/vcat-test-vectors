# vcat-test-vectors
#
# SPDX-FileCopyrightText: Copyright (C) 2020-2025 VCAT authors and RoncaTech
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of vcat-test-vectors.
#
# vcat-test-vectors is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# vcat-test-vectors is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with vcat-test-vectors. If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# For proprietary/commercial use cases, a written GPL-3.0 waiver or
# a separate commercial license is required from RoncaTech LLC.
#
# All VCAT artwork is owned exclusively by RoncaTech LLC. Use of VCAT logos
# and artwork is permitted for the purpose of discussing, documenting,
# or promoting VCAT itself. Any other use requires prior written permission
# from RoncaTech LLC.
#
# Contact: legal@roncatech.com

import hashlib
import os


def getChecksum(local_file_path):
    """
    Calculate the checksum of a local file using SHA256.
    """
    hash_sha256 = hashlib.sha256()

    with open(local_file_path, "rb") as f:
        while chunk := f.read(4096):
            hash_sha256.update(chunk)

    return hash_sha256.hexdigest()


def getFileLength(file_path):
    """
    Get the length (size) of the file in bytes.
    """
    return os.path.getsize(file_path)
