#!/usr/bin/env bash
set -euo pipefail

# Pull ilhmp results from an EC2 worker.
#
# Usage:
#   aws/pull.sh <county>               # Pull to ./output/
#   aws/pull.sh <county> --upload       # Pull + upload to tile server
#   aws/pull.sh <county> --terminate    # Pull + terminate worker
#
# Reads worker info from /tmp/ilhmp-worker-<county>.env

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

UPLOAD=false
TERMINATE=false
LOCAL_DIR="./output"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <county> [--upload] [--terminate] [--output DIR]"
    echo ""
    echo "Active workers:"
    ls /tmp/ilhmp-worker-*.env 2>/dev/null | sed 's|/tmp/ilhmp-worker-||;s|\.env||' || echo "  (none)"
    exit 1
fi

COUNTY="$1"; shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --upload) UPLOAD=true; shift ;;
        --terminate) TERMINATE=true; shift ;;
        --output) LOCAL_DIR="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

ENV_FILE="/tmp/ilhmp-worker-${COUNTY}.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "❌ No worker for '$COUNTY'. Expected: $ENV_FILE"
    exit 1
fi
source "$ENV_FILE"

echo "🔍 Checking worker $WORKER_INSTANCE_ID ($WORKER_IP)..."

STATE=$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$WORKER_INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null)
if [[ "$STATE" != "running" ]]; then
    echo "❌ Worker is $STATE"
    exit 1
fi

ssh -i "$WORKER_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
    "ubuntu@$WORKER_IP" 'test -f /data/output/DONE' 2>/dev/null || {
    echo "⏳ Still running. Check: ssh -i $WORKER_KEY ubuntu@$WORKER_IP 'tail -20 /var/log/ilhmp.log'"
    exit 1
}

echo "✅ Generation complete!"

# List outputs
echo ""
echo "📦 Output files:"
ssh -i "$WORKER_KEY" "ubuntu@$WORKER_IP" \
    'find /data/output -name "*.mbtiles" -exec ls -lh {} \;'

# Pull mbtiles
mkdir -p "$LOCAL_DIR"
MBTILES_LIST=$(ssh -i "$WORKER_KEY" "ubuntu@$WORKER_IP" \
    'find /data/output -name "*.mbtiles" -print')

echo ""
echo "📥 Pulling to $LOCAL_DIR..."
PULLED=0
for MB in $MBTILES_LIST; do
    BASENAME=$(basename "$MB")
    scp -i "$WORKER_KEY" "ubuntu@$WORKER_IP:$MB" "$LOCAL_DIR/$BASENAME"
    echo "   ✓ $BASENAME"
    PULLED=$((PULLED + 1))
done
echo "   $PULLED file(s) pulled"

# Upload to tile server
if $UPLOAD; then
    require_var TILE_SERVER_SSH
    echo ""
    echo "📤 Uploading to $TILE_SERVER_SSH..."
    for MB in "$LOCAL_DIR"/*.mbtiles; do
        BASENAME=$(basename "$MB")
        scp -i "$SSH_KEY" "$MB" "${TILE_SERVER_SSH}:${TILE_SERVER_TILES_DIR}/$BASENAME"
        echo "   ✓ $BASENAME"
    done
    echo "🔄 Restarting mbtileserver..."
    ssh -i "$SSH_KEY" "$TILE_SERVER_SSH" \
        'cd /data && sudo docker compose restart mbtileserver 2>/dev/null || docker restart data-mbtileserver-1 2>/dev/null'
fi

# Terminate
if $TERMINATE; then
    echo ""
    echo "🗑️  Terminating worker..."
    aws ec2 terminate-instances --region "$AWS_REGION" --instance-ids "$WORKER_INSTANCE_ID" >/dev/null
    echo "   Terminated $WORKER_INSTANCE_ID"
    rm -f "$ENV_FILE"
elif [[ "${KEEP:-false}" != "true" ]]; then
    echo ""
    echo "⚠️  Worker still running. Terminate with:"
    echo "   aws ec2 terminate-instances --region $AWS_REGION --instance-ids $WORKER_INSTANCE_ID"
fi

echo ""
echo "✅ Done!"
