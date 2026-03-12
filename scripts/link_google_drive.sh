#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# AARI-NEXUS Google Drive Linker
# Run this after signing into Google Drive for Desktop
#
# Usage:
#   bash scripts/link_google_drive.sh
# ──────────────────────────────────────────────────────────────

set -euo pipefail

CLOUD_STORAGE="$HOME/Library/CloudStorage"
NEXUS_LINK="$HOME/aari-nexus/data/google_drive"

echo "── AARI-NEXUS Google Drive Linker ──"
echo ""

# Find the Google Drive mount
GDRIVE_PATH=$(find "$CLOUD_STORAGE" -maxdepth 1 -name "GoogleDrive-*" -type d 2>/dev/null | head -1)

if [[ -z "$GDRIVE_PATH" ]]; then
  echo "❌  Google Drive not found in $CLOUD_STORAGE"
  echo ""
  echo "Steps to fix:"
  echo "  1. Download: https://www.google.com/drive/download/"
  echo "  2. Sign in with your Google account"
  echo "  3. Wait for initial sync"
  echo "  4. Re-run this script"
  exit 1
fi

MY_DRIVE="$GDRIVE_PATH/My Drive"

if [[ ! -d "$MY_DRIVE" ]]; then
  echo "❌  'My Drive' not found in $GDRIVE_PATH"
  echo "     Google Drive may still be syncing. Try again in a moment."
  exit 1
fi

# Remove existing symlink if stale
if [[ -L "$NEXUS_LINK" ]]; then
  echo "↺  Updating existing symlink..."
  rm "$NEXUS_LINK"
fi

# Create symlink
ln -s "$MY_DRIVE" "$NEXUS_LINK"

echo "✓  Linked: $MY_DRIVE"
echo "       → $NEXUS_LINK"
echo ""
echo "Your Google Drive is now accessible at:"
echo "   ~/aari-nexus/data/google_drive/"
echo ""
echo "Next steps:"
echo "  1. Drop research PDFs into your Drive"
echo "  2. Run: python3 scripts/ingest_drive.py"
echo "  3. Or watch continuously: python3 scripts/ingest_drive.py --watch"
