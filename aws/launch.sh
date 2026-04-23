#!/usr/bin/env bash
set -euo pipefail

# Launch an EC2 spot instance to run ilhmp for one or more counties.
#
# Usage:
#   aws/launch.sh cook --dem dtm --style dark,light --zoom 10-16
#   aws/launch.sh cook dupage --style all --exaggeration 3,9
#   aws/launch.sh --list
#   aws/launch.sh cook --dry-run
#
# Options:
#   --dem TYPE           dtm or dsm [default: dtm]
#   --style STYLES       comma-separated, or 'all' [default: dark]
#   --exaggeration VALS  comma-separated z-factors [default: 3]
#   --zoom RANGE         tile zoom range [default: 10-16]
#   --instance TYPE      EC2 instance type [default: from .env]
#   --disk SIZE          EBS volume in GB [default: from .env]
#   --spot               Use spot instances [default: on-demand]
#   --keep               Don't flag for auto-terminate
#   --dry-run            Show plan without launching
#   --list               List available counties

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

DEM="dtm"
STYLES="dark"
EXAGGERATIONS="3"
ZOOM="10-16"
KEEP=false
DRY_RUN=false
LIST=false
SPOT=false
COUNTIES=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --dem) DEM="$2"; shift 2 ;;
        --style) STYLES="$2"; shift 2 ;;
        --exaggeration|-z) EXAGGERATIONS="$2"; shift 2 ;;
        --zoom) ZOOM="$2"; shift 2 ;;
        --instance) INSTANCE_TYPE="$2"; shift 2 ;;
        --disk) DISK_GB="$2"; shift 2 ;;
        --spot) SPOT=true; shift ;;
        --keep) KEEP=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --list) LIST=true; shift ;;
        -h|--help)
            sed -n '3,/^$/p' "$0" | sed 's/^# \?//'
            exit 0 ;;
        -*) echo "Unknown option: $1"; exit 1 ;;
        *) COUNTIES+=("$1"); shift ;;
    esac
done

if $LIST; then
    echo "Fetching county list..."
    python3 -c "
