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

"""
Unified VCAT Test Vector Builder

Generates video manifests, playlists, and catalog from a folder containing
a 'media' subfolder with video assets.

Usage:
    python vcat_testvector_builder.py --input-folder /path/to/folder
    python vcat_testvector_builder.py --input-folder /path/to/folder --created-by "Your Name"
    python vcat_testvector_builder.py --codec av1                    # Only process media/av1 videos
    python vcat_testvector_builder.py --codec av1 --append_index     # Process av1 and append to existing index
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import settings as cfg
from vcat_testvector_datamodels import (
    VcatTestVectorHeader,
    VcatTestVectorVideoAsset,
    VcatTestVectorPlaylistAsset,
    VcatTestVectorPlaylistManifest,
    VcatTestVectorPlaylistCatalog,
    VcatTestVectorCatalogAsset,
    VcatTestVectorCatalogIndex,
)
from utils import getChecksum, getFileLength


class BuilderConfig:
    """Configuration for the builder, populated from CLI args and defaults."""

    DEFAULT_CATALOG_FILENAME = "vcat_testvector_playlist_catalog.json"

    def __init__(
        self,
        input_folder: Optional[Path] = None,
        created_by: Optional[str] = None,
        catalog_filename: Optional[str] = None,
        description: Optional[str] = None,
        codec: Optional[str] = None,
        append_index: bool = False,
        catalog_name: Optional[str] = None,
    ):
        self.input_folder = Path(input_folder).expanduser().resolve() if input_folder else cfg.BASE_OUTPUT_DIR
        # Output is always in input folder (relative paths require this)
        self.output_dir = self.input_folder
        self.manifest_dir = self.input_folder / "manifests"
        self.created_by = created_by or cfg.CREATED_BY
        self.codec = codec
        self.append_index = append_index

        # Set catalog filename based on codec if specified
        if catalog_filename:
            self.catalog_filename = catalog_filename
        elif codec:
            self.catalog_filename = f"vcat_{codec}_testvector_playlist_catalog.json"
        else:
            self.catalog_filename = cfg.CATALOG_FILENAME

        self.description = description or cfg.CATALOG_DESCRIPTION
        # Derive catalog name - VCAT and codec are uppercase, rest is title case
        if catalog_name:
            self.catalog_name = catalog_name
        elif codec:
            self.catalog_name = f"VCAT {codec.upper()} Testvector Playlist Catalog"
        else:
            self.catalog_name = Path(self.catalog_filename).stem.replace("_", " ").title()
        self.index_name = "VCAT Test Vector Catalog Index"
        self.index_description = "Index of all VCAT test vector catalogs"

    @property
    def media_folder(self) -> Path:
        if self.codec:
            return self.input_folder / "media" / self.codec
        return self.input_folder / "media"


# -----------------------------------------------------------------------------
# Video Manifest Generation
# -----------------------------------------------------------------------------

def get_video_files_from_folder(media_folder: Path) -> List[Path]:
    """Return list of video files under the media folder."""
    if not media_folder.exists():
        raise FileNotFoundError(f"Media folder does not exist: {media_folder}")

    if not os.access(media_folder, os.R_OK | os.X_OK):
        raise PermissionError(f"Cannot read media folder: {media_folder}")

    video_files = []
    for root, dirs, files in os.walk(media_folder):
        # Skip macOS artifacts
        dirs[:] = [d for d in dirs if d not in ('.DS_Store', '__MACOSX')]
        for name in files:
            if name == '.DS_Store':
                continue
            video_files.append(Path(root) / name)

    return video_files


def _ffprobe_video(file_path: Path, count_packets: bool = False) -> dict:
    """Run ffprobe on the first video stream and return the parsed JSON."""
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0"]
    if count_packets:
        cmd.append("-count_packets")
    cmd += [
        "-show_entries",
        "stream=codec_name,codec_tag_string,width,height,r_frame_rate,duration,nb_read_packets:format=duration",
        "-of", "json", str(file_path),
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return json.loads(result.stdout)


def _to_float(value) -> Optional[float]:
    try:
        f = float(value)
        return f if f > 0 else None
    except (TypeError, ValueError):
        return None


def get_video_details(file_path: Path) -> tuple:
    """Get video codec, duration, resolution, and frame rate using ffprobe.

    Raw elementary streams (e.g. .266) carry no container duration, so the
    duration is derived from the packet count and frame rate in that case.
    """
    try:
        info = _ffprobe_video(file_path)
        stream = (info.get("streams") or [{}])[0]

        # Detect codec
        codec_name = stream.get("codec_name", "")
        # FFmpeg has no AV2 decoder yet, so fall back to the IVF fourcc
        codec_tag = stream.get("codec_tag_string", "").upper()
        if codec_name == "av2" or codec_tag == "AV02":
            codec = "video/av2"
        elif codec_name == "av1":
            codec = "video/av1"
        elif codec_name == "vp9":
            codec = 'video/mp4; codecs="vp09"'
        elif codec_name == "vvc":
            codec = 'video/mp4; codecs="vvc"'
        else:
            codec = "Unknown"

        # Extract resolution
        resolution_x_y = None
        if stream.get("width") and stream.get("height"):
            resolution_x_y = f"{stream['width']}X{stream['height']}"

        # Extract frame rate
        fps = None
        num, _, den = stream.get("r_frame_rate", "0/0").partition("/")
        if _to_float(num) and _to_float(den or "1"):
            fps = float(num) / float(den or "1")
        frame_rate = f"{round(fps, 3):g}" if fps else "unknown"

        # Extract duration
        duration_s = _to_float(info.get("format", {}).get("duration")) or _to_float(stream.get("duration"))
        if duration_s is None and fps:
            counted = (_ffprobe_video(file_path, count_packets=True).get("streams") or [{}])[0]
            packets = _to_float(counted.get("nb_read_packets"))
            if packets:
                duration_s = packets / fps
        duration_ms = round(duration_s * 1000) if duration_s else None

        return codec, duration_ms, resolution_x_y, frame_rate

    except Exception as e:
        print(f"Error getting video details: {e}")
        return "unknown", "unknown", "unknown", "unknown"


def generate_header_title(video_file: str, video_mime_type: str, resolution_x_y: str, frame_rate: str) -> str:
    """Generate a descriptive title for the video manifest header."""
    base_name = ""

    if 'av1' in video_mime_type.lower():
        base_name = f"av1-{resolution_x_y}p{frame_rate}fps"
    elif 'av2' in video_mime_type.lower():
        base_name = f"av2-{resolution_x_y}p{frame_rate}fps"
    elif 'vvc' in video_mime_type.lower():
        base_name = f"vvc-{resolution_x_y}p{frame_rate}fps"
    elif 'vp09' in video_mime_type.lower():
        base_name = f"vp9-{resolution_x_y}p{frame_rate}fps"

    if not base_name:
        base_name = Path(video_file).stem

    # Handle film grain suffix
    for suffix in ('fd0', 'fd1', 'fd2'):
        if suffix in video_file:
            base_name += f'-{suffix}'
            break

    # Handle bitrate ladder suffix (e.g. "_br0.5_") so rungs get unique names
    br_match = re.search(r"_br(\d+(?:\.\d+)?)", Path(video_file).stem)
    if br_match:
        base_name += f"-br{br_match.group(1)}"

    return base_name


def generate_video_manifest(video_path: Path, config: BuilderConfig) -> Optional[Path]:
    """Generate a video manifest for a single video file."""
    try:
        checksum = getChecksum(str(video_path))
        length_bytes = getFileLength(str(video_path))
        video_mime_type, duration_ms, resolution_x_y, frame_rate = get_video_details(video_path)

        # Build relative URL from manifest to media file
        rel_path = video_path.relative_to(config.input_folder)
        video_url = f"../{rel_path}"

        header_title = generate_header_title(str(video_path), video_mime_type, resolution_x_y, frame_rate)
        header_description = (
            f"VCAT Test asset: {video_mime_type}, "
            f"{resolution_x_y}, {frame_rate}fps, {duration_ms}ms"
        )

        header = VcatTestVectorHeader(header_title, header_description, config.created_by)

        media_asset = VcatTestVectorVideoAsset(
            name=video_path.name,
            url=video_url,
            checksum=checksum,
            length_bytes=length_bytes,
            video_mime_type=video_mime_type,
            duration_ms=duration_ms,
            resolution_x_y=resolution_x_y,
            frame_rate=frame_rate
        )

        manifest = {
            "vcat_testvector_header": header.to_dict(),
            "media_asset": media_asset.to_dict()
        }

        out_path = config.manifest_dir / f"{video_path.name}_video_manifest.json"
        with out_path.open("w") as f:
            json.dump(manifest, f, indent=2)

        print(f"  ✔ {out_path.name}")
        return out_path

    except Exception as e:
        print(f"  ✗ Error processing {video_path.name}: {e}")
        return None


# -----------------------------------------------------------------------------
# Playlist Generation
# -----------------------------------------------------------------------------

def generate_playlist_from_manifest(manifest_path: Path, config: BuilderConfig) -> Optional[Path]:
    """Generate a playlist from a video manifest."""
    try:
        with manifest_path.open("r") as f:
            video_manifest = json.load(f)

        header = video_manifest["vcat_testvector_header"]
        ma = video_manifest["media_asset"]

        if "video_mime_type" not in ma:
            print(f"  → Skipping {manifest_path.name}, not a video manifest")
            return None

        manifest_checksum = getChecksum(str(manifest_path))
        asset_url = f"./manifests/{manifest_path.name}"

        playlist_asset = VcatTestVectorPlaylistAsset(
            name=header["name"],
            url=asset_url,
            checksum=manifest_checksum,
            length_bytes=manifest_path.stat().st_size,
            uuid=header["uuid"],
            description=header["description"]
        )

        playlist_header = VcatTestVectorHeader(
            name=header["name"],
            description=f"Playlist for {header['name']}",
            created_by=config.created_by
        )

        playlist_manifest = VcatTestVectorPlaylistManifest(
            vcat_testvector_header=playlist_header,
            media_assets=[playlist_asset]
        )

        video_name = manifest_path.name.removesuffix("_video_manifest.json")
        out_path = config.manifest_dir / f"{video_name}_playlist.json"
        with out_path.open("w") as f:
            json.dump(playlist_manifest.to_dict(), f, indent=2)

        print(f"  ✔ {out_path.name}")
        return out_path

    except Exception as e:
        print(f"  ✗ Error generating playlist from {manifest_path.name}: {e}")
        return None


# -----------------------------------------------------------------------------
# Catalog Generation
# -----------------------------------------------------------------------------

def generate_catalog(config: BuilderConfig, playlist_files: List[Path]) -> Optional[Path]:
    """Generate catalog from the given playlists."""
    playlist_files = sorted(playlist_files)

    if not playlist_files:
        print("  ✗ No playlist files found")
        return None

    assets: List[VcatTestVectorPlaylistAsset] = []

    for p in playlist_files:
        try:
            data = json.loads(p.read_text())
            hdr = data["vcat_testvector_header"]

            checksum = getChecksum(str(p))
            length_bytes = p.stat().st_size
            rel_url = f"./manifests/{p.name}"

            asset = VcatTestVectorPlaylistAsset(
                name=hdr["name"],
                url=rel_url,
                checksum=checksum,
                length_bytes=length_bytes,
                uuid=hdr["uuid"],
                description=hdr["description"]
            )
            assets.append(asset)
        except Exception as e:
            print(f"  ✗ Error reading playlist {p.name}: {e}")

    catalog_header = VcatTestVectorHeader(
        name=config.catalog_name,
        description=config.description,
        created_by=config.created_by
    )

    catalog = VcatTestVectorPlaylistCatalog(
        vcat_testvector_header=catalog_header,
        playlists=assets
    )

    out_path = config.output_dir / config.catalog_filename
    with out_path.open("w") as f:
        json.dump(catalog.to_dict(), f, indent=2)

    print(f"  ✔ {out_path.name}")
    return out_path


# -----------------------------------------------------------------------------
# Index Generation
# -----------------------------------------------------------------------------

def generate_index(catalog_path: Path, config: BuilderConfig) -> Optional[Path]:
    """Generate catalog index from the catalog."""
    if not catalog_path or not catalog_path.exists():
        print("  ✗ No catalog file to index")
        return None

    try:
        data = json.loads(catalog_path.read_text())

        # Verify it has playlists section
        if "playlists" not in data:
            print(f"  ✗ Catalog missing 'playlists' section")
            return None

        hdr = data["vcat_testvector_header"]
        checksum = getChecksum(str(catalog_path))
        length_bytes = catalog_path.stat().st_size
        rel_url = f"./{catalog_path.name}"

        asset = VcatTestVectorCatalogAsset(
            name=hdr["name"],
            url=rel_url,
            checksum=checksum,
            length_bytes=length_bytes,
            uuid=hdr["uuid"],
            description=hdr["description"]
        )

        out_path = config.output_dir / "vcat_testvector_catalog_index.json"

        # Check if we should append to existing index
        existing_catalogs = []
        existing_header = None
        if config.append_index and out_path.exists():
            try:
                existing_data = json.loads(out_path.read_text())
                existing_catalogs = existing_data.get("catalogs", [])
                existing_header = existing_data.get("vcat_testvector_header")
                print(f"  → Appending to existing index with {len(existing_catalogs)} catalog(s)")
            except Exception as e:
                print(f"  → Warning: Could not read existing index, creating new: {e}")

        # Replace any existing entry with the same URL in place, otherwise append
        all_catalogs = [asset.to_dict() if c.get("url") == rel_url else c for c in existing_catalogs]
        if not any(c.get("url") == rel_url for c in existing_catalogs):
            all_catalogs.append(asset.to_dict())

        if existing_header:
            index_dict = {"vcat_testvector_header": existing_header}
        else:
            index_header = VcatTestVectorHeader(
                name=config.index_name,
                description=config.index_description,
                created_by=config.created_by
            )
            index = VcatTestVectorCatalogIndex(
                vcat_testvector_header=index_header,
                catalogs=[]  # We'll set catalogs manually to preserve existing entries
            )
            index_dict = index.to_dict()
        index_dict["catalogs"] = all_catalogs

        with out_path.open("w") as f:
            json.dump(index_dict, f, indent=2)

        print(f"  ✔ {out_path.name}")
        return out_path

    except Exception as e:
        print(f"  ✗ Error generating index: {e}")
        return None


# -----------------------------------------------------------------------------
# Main Pipeline
# -----------------------------------------------------------------------------

def build(config: BuilderConfig):
    """Run the full build pipeline."""
    # Validate input folder
    if not config.input_folder.exists():
        print(f"Error: Input folder does not exist: {config.input_folder}")
        sys.exit(1)

    if not config.media_folder.exists():
        print(f"Error: Input folder must contain a 'media' subfolder: {config.media_folder}")
        sys.exit(1)

    # Create manifest directory only after validation
    config.manifest_dir.mkdir(parents=True, exist_ok=True)

    print(f"Building from: {config.input_folder}")
    print()

    # Step 1: Generate video manifests
    print("Step 1: Generating video manifests...")
    video_files = get_video_files_from_folder(config.media_folder)
    print(f"  Found {len(video_files)} video file(s)")

    manifest_paths = []
    for video_path in video_files:
        result = generate_video_manifest(video_path, config)
        if result:
            manifest_paths.append(result)
    print()

    # Step 2: Generate playlists
    print("Step 2: Generating playlists...")
    playlist_paths = []
    for manifest_path in manifest_paths:
        result = generate_playlist_from_manifest(manifest_path, config)
        if result:
            playlist_paths.append(result)
    print()

    # Step 3: Generate catalog
    print("Step 3: Generating catalog...")
    catalog_path = generate_catalog(config, playlist_paths)
    print()

    # Step 4: Generate index
    print("Step 4: Generating catalog index...")
    index_path = generate_index(catalog_path, config)
    print()

    # Summary
    print("Build complete!")
    print(f"  Video manifests: {len(manifest_paths)}")
    print(f"  Playlists: {len(playlist_paths)}")
    print(f"  Catalog: {catalog_path}")
    print(f"  Index: {index_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build VCAT test vector manifests, playlists, and catalog from a folder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                                # Use defaults from settings.py
  %(prog)s --input-folder /path/to/folder
  %(prog)s --input-folder /path/to/folder --created-by "Your Name"
  %(prog)s --input-folder /path/to/folder --catalog-filename my_catalog.json --description "My test vectors"
  %(prog)s --codec av1                                    # Only process media/av1 videos
  %(prog)s --codec av1 --append_index                     # Process av1 and append to existing index
        """
    )

    parser.add_argument(
        "--input-folder",
        type=str,
        default=None,
        help=f"Path to folder containing a 'media' subfolder with video assets (default: {cfg.BASE_OUTPUT_DIR})"
    )

    parser.add_argument(
        "--created-by",
        type=str,
        default=None,
        help=f"Creator attribution (default: {cfg.CREATED_BY})"
    )

    parser.add_argument(
        "--catalog-filename",
        type=str,
        default=None,
        help=f"Output filename for the catalog (default: {BuilderConfig.DEFAULT_CATALOG_FILENAME})"
    )

    parser.add_argument(
        "--description",
        type=str,
        default=None,
        help="Description for the catalog"
    )

    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Display name for the catalog (default: derived from codec or catalog filename)"
    )

    parser.add_argument(
        "--codec",
        type=str,
        default=None,
        help="Only process videos in media/<codec> subfolder. Catalog will be named vcat_<codec>_testvector_playlist_catalog.json"
    )

    parser.add_argument(
        "--append_index",
        action="store_true",
        help="Append to existing index file instead of overwriting"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    config = BuilderConfig(
        input_folder=args.input_folder,
        created_by=args.created_by,
        catalog_filename=args.catalog_filename,
        description=args.description,
        codec=args.codec,
        append_index=args.append_index,
        catalog_name=args.name,
    )

    build(config)


if __name__ == "__main__":
    main()
