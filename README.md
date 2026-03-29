# cli-tools

Personal collection of terminal utilities.

## Tools

| Tool | Description |
|------|-------------|
| `csvview` | Display CSV files as formatted tables in the terminal |
| `fast-monitor` | Monitor and log internet speed using fast.com |
| `speedtest-monitor` | Monitor and log internet speed using speedtest.net |
| `compressimg` | Compress images by percentage or target resolution |

## Install

```bash
git clone https://github.com/prajyot/cli-tools.git
cd cli-tools
./install.sh
```

This copies all tools to `~/.local/bin`. Make sure that directory is in your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Update

```bash
git pull
./install.sh
```

## Usage

### csvview

```bash
csvview data.csv                   # show last 10 rows
csvview data.csv --limit 20        # show last 20 rows
csvview data.csv --limit 0         # show all rows
csvview data.csv --average         # show average row for numeric columns
csvview data.csv --cols a,b        # show specific columns
csvview data.csv --stats           # show min/max/avg stats
csvview data.csv --delimiter ';'   # custom delimiter
```

### fast-monitor

```bash
fast-monitor
```

### speedtest-monitor

```bash
speedtest-monitor
```

### compressimg

```bash
compressimg photo.jpg -s 50%              # shrink to 50% of original dimensions
compressimg photo.jpg -s 1920x1080        # fit within 1920x1080, preserve aspect ratio
compressimg *.png -s 75% -o compressed/  # batch compress PNGs into a folder
compressimg photo.jpg -s 50% --dry-run   # preview without writing files
compressimg photo.jpg -s 50% -q 90       # custom JPEG/WebP quality (default: 85)
compressimg photo.jpg -s 1280x720 --suffix _hd  # custom output filename suffix
compressimg photo.jpg -s 50% --overwrite  # overwrite original file
```
