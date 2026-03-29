#!/usr/bin/env bash
set -e

INSTALL_DIR="$HOME/.local/bin"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$INSTALL_DIR"

install_tool() {
    local src="$1"
    local name="$2"
    cp "$src" "$INSTALL_DIR/$name"
    chmod +x "$INSTALL_DIR/$name"
    echo "  installed: $name -> $INSTALL_DIR/$name"
}

echo "Installing cli-tools to $INSTALL_DIR..."

install_tool "$REPO_DIR/csvview/csvview.py"                       csvview
install_tool "$REPO_DIR/fast-monitor/fast-monitor.py"             fast-monitor
install_tool "$REPO_DIR/speedtest-monitor/speedtest-monitor.py"   speedtest-monitor
install_tool "$REPO_DIR/compressimg/compressimg.py"               compressimg

# Warn if INSTALL_DIR is not in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "  WARNING: $INSTALL_DIR is not in your PATH."
    echo "  Add this to your ~/.zshrc or ~/.bashrc:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "Done."
