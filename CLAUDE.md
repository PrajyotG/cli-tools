# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal collection of 4 Python 3 CLI tools installed to `~/.local/bin` via `install.sh`:

| Tool | Purpose |
|------|---------|
| `csvview` | Display CSV files as formatted tables in the terminal |
| `fast-monitor` | Monitor and log internet speed via fast.com |
| `speedtest-monitor` | Monitor and log internet speed via speedtest.net |
| `compressimg` | Compress images by percentage or target resolution |

## Installation

```bash
./install.sh   # copies all tools to ~/.local/bin and makes them executable
```

## Running Tools

Each tool is a single Python script that can be run directly:

```bash
python3 csvview/csvview.py data.csv
python3 fast-monitor/fast-monitor.py
python3 speedtest-monitor/speedtest-monitor.py
python3 compressimg/compressimg.py image.jpg 50%
```

## Dependencies

- **csvview**: stdlib only
- **fast-monitor**: `requests`
- **speedtest-monitor**: `speedtest` (speedtest-cli)
- **imgcompress**: `Pillow`

Install deps: `pip install requests speedtest-cli Pillow`

## Architecture

Each tool lives in its own subdirectory as a **single self-contained Python file** — no packages, no shared code between tools, no build steps. New tools should follow this same pattern.

### csvview
Reads CSV via stdlib `csv`, formats output with Unicode box-drawing characters. Defaults to last 10 rows. Numeric vs text columns are auto-detected for alignment. Key functions build a column-width map, then render header/rows/stats in separate passes.

### fast-monitor
Extracts API token by fetching fast.com's JS bundle, then hits the API for server URLs. Uses `concurrent.futures.ThreadPoolExecutor` for parallel download/upload streams to measure throughput. Logs each run appended to `fast-monitor/fast_results.csv`.

### speedtest-monitor
Thin wrapper around the `speedtest` library — finds best server, runs test, appends row to `speedtest-monitor/results.csv`.

### compressimg
Uses `Pillow`. Accepts scale as `50%` or `1920x1080` (maintains aspect ratio). Format-specific save options: JPEG uses progressive+optimize, PNG uses compression level 9, WebP uses method=6. Supports batch glob patterns and dry-run mode.
