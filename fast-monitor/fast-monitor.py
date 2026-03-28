#!/usr/bin/env python3
import re
import os
import csv
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

LOG_FILE = os.path.join(os.path.dirname(__file__), "fast_results.csv")

FAST_COM_URL = "https://fast.com"
FAST_API_URL = "https://api.fast.com/netflix/speedtest/v2"


def get_token():
    """Extract the API token from fast.com's JS bundle."""
    resp = requests.get(FAST_COM_URL, timeout=10)
    match = re.search(r'<script src="(/app-[^"]+\.js)"', resp.text)
    if not match:
        raise RuntimeError("Could not find fast.com JS bundle")
    js = requests.get(FAST_COM_URL + match.group(1), timeout=10).text
    token_match = re.search(r'token:"([^"]+)"', js)
    if not token_match:
        raise RuntimeError("Could not extract fast.com token")
    return token_match.group(1)


def get_targets(token, count=5):
    resp = requests.get(FAST_API_URL, params={"https": "true", "token": token, "urlCount": count}, timeout=10)
    data = resp.json()
    urls = [t["url"] for t in data["targets"]]
    location = data["targets"][0].get("location", {})
    server = f"{location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}"
    return urls, server


def measure_download(urls, duration=10):
    total = [0]
    start = time.monotonic()
    deadline = start + duration

    def fetch(url):
        try:
            with requests.get(url, stream=True, timeout=duration + 5) as r:
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if time.monotonic() >= deadline:
                        break
                    total[0] += len(chunk)
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=len(urls)) as ex:
        list(as_completed([ex.submit(fetch, u) for u in urls]))

    elapsed = min(time.monotonic() - start, duration)
    return (total[0] * 8) / elapsed / 1_000_000  # Mbps


def measure_upload(urls, duration=10):
    total = [0]
    start = time.monotonic()
    deadline = start + duration
    payload = b"x" * (256 * 1024)  # 256 KB

    def post(url):
        try:
            while time.monotonic() < deadline:
                requests.post(url, data=payload, timeout=duration + 5)
                total[0] += len(payload)
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=len(urls)) as ex:
        list(as_completed([ex.submit(post, u) for u in urls]))

    elapsed = min(time.monotonic() - start, duration)
    return (total[0] * 8) / elapsed / 1_000_000  # Mbps


def measure_ping(url, samples=5):
    """Measure latency using a 1-byte range request for true TTFB."""
    times = []
    for _ in range(samples):
        try:
            start = time.monotonic()
            requests.get(url, headers={"Range": "bytes=0-0"}, timeout=5)
            times.append((time.monotonic() - start) * 1000)
        except Exception:
            pass
    return min(times) if times else 0.0


def run_speedtest():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Running fast.com speed test...")

    print("  Fetching test servers...")
    token = get_token()
    urls, server = get_targets(token)

    print("  Measuring ping...")
    ping = measure_ping(urls[0])

    print("  Measuring download...")
    download = measure_download(urls)

    print("  Measuring upload...")
    upload = measure_upload(urls)

    print(f"  Download : {download:.2f} Mbps")
    print(f"  Upload   : {upload:.2f} Mbps")
    print(f"  Ping     : {ping:.2f} ms")
    print(f"  Server   : {server}")

    write_header = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "download_mbps", "upload_mbps", "ping_ms", "server"])
        writer.writerow([timestamp, f"{download:.2f}", f"{upload:.2f}", f"{ping:.2f}", server])

    print(f"  Logged to: {LOG_FILE}")


if __name__ == "__main__":
    run_speedtest()
