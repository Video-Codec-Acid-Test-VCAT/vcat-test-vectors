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

# settings.py

from pathlib import Path

#
# ── Local FS settings ─────────────────────────────────────────────────────────
#

# User's home directory
HOME = Path.home()

# Default input/output folder (override with --input-folder)
BASE_OUTPUT_DIR = HOME / "Downloads" / "vcat_test_vectors"

# Manifest subdirectory
MANIFEST_DIR = BASE_OUTPUT_DIR / "manifests"

#
# ── Catalog settings ──────────────────────────────────────────────────────────
#
CATALOG_FILENAME    = "vcat_testvector_playlist_catalog.json"
CATALOG_DESCRIPTION = "VCAT test vector playlist catalog"

#
# ── Metadata defaults ─────────────────────────────────────────────────────────
#
CREATED_BY = "RoncaTech, LLC"
