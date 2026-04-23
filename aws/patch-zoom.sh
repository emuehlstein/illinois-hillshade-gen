#!/usr/bin/env bash
set -euo pipefail

# Patch zoom-level mbtiles into a combined mbtiles file.
# Works locally or on a remote tile server via SSH.
#
# Usage:
#   # Remote: pull from S3 to tile server and patch
#   aws/patch-zoom.sh --source s3://bucket/z14-dark.mbtiles \
#       --target cook-combined-dark.mbtiles --zoom 14
#
#   # Local: patch directly
#   aws/patch-zoom.sh --source ./z14-dark.mbtiles \
#       --target ./combined-dark.mbtiles --zoom 14 --local
#
# Options:
#   --source PATH/URI    S3 URI or local path to z-level mbtiles (required)
#   --target FILENAME    Target mbtiles (filename on tile server, or full local path)
#   --zoom LEVEL         Zoom level to patch (required)
#   --local              Patch locally instead of on tile server
#   --no-restart         Don't restart mbtileserver after patching

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

SOURCE=""
TARGET=""
ZOOM=""
LOCAL=false
RESTART=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --source)     SOURCE="$2"; shift 2 ;;
        --target)     TARGET="$2"; shift 2 ;;
        --zoom|-z)    ZOOM="$2"; shift 2 ;;
        --local)      LOCAL=true; shift ;;
        --no-restart) RESTART=false; shift ;;
        -h|--help)
            sed -n '3,/^$/p' "$0" | sed 's/^# \?//'
            exit 0 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

[[ -z "$SOURCE" || -z "$TARGET" || -z "$ZOOM" ]] && {
    echo "❌ --source, --target, and --zoom are required."
    exit 1
}

echo "🔧 Patch z${ZOOM}"
echo "   Source: $SOURCE"
echo "   Target: $TARGET"
echo ""

if $LOCAL; then
    # Local patching
    [[ "$SOURCE" == s3://* ]] && { aws s3 cp "$SOURCE" "/tmp/$(basename "$SOURCE")"; SOURCE="/tmp/$(basename "$SOURCE")"; }
    echo "Patching locally..."
    sqlite3 "$TARGET" "
        ATTACH '${SOURCE}' AS src;
        DELETE FROM tiles WHERE zoom_level=${ZOOM};
        INSERT OR REPLACE INTO tiles SELECT * FROM src.tiles WHERE zoom_level=${ZOOM};
        DETACH src;"
    echo "✅ Done"
else
    # Remote patching on tile server
    require_var TILE_SERVER_SSH
    TARGET_PATH="${TILE_SERVER_TILES_DIR}/${TARGET}"
    SRC_BASE="$(basename "$SOURCE")"

    if [[ "$SOURCE" == s3://* ]]; then
        echo "📥 Pulling from S3 to tile server..."
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$TILE_SERVER_SSH" \
            "export PATH=\$PATH:\$HOME/.local/bin; aws s3 cp '$SOURCE' '/tmp/$SRC_BASE'" 2>&1 | tail -1
    else
        echo "📤 Uploading to tile server..."
        scp -i "$SSH_KEY" "$SOURCE" "${TILE_SERVER_SSH}:/tmp/$SRC_BASE"
    fi

    echo "🔀 Patching..."
    ssh -i "$SSH_KEY" "$TILE_SERVER_SSH" "
        echo '  Before:'; sqlite3 '$TARGET_PATH' \"SELECT 'z$ZOOM: ' || COUNT(*) || ' tiles' FROM tiles WHERE zoom_level=$ZOOM;\" 2>/dev/null || echo '    (none)'
        sqlite3 '$TARGET_PATH' \"ATTACH '/tmp/$SRC_BASE' AS src; DELETE FROM tiles WHERE zoom_level=$ZOOM; INSERT OR REPLACE INTO tiles SELECT * FROM src.tiles WHERE zoom_level=$ZOOM; DETACH src;\"
        echo '  After:'; sqlite3 '$TARGET_PATH' \"SELECT 'z$ZOOM: ' || COUNT(*) || ' tiles' FROM tiles WHERE zoom_level=$ZOOM;\"
        rm -f '/tmp/$SRC_BASE'"

    if $RESTART; then
        echo "🔄 Restarting mbtileserver..."
        ssh -i "$SSH_KEY" "$TILE_SERVER_SSH" \
            'cd /data && sudo docker compose restart mbtileserver 2>/dev/null || docker restart data-mbtileserver-1 2>/dev/null'
    fi
fi

echo "✅ z${ZOOM} patched into ${TARGET}"
