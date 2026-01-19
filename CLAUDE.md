# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VCAT (Video Codec Assessment Technology) test vector generation system. Produces JSON manifests, playlists, and catalogs for video test assets. Supports both local filesystem and AWS S3 storage with relative URLs for portability.

## Build Pipeline

The system operates as a sequential pipeline where each stage produces input for the next:

```bash
# 1. Generate video manifests from media files (requires FFmpeg)
python vcat_testvector_video_builder.py

# 2. Generate playlists from video manifests
python vcat_testvector_playlist_builder.py

# 3. Generate catalog from playlists
python vcat_testvector_catalog_builder.py

# 4. Generate master index from catalogs
python vcat_testvector_index_builder.py
```

Validation scripts:
```bash
python validate_vcat_manifests.py        # Validate S3 manifests
python validate_vcat_test_vector_catalog.py  # Validate catalog entries
```

## Architecture

### Data Flow
```
Video Files (local/S3)
    ↓ vcat_testvector_video_builder.py
manifests/*_video_manifest.json
    ↓ vcat_testvector_playlist_builder.py
manifests/*_playlist.json
    ↓ vcat_testvector_catalog_builder.py
vcat_testvector_playlist_catalog.json
    ↓ vcat_testvector_index_builder.py
index.json
```

### Core Files
- **settings.py**: All configuration (paths, S3 bucket, output directories)
- **vcat_testvector_datamodels.py**: Dataclass definitions with `.to_dict()` serialization
- **utils.py**: S3 download, SHA256 checksum, file size utilities

### Key Design Patterns
- **Dispatch pattern**: `get_video_files()` handles S3/local paths uniformly via URL prefix detection (s3://, file://, local paths)
- **Relative URLs**: Manifests use `../media/` and `manifests/` relative paths for storage-agnostic operation
- **Dataclasses with serialization**: All models have `.to_dict()` methods for JSON output
- **Checksums everywhere**: SHA256 for all assets and manifests

### Output Locations
- Video/playlist manifests: `./manifests/` (relative to script)
- Catalog/index: `~/Downloads/roncatech_testvector_index/`

## Dependencies

**External tools**: FFmpeg (for video probing)

**Python packages** (not in requirements.txt): boto3, requests

**AWS**: S3 bucket "roncatech-vcat-test-vectors" in us-west-2. Requires AWS credentials configured.

## Platform Notes

- Handles macOS TCC permissions for file access
- Supports path expansion (~, environment variables)
- Filters .DS_Store and __MACOSX artifacts
