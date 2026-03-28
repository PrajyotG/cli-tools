#!/usr/bin/env python3
import speedtest
import json
import csv
import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "results.csv")


def run_speedtest():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running speed test...")

    st = speedtest.Speedtest()
    st.get_best_server()

    download = st.download() / 1_000_000  # Mbps
    upload = st.upload() / 1_000_000      # Mbps
    ping = st.results.ping

    server = st.results.server
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"  Download : {download:.2f} Mbps")
    print(f"  Upload   : {upload:.2f} Mbps")
    print(f"  Ping     : {ping:.2f} ms")
    print(f"  Server   : {server['name']}, {server['country']}")

    write_header = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "download_mbps", "upload_mbps", "ping_ms", "server"])
        writer.writerow([
            timestamp,
            f"{download:.2f}",
            f"{upload:.2f}",
            f"{ping:.2f}",
            f"{server['name']}, {server['country']}"
        ])

    print(f"  Logged to: {LOG_FILE}")


if __name__ == "__main__":
    run_speedtest()