from ilhmp.counties import list_all
for c in list_all():
    dtm = '✓' if c.get('dtm_url') else '—'
    dsm = '✓' if c.get('dsm_url') else '—'
    print(f\"  {c['name']:<20} DTM:{dtm}  DSM:{dsm}  ({c.get('year','?')})\")" 2>/dev/null \
    || echo "Install ilhmp locally to list counties, or check the README."
    exit 0
fi

if [[ ${#COUNTIES[@]} -eq 0 ]]; then
    echo "Usage: $0 COUNTY [COUNTY...] [--dem dtm] [--style dark,light] [--zoom 10-16]"
    echo "       $0 --list"
    exit 1
fi

require_var SECURITY_GROUP
require_var KEY_PAIR_NAME

[[ "$STYLES" == "all" ]] && STYLES="dark,light,tactical,terrain,gray"

COUNTY_LIST="${COUNTIES[*]}"
IFS=',' read -ra _S <<< "$STYLES"
IFS=',' read -ra _E <<< "$EXAGGERATIONS"
COMBOS=$(( ${#_S[@]} * ${#_E[@]} ))

echo "🗺️  ilhmp AWS Worker"
echo "   Counties:      $COUNTY_LIST"
echo "   DEM:           $DEM"
echo "   Styles:        $STYLES"
echo "   Exaggerations: $EXAGGERATIONS"
echo "   Combos:        $COMBOS per county"
echo "   Zoom:          $ZOOM"
echo "   Instance:      $INSTANCE_TYPE"
echo "   Disk:          ${DISK_GB}GB"
echo ""

if $DRY_RUN; then
    echo "[DRY RUN] Would launch instance and generate hillshades."
    exit 0
fi

AMI=$(get_ubuntu_arm64_ami)
echo "🔍 AMI: $AMI"

# Build IAM args
IAM_ARGS=()
[[ -n "${IAM_INSTANCE_PROFILE:-}" ]] && IAM_ARGS=(--iam-instance-profile "Name=${IAM_INSTANCE_PROFILE}")

# Build spot args
SPOT_ARGS=()
$SPOT && SPOT_ARGS=(--instance-market-options '{"MarketType":"spot","SpotOptions":{"SpotInstanceType":"one-time"}}')

# User-data script
USERDATA_FILE=$(mktemp)
cat > "$USERDATA_FILE" << 'SETUP_EOF'
#!/bin/bash
set -euo pipefail
exec > /var/log/ilhmp.log 2>&1
echo "=== ilhmp setup at $(date) ==="

export HOME=/root DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3-pip python3-venv gdal-bin libgdal-dev python3-gdal python3-numpy sqlite3 wget >/dev/null 2>&1

python3 -m venv --system-site-packages /opt/ilhmp-venv
source /opt/ilhmp-venv/bin/activate
pip install -q 'numpy<2' git+https://github.com/emuehlstein/illinois-hillshade-gen.git mbutil

mkdir -p /data/output /data/tmp
export TMPDIR=/data/tmp
SETUP_EOF

# Append the run portion with variable expansion
cat >> "$USERDATA_FILE" << RUNEOF

echo "=== Starting generation at \$(date) ==="
source /opt/ilhmp-venv/bin/activate
export TMPDIR=/data/tmp

IFS=',' read -ra STYLES <<< "${STYLES}"
IFS=',' read -ra EXAGGS <<< "${EXAGGERATIONS}"

for COUNTY in ${COUNTY_LIST}; do
    for EXAGG in "\${EXAGGS[@]}"; do
        for STYLE in "\${STYLES[@]}"; do
            echo "--- \${COUNTY}: \${STYLE} @ \${EXAGG}x ---"
            ilhmp run "\${COUNTY}" \\
                --dem "${DEM}" \\
                --style "\${STYLE}" \\
                --exaggeration "\${EXAGG}" \\
                --zoom "${ZOOM}" \\
                --output "/data/output/\${COUNTY}/\${STYLE}-\${EXAGG}x" \\
                --cache-dir "/data/cache/\${COUNTY}" \\
                --json || echo "ERROR: \${COUNTY}/\${STYLE}/\${EXAGG}x failed"
        done
    done
done

echo "=== Output files ==="
find /data/output -name "*.mbtiles" -exec ls -lh {} \;
touch /data/output/DONE
echo "=== DONE at \$(date) ==="
RUNEOF

USERDATA_B64=$(base64 < "$USERDATA_FILE")
rm -f "$USERDATA_FILE"

MODE="on-demand"
$SPOT && MODE="spot"
echo "🚀 Launching $MODE instance..."

INSTANCE_ID=$(aws ec2 run-instances \
    --region "$AWS_REGION" \
    --image-id "$AMI" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_PAIR_NAME" \
    --security-group-ids "$SECURITY_GROUP" \
    "${IAM_ARGS[@]}" \
    "${SPOT_ARGS[@]}" \
    --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":${DISK_GB},\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" \
    --user-data "$USERDATA_B64" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=ilhmp-${COUNTIES[0]}},{Key=Purpose,Value=ilhmp}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "   Instance: $INSTANCE_ID"
echo "⏳ Waiting for instance..."
aws ec2 wait instance-running --region "$AWS_REGION" --instance-ids "$INSTANCE_ID"

WORKER_IP=$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "   IP: $WORKER_IP"

ENV_FILE="/tmp/ilhmp-worker-${COUNTIES[0]}.env"
cat > "$ENV_FILE" << EOF
WORKER_INSTANCE_ID=$INSTANCE_ID
WORKER_IP=$WORKER_IP
WORKER_KEY=$SSH_KEY
COUNTIES="${COUNTY_LIST}"
DEM=$DEM
STYLES=$STYLES
EXAGGERATIONS=$EXAGGERATIONS
KEEP=$KEEP
EOF

echo ""
echo "✅ Worker launched!"
echo ""
echo "Monitor:  ssh -i $SSH_KEY ubuntu@$WORKER_IP 'tail -f /var/log/ilhmp.log'"
echo "Check:    ssh -i $SSH_KEY ubuntu@$WORKER_IP 'test -f /data/output/DONE && echo DONE || echo RUNNING'"
echo "Pull:     aws/pull.sh ${COUNTIES[0]}"
echo ""
echo "Saved: $ENV_FILE"
