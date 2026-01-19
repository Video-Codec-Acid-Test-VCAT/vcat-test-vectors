#!/usr/bin/env python3
"""
Video manifest builder - generates manifests for video files in a local folder.
"""
import os
import json
import subprocess
import re

import vcat_testvector_datamodels
from utils import getChecksum, getFileLength
import settings as cfg


def get_video_files_from_folder(folderpath):
    """
    Return a list of files under '<folderpath>/media'.
    """
    folderpath = os.path.expanduser(os.path.expandvars(os.fspath(folderpath)))
    base = os.path.normpath(folderpath)
    media_folder = os.path.join(base, "media")

    if not os.path.isdir(media_folder):
        print(f"Error: Media folder does not exist: {media_folder}")
        return []

    if not os.access(media_folder, os.R_OK | os.X_OK):
        print(f"Error: Cannot read media folder: {media_folder}")
        return []

    video_files = []
    for root, dirs, files in os.walk(media_folder):
        dirs[:] = [d for d in dirs if d not in ('.DS_Store', '__MACOSX')]
        for name in files:
            if name == '.DS_Store':
                continue
            relative = os.path.join("media", os.path.relpath(root, media_folder))
            video_files.append(os.path.join(relative, name))

    return video_files


def get_video_details(file_path):
    """
    Get video codec, duration, resolution, and frame rate using FFmpeg.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", file_path],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        stderr_output = result.stderr

        # Detect codec
        if "Video: av1" in stderr_output:
            codec = "video/av1"
        elif "Video: vp9" in stderr_output:
            codec = 'video/mp4; codecs="vp09"'
        elif "Video: vvc" in stderr_output:
            codec = 'video/mp4; codecs="vvc"'
        else:
            codec = "Unknown"

        # Extract duration
        duration_ms = None
        duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", stderr_output)
        if duration_match:
            hours = int(duration_match.group(1))
            minutes = int(duration_match.group(2))
            seconds = int(duration_match.group(3))
            milliseconds = int(duration_match.group(4)) * 10
            duration_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds

        # Extract resolution
        resolution_x_y = None
        resolution_match = re.search(r", (\d+)x(\d+),", stderr_output)
        if resolution_match:
            resolution_x_y = f"{resolution_match.group(1)}X{resolution_match.group(2)}"

        # Extract frame rate
        frame_rate = "unknown"
        frame_rate_match = re.search(r"(\d+(\.\d+)?) fps", stderr_output)
        if frame_rate_match:
            frame_rate = f"{float(frame_rate_match.group(1)):g}"

        return codec, duration_ms, resolution_x_y, frame_rate

    except Exception as e:
        print(f"Error getting video details: {e}")
        return "unknown", "unknown", "unknown", "unknown"


def generate_header_title(video_file, video_mime_type, resolution_x_y, frame_rate):
    """Generate a descriptive title for the video manifest header."""
    base_name = ""

    if 'av1' in video_mime_type.lower():
        base_name = f"av1-{resolution_x_y}p{frame_rate}fps"
    elif 'vvc' in video_mime_type.lower():
        base_name = f"vvc-{resolution_x_y}p{frame_rate}fps"
    elif 'vp09' in video_mime_type.lower():
        base_name = f"vp9-{resolution_x_y}p{frame_rate}fps"

    if not base_name:
        base_name = video_file.split('/')[-1]

    # Handle film grain suffix
    for suffix in ('fd0', 'fd1', 'fd2'):
        if suffix in video_file:
            base_name += f'-{suffix}'
            break

    return base_name


def generate_video_manifest(video_file, base_folder, created_by):
    """Generate a video manifest for a local video file."""
    local_file = os.path.join(base_folder, video_file)
    video_url = f"../{video_file}"

    try:
        checksum = getChecksum(local_file)
        length_bytes = getFileLength(local_file)
        video_mime_type, duration_ms, resolution_x_y, frame_rate = get_video_details(local_file)

        header_title = generate_header_title(video_file, video_mime_type, resolution_x_y, frame_rate)
        header_description = (
            f"VCAT Test asset: {video_mime_type}, "
            f"{resolution_x_y}, {frame_rate}fps, {duration_ms}ms"
        )
        header = vcat_testvector_datamodels.VcatTestVectorHeader(
            header_title, header_description, created_by
        )

        media_asset = vcat_testvector_datamodels.VcatTestVectorVideoAsset(
            video_file, video_url,
            checksum, length_bytes,
            video_mime_type, duration_ms,
            resolution_x_y, frame_rate
        )

        test_vector = {
            "vcat_testvector_header": header.to_dict(),
            "media_asset": media_asset.to_dict()
        }

        clean_name = video_file.split("/")[-1]
        out = f"{cfg.MANIFEST_DIR}/{clean_name}_video_manifest.json"
        with open(out, "w") as f:
            json.dump(test_vector, f, indent=4)
        print(f"✔ Wrote {out}")

    except Exception as e:
        print(f"Error during manifest generation: {e}")


def main():
    base_folder = cfg.BASE_OUTPUT_DIR
    created_by = cfg.CREATED_BY

    # Ensure manifest directory exists
    cfg.MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    video_files = get_video_files_from_folder(base_folder)
    print(f"Found {len(video_files)} video file(s)")

    for video_file in video_files:
        generate_video_manifest(video_file, base_folder, created_by)


if __name__ == "__main__":
    main()
