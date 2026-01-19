#!/usr/bin/env python3
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

import json
from pathlib import Path
from typing import List

import settings as cfg
from vcat_testvector_datamodels import (
    VcatTestVectorCatalogAsset,
    VcatTestVectorCatalogIndex,
    VcatTestVectorHeader
)
from utils import getChecksum

OUTPUT_FILENAME = "vcat_testvector_catalog_index.json"


def find_local_catalogs() -> List[Path]:
    """
    Return all *_catalog.json files under cfg.BASE_OUTPUT_DIR
    that contain a 'playlists' section.
    """
    candidates = list(cfg.BASE_OUTPUT_DIR.glob("*_catalog.json"))
    valid_catalogs = []

    for p in candidates:
        try:
            data = json.loads(p.read_text())
            if "playlists" in data:
                valid_catalogs.append(p)
        except (json.JSONDecodeError, IOError):
            continue

    return valid_catalogs


def build_index() -> VcatTestVectorCatalogIndex:
    """
    Read every catalog in cfg.BASE_OUTPUT_DIR and assemble an Index object.
    """
    catalog_files = find_local_catalogs()
    assets: List[VcatTestVectorCatalogAsset] = []

    for p in catalog_files:
        # 1) Load the JSON to pull out the header fields
        data = json.loads(p.read_text())
        hdr = data["vcat_testvector_header"]

        # 2) Compute checksum & length of the .json file itself
        checksum = getChecksum(str(p))
        length_bytes = p.stat().st_size

        # 3) Build the "url" field relative to the index's location
        rel_url = f"./{p.name}"

        asset = VcatTestVectorCatalogAsset(
            name=hdr["name"],
            url=rel_url,
            checksum=checksum,
            length_bytes=length_bytes,
            uuid=hdr["uuid"],
            description=hdr["description"]
        )
        assets.append(asset)

    # 4) Create a fresh index header
    index_header = VcatTestVectorHeader(
        name="VCAT Test Vector Catalog Index",
        description="Index of all VCAT test vector catalogs",
        created_by=cfg.CREATED_BY
    )

    return VcatTestVectorCatalogIndex(
        vcat_testvector_header=index_header,
        catalogs=assets
    )


def write_index_to_disk(index: VcatTestVectorCatalogIndex):
    """
    Serialize the index to JSON under cfg.BASE_OUTPUT_DIR.
    """
    out_path = cfg.BASE_OUTPUT_DIR / OUTPUT_FILENAME

    with out_path.open("w") as f:
        json.dump(index.to_dict(), f, indent=2)

    print(f"▶️  Index written to {out_path}")


def main():
    index = build_index()
    write_index_to_disk(index)


if __name__ == "__main__":
    main()
