#!/usr/bin/env python3
"""
Radarr Quality Profile & Custom Formats Auto-Importer
-----------------------------------------------------
Imports curated Custom Formats and creates the '1080p IMAX HDR (English + Hindi)'
Quality Profile directly in your Radarr instance via the REST API.

Usage:
    python import_to_radarr.py --api-key YOUR_API_KEY
    python import_to_radarr.py --url http://192.168.1.100:7878 --api-key YOUR_API_KEY
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_SCORES = {
    "IMAX": 300,
    "English + Hindi Dual Audio": 300,
    "Blu-ray Remux": 250,
    "HDR": 200,
    "HDR10+": 100,
    "WEB-DL": 100,
    "HEVC / H.265": 40,
    "Low Quality Release": -10000,
    "Dolby Vision": 150,
    "Dolby Atmos": 100,
    "DTS-HD MA": 80,
    "Proper / Repack": 50,
}

# Quality definition names to prioritize in order (highest to lowest)
ALLOWED_QUALITIES = [
    "Remux-1080p",
    "Bluray-1080p",
    "WEBDL-1080p",
    "WEBRip-1080p",
    "Bluray-720p",
    "WEBDL-720p",
    "WEBRip-720p",
]

CUTOFF_QUALITY = "Bluray-1080p"


def make_request(url: str, api_key: str, method: str = "GET", data: dict = None) -> dict:
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"[-] HTTP Error {e.code}: {err_msg}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"[-] Request failed: {e}", file=sys.stderr)
        raise


def test_connection(base_url: str, api_key: str):
    url = f"{base_url.rstrip('/')}/api/v3/system/status"
    try:
        status = make_request(url, api_key)
        version = status.get("version", "Unknown")
        print(f"[+] Connected to Radarr v{version}")
    except Exception:
        print("[-] Could not connect to Radarr. Please check URL and API Key.", file=sys.stderr)
        sys.exit(1)


def sync_custom_formats(base_url: str, api_key: str, cf_dir: Path) -> dict:
    """
    Reads all JSON files in custom-formats/ and posts/updates them in Radarr.
    Returns a dict mapping {format_name: format_id}.
    """
    cf_url = f"{base_url.rstrip('/')}/api/v3/customformat"
    existing_cfs = make_request(cf_url, api_key)
    existing_map = {cf["name"]: cf for cf in existing_cfs}

    name_to_id = {}

    for file_path in sorted(cf_dir.glob("*.json")):
        if file_path.name == "1080p-imax-hdr-complete.json":
            # Skip composite all-in-one format during individual scoring setup
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            cf_data = json.load(f)

        name = cf_data.get("name")
        if not name:
            continue

        if name in existing_map:
            cf_id = existing_map[name]["id"]
            cf_data["id"] = cf_id
            update_url = f"{cf_url}/{cf_id}"
            make_request(update_url, api_key, method="PUT", data=cf_data)
            print(f"  [~] Updated Custom Format: {name} (ID: {cf_id})")
            name_to_id[name] = cf_id
        else:
            created = make_request(cf_url, api_key, method="POST", data=cf_data)
            cf_id = created.get("id")
            print(f"  [+] Created Custom Format: {name} (ID: {cf_id})")
            name_to_id[name] = cf_id

    return name_to_id


def sync_quality_profile(base_url: str, api_key: str, cf_name_to_id: dict):
    """
    Creates or updates the 1080p IMAX HDR (English + Hindi) profile.
    """
    profile_url = f"{base_url.rstrip('/')}/api/v3/qualityprofile"
    schema_url = f"{base_url.rstrip('/')}/api/v3/qualityprofile/schema"
    existing_profiles = make_request(profile_url, api_key)

    target_name = "1080p IMAX HDR (English + Hindi)"
    target_profile = next((p for p in existing_profiles if p["name"] == target_name), None)

    if not target_profile:
        # Fetch base schema for standard items
        try:
            target_profile = make_request(schema_url, api_key)
        except Exception:
            # Fall back to using first existing profile structure
            if existing_profiles:
                target_profile = json.loads(json.dumps(existing_profiles[0]))
                target_profile.pop("id", None)
            else:
                print("[-] Could not fetch Quality Profile template schema.", file=sys.stderr)
                return

    target_profile["name"] = target_name
    target_profile["upgradeAllowed"] = True

    # Reorder and filter items
    cutoff_id = None
    items = target_profile.get("items", [])

    # Flatten nested items if any
    for item in items:
        q_name = item.get("quality", {}).get("name", "")
        if q_name in ALLOWED_QUALITIES:
            item["allowed"] = True
            if q_name == CUTOFF_QUALITY:
                cutoff_id = item["quality"]["id"]
        else:
            item["allowed"] = False

    # Sort allowed items according to priority
    def quality_priority(item):
        q_name = item.get("quality", {}).get("name", "")
        if q_name in ALLOWED_QUALITIES:
            return ALLOWED_QUALITIES.index(q_name)
        return 999

    items.sort(key=quality_priority)
    target_profile["items"] = items

    if cutoff_id:
        target_profile["cutoff"] = cutoff_id

    # Configure Custom Format scores
    format_items = []
    for cf_name, cf_id in cf_name_to_id.items():
        score = DEFAULT_SCORES.get(cf_name, 0)
        format_items.append({
            "format": cf_id,
            "name": cf_name,
            "score": score,
        })

    target_profile["formatItems"] = format_items
    target_profile["minFormatScore"] = 0
    target_profile["cutoffFormatScore"] = 0

    if "id" in target_profile and target_profile["id"]:
        pid = target_profile["id"]
        make_request(f"{profile_url}/{pid}", api_key, method="PUT", data=target_profile)
        print(f"[+] Updated Profile: '{target_name}' (ID: {pid})")
    else:
        created = make_request(profile_url, api_key, method="POST", data=target_profile)
        print(f"[+] Created Profile: '{target_name}' (ID: {created.get('id')})")


def main():
    parser = argparse.ArgumentParser(description="Radarr Quality Profile & Custom Formats Importer")
    parser.add_argument("--url", default="http://127.0.0.1:7878", help="Radarr base URL (default: http://127.0.0.1:7878)")
    parser.add_argument("--api-key", required=True, help="Radarr API Key (from Settings > General)")
    parser.add_argument("--cf-dir", default=None, help="Directory containing custom format JSON files")

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    cf_dir = Path(args.cf_dir) if args.cf_dir else repo_root / "custom-formats"

    if not cf_dir.exists():
        print(f"[-] Custom Formats directory not found at: {cf_dir}", file=sys.stderr)
        sys.exit(1)

    print("==================================================")
    print("  Radarr Quality Profile & Formats Auto-Importer  ")
    print("==================================================")
    print(f"URL: {args.url}")
    test_connection(args.url, args.api_key)

    print("\n[*] Syncing Custom Formats...")
    cf_map = sync_custom_formats(args.url, args.api_key, cf_dir)
    print(f"[+] Synced {len(cf_map)} Custom Formats.")

    print("\n[*] Configuring Quality Profile...")
    sync_quality_profile(args.url, args.api_key, cf_map)

    print("\n[✓] Done! Profile and Custom Formats successfully configured in Radarr.")


if __name__ == "__main__":
    main()
