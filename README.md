# VCAT Test Vector Builder

A tool for generating VCAT (Video Codec Assessment Technology) test vector manifests, playlists, and catalogs from local video assets.

## Overview

This tool processes a folder of video files and generates a structured set of JSON manifests that describe the video assets, organized into playlists and a catalog index.

## Folder Structure

Start with a folder containing a `media` subfolder. Within the `media` subfolder, place your video assets, typically organized by codec type:

```
my_test_vectors/
├── media/
│   ├── av1/
│   │   ├── video1.mp4
│   │   └── video2.mp4
│   ├── vp9/
│   │   ├── video3.mp4
│   │   └── video4.mp4
│   └── vvc/
│       └── video5.mp4
```

After running the builder, the output structure will be:

```
my_test_vectors/
├── media/
│   └── ... (your video files)
├── manifests/
│   ├── video1.mp4_video_manifest.json
│   ├── video1.mp4_playlist.json
│   └── ... (manifest for each video)
├── vcat_testvector_playlist_catalog.json
└── vcat_testvector_catalog_index.json
```

## Requirements

- Python 3.9+
- FFmpeg (must be installed and available in PATH)

## Usage

### Basic Usage

Run with defaults from `settings.py`:

```bash
python3 vcat_testvector_builder.py
```

### With Parameters

```bash
python3 vcat_testvector_builder.py --input-folder /path/to/folder --catalog-filename my_catalog.json --description "My test vectors"
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--input-folder` | Path to folder containing the `media` subfolder | Value from `settings.py` |
| `--catalog-filename` | Output filename for the catalog JSON | `vcat_testvector_playlist_catalog.json` |
| `--description` | Description text for the catalog | `VCAT test vector playlist catalog` |
| `--created-by` | Creator attribution in metadata | `RoncaTech, LLC` |

### Configuration via settings.py

You can also set defaults by editing `settings.py`:

```python
BASE_OUTPUT_DIR = Path.home() / "Downloads" / "my_test_vectors"
CATALOG_FILENAME = "my_catalog.json"
CATALOG_DESCRIPTION = "My custom description"
CREATED_BY = "Your Name"
```

## Output Files

The builder generates:

1. **Video Manifests** (`*_video_manifest.json`) - Metadata for each video file including codec, resolution, duration, frame rate, and checksum
2. **Playlists** (`*_playlist.json`) - Wrapper manifests that reference video manifests
3. **Catalog** (`vcat_testvector_playlist_catalog.json`) - Index of all playlists
4. **Catalog Index** (`vcat_testvector_catalog_index.json`) - Top-level index of catalogs

## Supported Codecs

The tool automatically detects and labels:
- AV1
- VP9
- VVC

Other codecs will be labeled as "Unknown".

## Disclaimer of Suitability

vcat-test-vectors is provided for general benchmarking and evaluation purposes only. RoncaTech makes no representations or guarantees that vcat-test-vectors is suitable for any particular purpose, environment, or workflow. You are solely responsible for determining whether vcat-test-vectors meets your needs. Under no circumstances should reliance on vcat-test-vectors substitute for your own testing, validation, or professional judgment.

## Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT WILL RONCATECH, LLC OR ITS AFFILIATES, CONTRIBUTORS, OR SUPPLIERS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO LOSS OF PROFITS, REVENUE, DATA, OR USE, ARISING OUT OF OR IN CONNECTION WITH YOUR USE OF VCAT-TEST-VECTORS, EVEN IF RONCATECH HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

You agree that your sole and exclusive remedy for any claim under or related to vcat-test-vectors will be to discontinue use of the software.

## Patent Notice (No Patent Rights Granted)

vcat-test-vectors is distributed under GPL-3.0-or-later. Nothing in this README, the source code, or the license grants you any rights under third-party patents, including without limitation patents essential to implement or use media codecs and container formats (e.g., AVC/H.264, HEVC/H.265, VVC/H.266, MPEG-2, AAC, etc.).

- You are solely responsible for determining whether your use, distribution, or deployment of vcat-test-vectors requires patent licenses from any third party (including patent pools or individual patent holders) and for obtaining any such licenses.
- Contributions to this project may include a limited patent grant from contributors as specified by GPL-3.0-or-later, but no additional patent rights are provided, and no rights are granted on behalf of any third party.
- Use of bundled or integrated decoders/parsers does not imply or provide patent clearance for any jurisdiction. Your compliance with all applicable intellectual property laws remains your responsibility.

## License

vcat-test-vectors is licensed under GPL-3.0-or-later.

See: https://www.gnu.org/licenses/gpl-3.0.html

Contact us for commercial licensing if you can't use GPL.

Use of the VCAT logo and artwork is permitted when discussing, documenting, demonstrating, or promoting VCAT itself. Any other usage requires prior written permission from RoncaTech LLC.

Contact: https://www.roncatech.com/contact
