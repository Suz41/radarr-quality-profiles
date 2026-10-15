# Radarr Quality Profiles & Custom Formats

[![Radarr](https://img.shields.io/badge/Radarr-v3%20%7C%20v4%20%7C%20v5%20%7C%20v6-fec107?style=flat-square&logo=radarr&logoColor=white)](https://radarr.video)
[![Python 3](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PowerShell](https://img.shields.io/badge/PowerShell-5.1+-5391fe?style=flat-square&logo=powershell&logoColor=white)](https://github.com/PowerShell/PowerShell)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

A curated collection of production-ready **Radarr Quality Profiles** and **Custom Formats (CF)** engineered for optimal 1080p video fidelity. Tailored specifically for users wanting pristine 1080p Remux/WEB-DL releases with **IMAX Enhanced** framing, **HDR/HDR10+/Dolby Vision**, preferred **English + Hindi Dual Audio**, and automatic elimination of low-quality theatrical CAM/Telesync rips.

Compatible with standalone desktop installs, Docker containers, NAS setups, and mobile hosts like [Fishbowl](https://github.com/Suz41/Fishbowl).

---

## 📑 Repository Structure

```text
radarr-quality-profiles/
├── custom-formats/                      # Individual Radarr-importable CF JSONs
│   ├── imax.json                       # (+300) IMAX Enhanced releases
│   ├── english-hindi-dual-audio.json   # (+300) Dual/Multi audio releases (Eng + Hin)
│   ├── bluray-remux.json               # (+250) Untouched Blu-ray Remux
│   ├── hdr.json                        # (+200) HDR / HDR10 / HDR10+ / HDR10P
│   ├── hdr10plus.json                  # (+100) HDR10+ dynamic metadata
│   ├── web-dl.json                     # (+100) Pure WEB-DL stream captures
│   ├── hevc-h265.json                  # (+40)  H.265 / HEVC efficiency
│   ├── low-quality-release.json        # (-10000) CAM, HDCAM, TS, TC, Screener rejection
│   ├── dolby-vision.json               # (Optional +150) Dolby Vision releases
│   ├── dolby-atmos.json                # (Optional +100) Dolby Atmos audio
│   ├── dts-hd-ma.json                  # (Optional +80)  Lossless DTS-HD MA
│   ├── proper-repack.json              # (Optional +50)  Fixed and repacked releases
│   └── 1080p-imax-hdr-complete.json    # Consolidated all-in-one specification
├── profiles/
│   ├── 1080p-imax-hdr-dual-audio.json  # Setup specification & configuration reference
│   └── radarr-api-profile-payload.json # Direct REST API payload for /api/v3/qualityprofile
├── scripts/
│   ├── import_to_radarr.py             # Python script for 1-click automated API sync
│   └── import_to_radarr.ps1            # PowerShell script for 1-click automated API sync
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🎯 Profile: `1080p IMAX HDR (English + Hindi)`

This profile is designed as the ultimate daily-driver for screens where 4K/2160p is unnecessary or storage-constrained. It enforces a strict **1080p ceiling** while maximizing audio/video quality through Custom Format scoring.

### 1. Quality Tier Hierarchy

| Priority | Quality Tier | State | Notes |
| :---: | :--- | :---: | :--- |
| **1** | **Remux-1080p** | ✅ Allowed | Highest bitrate; zero compression loss |
| **2** | **Bluray-1080p** | ✅ Allowed | **Cutoff Quality** — Upgrades stop once reached |
| **3** | **WEBDL-1080p** | ✅ Allowed | Pristine untouched streaming master |
| **4** | **WEBRip-1080p** | ✅ Allowed | High quality re-encoded web release |
| **5** | **Bluray-720p** | ✅ Allowed | High quality fallback if 1080p is unavailable |
| **6** | **WEBDL-720p** | ✅ Allowed | Fallback streaming release |
| **7** | **WEBRip-720p** | ✅ Allowed | Acceptable minimum fallback |
| — | *HDTV (720p / 1080p)* | ❌ Disabled | Broadcast compression artifacts |
| — | *SDTV / DVD / DVD-R / 480p* | ❌ Disabled | Below target resolution threshold |
| — | *All 2160p / 4K Qualities* | ❌ Disabled | Hard limit; disabled directly in profile |

### 2. Custom Format Scoring Matrix

| Custom Format | Recommended Score | Matching Expression | Objective |
| :--- | :---: | :--- | :--- |
| **IMAX** | `+300` | `(?i)\bIMAX\b` | Expanded aspect ratio & open matte |
| **English + Hindi Dual Audio** | `+300` | `(?i)(DUAL[ ._-]?AUDIO\|MULTI[ ._-]?AUDIO\|HIN[ ._-]?ENG\|...)` | Regional dual audio tracks |
| **Blu-ray Remux** | `+250` | `(?i)\bREMUX\b` | Bit-for-bit disc stream preservation |
| **HDR** | `+200` | `(?i)\b(HDR\|HDR10\|HDR10\+\|HDR10PLUS\|HDR10P)\b` | 10-bit high dynamic range color |
| **HDR10+** | `+100` | `(?i)\b(HDR10\+\|HDR10PLUS\|HDR10P)\b` | Scene-by-scene dynamic tone mapping |
| **WEB-DL** | `+100` | `(?i)\bWEB[ ._-]?DL\b` | Unre-encoded direct digital stream |
| **HEVC / H.265** | `+40` | `(?i)\b(HEVC\|H[ ._-]?265\|X265)\b` | High compression efficiency |
| **Low Quality Release** | `-10000` | `(?i)\b(CAM\|HDCAM\|HDTS\|TELESYNC\|TELECINE\|SCREENER)\b` | Instant discard of poor theater recordings |
| *Dolby Vision* (Optional) | `+150` | `(?i)\b(DV\|DOVI\|DOLBY[ ._-]?VISION)\b` | Advanced Dolby Vision metadata |
| *Dolby Atmos* (Optional) | `+100` | `(?i)\bATMOS\b` | Spatial audio streams |
| *DTS-HD MA* (Optional) | `+80` | `(?i)\bDTS[ ._-]?HD[ ._-]?MA\b` | Lossless physical disc surround audio |
| *Proper / Repack* (Optional) | `+50` | `(?i)\b(PROPER\|REPACK\|RERIP)\b` | Sync/audio fixes over initial uploads |

---

## 🚀 Installation & Setup

### Option A: 1-Click Automated Import (Recommended)

Using the included automated scripts, you can connect to your Radarr instance, import all Custom Formats, and wire up the profile automatically in seconds.

#### Using Python 3:
```bash
# Clone the repository
git clone https://github.com/Suz41/radarr-quality-profiles.git
cd radarr-quality-profiles

# Run the importer with your Radarr API key (found in Settings > General)
python scripts/import_to_radarr.py --url "http://localhost:7878" --api-key "YOUR_RADARR_API_KEY"
```

#### Using PowerShell:
```powershell
# Clone the repository
git clone https://github.com/Suz41/radarr-quality-profiles.git
cd radarr-quality-profiles

# Run the PowerShell importer
.\scripts\import_to_radarr.ps1 -RadarrUrl "http://localhost:7878" -ApiKey "YOUR_RADARR_API_KEY"
```

---

### Option B: Manual Web UI Import

If you prefer configuring Radarr manually through the web dashboard:

#### Step 1: Import Custom Formats
1. Open Radarr and go to **Settings** > **Custom Formats**.
2. Click the **+** (Add) button and select **Import**.
3. Open any JSON file from the [`custom-formats/`](custom-formats/) folder, copy its contents, and paste it into the Radarr text area.
4. Click **Import** and **Save**.
5. Repeat for each custom format you wish to use (`imax.json`, `english-hindi-dual-audio.json`, `hdr.json`, `bluray-remux.json`, etc.).

#### Step 2: Create the Quality Profile
1. Navigate to **Settings** > **Profiles**.
2. Click **+** to add a new profile (or clone `HD-1080p`).
3. Set the **Name** to `1080p IMAX HDR (English + Hindi)`.
4. Ensure **Upgrades Allowed** is checked.
5. In the **Qualities** section:
   - Check only `Remux-1080p`, `Bluray-1080p`, `WEBDL-1080p`, `WEBRip-1080p`, `Bluray-720p`, `WEBDL-720p`, `WEBRip-720p`.
   - Drag to arrange them in order from highest to lowest as listed above.
   - **Uncheck** all 2160p / 4K and SD / 480p qualities.
6. Set the **Upgrade Until (Cutoff)** to `Bluray-1080p`.
7. Scroll down to **Custom Formats** in the profile modal:
   - Add each imported format and assign the scores from the [Scoring Matrix](#2-custom-format-scoring-matrix).
   - Set **Minimum Custom Format Score** to `0`.
8. Click **Save**.

---

## 💡 Best Practices & Technical Notes

1. **Resolution Cap Enforcement:**
   > Do **not** use negative scores to block 2160p releases. Always disable the 2160p qualities directly in the profile's allowed qualities list. This prevents Radarr from considering 4K torrents altogether, saving indexer API requests.

2. **Language Preference Handling:**
   > Radarr's built-in single preferred language setting cannot enforce an "English OR Hindi OR Dual Audio" condition by itself. We recommend setting Radarr's default language to `Original` or `English`, and relying on the `English + Hindi Dual Audio` Custom Format score (`+300`) to prioritize dual audio releases.

3. **Audio Quality Upgrades:**
   > If your audio hardware supports Dolby Atmos or DTS-HD MA, you can enable `dolby-atmos.json` (+100) and `dts-hd-ma.json` (+80) to preference lossless surround sound without requiring higher resolution.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
