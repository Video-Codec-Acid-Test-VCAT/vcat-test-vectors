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
