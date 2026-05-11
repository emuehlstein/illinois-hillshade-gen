#!/usr/bin/env bash
set -euo pipefail

# Generate hillshade tiles on a transient EC2 on-demand instance.
#
# Spins up a beefy ARM instance, runs ilhmp, copies the mbtiles to the
# tile server, then terminates the worker.
#
# Usage:
#   ./generate-aws.sh cook --dem dtm --style dark --zoom 10-16
#   ./generate-aws.sh cook dupage lake --dem dtm --style dark
#   ./generate-aws.sh cook --style dark,light          # multiple styles, one instance
#   ./generate-aws.sh cook --style all                  # all 5 styles
#   ./generate-aws.sh cook --exaggeration 3,10,15       # multiple exaggerations
#   ./generate-aws.sh cook --style dark,light --exaggeration 3,10  # cartesian product
#   ./generate-aws.sh --list                            # list available counties
#
# Options:
#   --dem TYPE           dtm (bare earth) or dsm (surface model) [default: dtm]
#   --style STYLES       comma-separated styles, or 'all' [default: dark]
#                        available: dark, light, tactical, terrain, gray
#   --exaggeration VALS  comma-separated vertical exaggeration factors [default: 3]
#   --zoom RANGE         tile zoom range [default: 10-16]
#   --instance TYPE      EC2 instance type [default: c7g.2xlarge]
#   --disk SIZE          EBS volume size in GB [default: 200]
#   --keep               don't terminate the worker when done (for debugging)
#   --keep-intermediates keep hillshade TIFs in cache (no cleanup between counties)
#   --dry-run            show what would happen without launching
#   --list               list available counties from ilhmp catalog

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Defaults
DEM="dtm"
STYLES="dark"
EXAGGERATIONS="3"
ZOOM="10-16"
INSTANCE_TYPE="${WORKER_INSTANCE_TYPE}"
DISK_GB=200
TILE_SERVER_KEY="${SSH_KEY}"
KEEP=false
KEEP_INTERMEDIATES=false
DRY_RUN=false
LIST=false
ON_DEMAND=true
COUNTIES=()

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --dem) DEM="$2"; shift 2 ;;
        --style) STYLES="$2"; shift 2 ;;
        --exaggeration|-z) EXAGGERATIONS="$2"; shift 2 ;;
        --zoom) ZOOM="$2"; shift 2 ;;
        --instance) INSTANCE_TYPE="$2"; shift 2 ;;
        --disk) DISK_GB="$2"; shift 2 ;;
        --keep) KEEP=true; shift ;;
        --keep-intermediates) KEEP_INTERMEDIATES=true; shift ;;
        --spot) ON_DEMAND=false; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --list) LIST=true; shift ;;
        -*) echo "Unknown option: $1"; exit 1 ;;
        *) COUNTIES+=("$1"); shift ;;
    esac
done

if $LIST; then
    echo "Fetching county list from ilhmp..."
    python3 -c "
from ilhmp.counties import list_all
for c in list_all():
    dtm = '✓' if c.get('dtm_url') else '—'
    dsm = '✓' if c.get('dsm_url') else '—'
    print(f\"  {c['name']:<20} DTM:{dtm}  DSM:{dsm}  ({c.get('year','?')})\")
" 2>/dev/null || echo "Install ilhmp locally to list counties, or check https://github.com/emuehlstein/illinois-hillshade-gen"
    exit 0
fi

if [[ ${#COUNTIES[@]} -eq 0 ]]; then
    echo "Usage: $0 COUNTY [COUNTY...] [--dem dtm|dsm] [--style dark,light] [--exaggeration 3,10] [--zoom 10-16]"
    echo "       $0 --list"
    exit 1
fi

COUNTY_LIST="${COUNTIES[*]}"

# Expand style shortcuts
if [[ "$STYLES" == "all" ]]; then
    STYLES="dark,light,tactical,terrain,gray"
fi

# Count combos for display
IFS=',' read -ra _S <<< "$STYLES"
IFS=',' read -ra _E <<< "$EXAGGERATIONS"
COMBO_COUNT=$(( ${#_S[@]} * ${#_E[@]} ))

echo "🗺️  AWS Hillshade Generator"
echo "   Counties:       ${COUNTY_LIST}"
echo "   DEM:            ${DEM}"
echo "   Styles:         ${STYLES}"
echo "   Exaggerations:  ${EXAGGERATIONS}"
echo "   Combinations:   ${COMBO_COUNT} per county (shared DEM cache)"
echo "   Zoom:           ${ZOOM}"
echo "   Instance:       ${INSTANCE_TYPE}"
echo "   Disk:           ${DISK_GB}GB"
echo "   Region:         ${AWS_REGION}"
echo ""

if $DRY_RUN; then
    echo "[DRY RUN] Would launch on-demand instance and generate hillshades."
    echo "Estimated cost: ~\$0.27/hr (on-demand) + \$0.08/GB-mo storage"
    exit 0
fi

require_var SECURITY_GROUP
require_var KEY_PAIR_NAME

# Ensure caller's IP can SSH to the security group
MY_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || curl -s --max-time 5 checkip.amazonaws.com 2>/dev/null || echo "")
if [[ -n "$MY_IP" ]]; then
    # Check if our IP is already allowed
    EXISTING=$(aws ec2 describe-security-groups --region "$AWS_REGION" \
        --group-ids "$SECURITY_GROUP" \
        --query "SecurityGroups[0].IpPermissions[?FromPort==\`22\`].IpRanges[].CidrIp" \
        --output text 2>/dev/null || echo "")
    if ! echo "$EXISTING" | grep -q "$MY_IP"; then
        echo "🔑 Adding SSH access for $MY_IP to security group..."
        aws ec2 authorize-security-group-ingress --region "$AWS_REGION" \
            --group-id "$SECURITY_GROUP" --protocol tcp --port 22 \
            --cidr "${MY_IP}/32" > /dev/null 2>&1 || true
    fi
fi

echo "🔍 Looking up latest Ubuntu 24.04 ARM64 AMI..."
AMI=$(get_ubuntu_arm64_ami)
echo "   AMI: $AMI"
echo ""

# Build the user-data script that runs on the worker.
# The WORKER_SCRIPT heredoc is single-quoted so nothing expands inside it.
# We use distinctive __PLACEHOLDER__ tokens (double underscores) to avoid
# substring collisions, then sed replaces them after the heredoc is written.
USERDATA=$(cat << CLOUD_INIT
#!/bin/bash
set -euo pipefail

# Phase 1: Install dependencies (runs in cloud-init)
exec > /var/log/hillshade-gen.log 2>&1
echo "=== Hillshade setup starting at \$(date) ==="

apt-get update -qq
apt-get install -y -qq python3-pip python3-venv gdal-bin libgdal-dev python3-gdal python3-numpy sqlite3 wget unzip curl > /dev/null 2>&1

# Install AWS CLI v2 (for S3 uploads + CloudWatch)
curl -sL "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp
/tmp/aws/install > /dev/null 2>&1
rm -rf /tmp/aws /tmp/awscliv2.zip

# ── CloudWatch Logs agent ─────────────────────────────────────────────────
# Streams /var/log/hillshade-gen.log to /ilhmp/hillshade-gen in real time.
# Requires the instance profile to have logs:CreateLogGroup,
# logs:CreateLogStream, logs:PutLogEvents on arn:aws:logs:*:*:log-group:/ilhmp/*
INSTANCE_ID=\$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "unknown")
REGION="${AWS_REGION}"
LOG_GROUP="/ilhmp/hillshade-gen"
LOG_STREAM="__COUNTY__-\${INSTANCE_ID}"

echo "=== Setting up CloudWatch Logs (stream: \${LOG_STREAM}) ==="

# Install CloudWatch agent
wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/arm64/latest/amazon-cloudwatch-agent.deb \
    -O /tmp/amazon-cloudwatch-agent.deb
dpkg -i /tmp/amazon-cloudwatch-agent.deb > /dev/null 2>&1 || apt-get install -f -y -qq > /dev/null 2>&1
rm -f /tmp/amazon-cloudwatch-agent.deb

# Write agent config
mkdir -p /opt/aws/amazon-cloudwatch-agent/etc
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << CW_CONFIG
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/hillshade-gen.log",
            "log_group_name": "\${LOG_GROUP}",
            "log_stream_name": "\${LOG_STREAM}",
            "timezone": "UTC",
            "timestamp_format": "%Y-%m-%d %H:%M:%S",
            "multi_line_start_pattern": "^==="
          }
        ]
      }
    },
    "log_stream_name": "\${LOG_STREAM}",
    "force_flush_interval": 5
  }
}
CW_CONFIG

# Start the agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json > /dev/null 2>&1 \
    && echo "✅ CloudWatch agent started (log stream: \${LOG_STREAM})" \
    || echo "⚠️  CloudWatch agent failed to start (non-fatal — logs still in /var/log/hillshade-gen.log)"
# ────────────────────────────────────────────────────────────────────────

python3 -m venv --system-site-packages /opt/ilhmp-venv
source /opt/ilhmp-venv/bin/activate
pip install -q 'numpy<2' Pillow git+https://github.com/emuehlstein/illinois-hillshade-gen.git@main mbutil

mkdir -p /data/output /data/tmp
export TMPDIR=/data/tmp

# Phase 2: Run the heavy work detached from cloud-init
# (cloud-init can SIGTERM long-running children; this avoids that)
cat > /opt/run-hillshade.sh << 'WORKER_SCRIPT'
#!/bin/bash
set -euo pipefail
exec >> /var/log/hillshade-gen.log 2>&1
export TMPDIR=/data/tmp
mkdir -p /data/tmp
source /opt/ilhmp-venv/bin/activate

# Args: <styles-csv> <exaggerations-csv> <county> [county...]
STYLES_CSV="\$1"; shift
EXAGG_CSV="\$1"; shift
IFS=',' read -ra STYLES <<< "\$STYLES_CSV"
IFS=',' read -ra EXAGGS <<< "\$EXAGG_CSV"

echo "=== Hillshade generation starting at \$(date) ==="
echo "    Styles: \${STYLES[*]}"
echo "    Exaggerations: \${EXAGGS[*]}"
echo "    Counties: \$@"

for COUNTY in "\$@"; do
    echo "=== Processing \${COUNTY} ==="
    CACHE="/data/cache/\${COUNTY}"
    mkdir -p "\${CACHE}"

    # ── S3 intermediate cache ────────────────────────────────────────────────
    # Pull reprojected DEM + any grayscale TIFs from S3 before running ilhmp.
    # On retry, this skips the expensive DEM download + reproject (~20-30 min).
    S3_INTERMEDIATES="s3://__S3_BUCKET__/\${COUNTY}/intermediates"
    echo "🔍 Checking S3 for cached intermediates: \${S3_INTERMEDIATES}/"
    S3_FILES=\$(aws s3 ls "\${S3_INTERMEDIATES}/" --no-paginate 2>/dev/null | awk '{print \$4}' || true)
    if [[ -z "\${S3_FILES}" ]]; then
        echo "   (no cached intermediates found — fresh run)"
    else
        echo "\${S3_FILES}" | while read KEY; do
            [[ -z "\${KEY}" ]] && continue
            LOCAL="\${CACHE}/\${KEY}"
            if [[ ! -f "\${LOCAL}" ]]; then
                echo "   ⬇ Pulling \${KEY} from S3..."
                aws s3 cp "\${S3_INTERMEDIATES}/\${KEY}" "\${LOCAL}" --quiet \
                    && echo "   ✓ Pulled \${KEY}" \
                    || echo "   ⚠️  Pull failed for \${KEY} (non-fatal)"
            else
                echo "   ⏩ Already local: \${KEY}"
            fi
        done
    fi
    # ────────────────────────────────────────────────────────────────────────

    COMBO=0
    TOTAL=\$(( \${#STYLES[@]} * \${#EXAGGS[@]} ))

    for EXAGG in "\${EXAGGS[@]}"; do
        for STYLE in "\${STYLES[@]}"; do
            COMBO=\$((COMBO + 1))
            echo "--- \${COUNTY}: [\${COMBO}/\${TOTAL}] \${STYLE} @ \${EXAGG}x ---"
            OUTDIR="/data/output/\${COUNTY}/\${STYLE}-\${EXAGG}x"
            CHECKPOINT="/data/output/\${COUNTY}/\${STYLE}-\${EXAGG}x/.done"

            # Checkpoint/resume: skip if this combo already completed
            if [[ -f "\${CHECKPOINT}" ]]; then
                PREV_MB=\$(find "\${OUTDIR}" -name "*.mbtiles" | head -1)
                echo "⏩ SKIP \${COUNTY}/\${STYLE}/\${EXAGG}x — already complete (\$(du -h "\${PREV_MB}" 2>/dev/null | cut -f1))"
                continue
            fi

            # Detect if STYLE is a theme name (contains hyphen or matches known themes)
            STYLE_FLAG="--style"
            if ilhmp themes --json 2>/dev/null | grep -q "\"\${STYLE}\""; then
                STYLE_FLAG="--theme"
            elif [[ "\${STYLE}" == *-* ]] || [[ "\${STYLE}" == "simmon" ]] || [[ "\${STYLE}" == "grayscale" ]]; then
                STYLE_FLAG="--theme"
            fi

            ilhmp run "\${COUNTY}" \
                --dem "__DEM__" \
                \${STYLE_FLAG} "\${STYLE}" \
                --exaggeration "\${EXAGG}" \
                --zoom "__ZOOM__" \
                --output "\${OUTDIR}" \
                --cache-dir "\${CACHE}" \
                --json > "/data/output/\${COUNTY}-\${STYLE}-\${EXAGG}x.json" 2>"/data/output/\${COUNTY}-\${STYLE}-\${EXAGG}x-stderr.log" || {
                    echo "ERROR: \${COUNTY}/\${STYLE}/\${EXAGG}x failed (exit code \$?)"
                    echo "--- stderr ---"
                    cat "/data/output/\${COUNTY}-\${STYLE}-\${EXAGG}x-stderr.log" 2>/dev/null || echo "(no stderr)"
                    echo "--- end error ---"
                    continue
                }

            # Find the mbtiles
            MBTILES=\$(find "\${OUTDIR}" -name "*.mbtiles" | head -1)
            if [[ -z "\${MBTILES}" ]]; then
                echo "ERROR: No mbtiles found for \${COUNTY}/\${STYLE}/\${EXAGG}x"
                continue
            fi

            # Inject metadata
            BASENAME=\$(basename "\${MBTILES}")
            TILESET_NAME="\${BASENAME%.mbtiles}"

            MIN_Z=\$(sqlite3 "\${MBTILES}" "SELECT min(zoom_level) FROM tiles;")
            MAX_Z=\$(sqlite3 "\${MBTILES}" "SELECT max(zoom_level) FROM tiles;")

            # Detect tile coordinate scheme (XYZ or TMS)
            SCHEME=\$(sqlite3 "\${MBTILES}" "SELECT value FROM metadata WHERE name='scheme';" 2>/dev/null || echo "")
            if [[ -z "\${SCHEME}" ]]; then SCHEME="xyz"; fi

            BOUNDS=\$(python3 -c "
import sqlite3, math
conn = sqlite3.connect('\${MBTILES}')
row = conn.execute('SELECT min(tile_column), max(tile_column), min(tile_row), max(tile_row) FROM tiles WHERE zoom_level=\${MIN_Z}').fetchone()
x_min, x_max, y_min, y_max = row
z = \${MIN_Z}
n = 2**z
scheme = '\${SCHEME}'
lon_min = x_min / n * 360 - 180
lon_max = (x_max + 1) / n * 360 - 180
if scheme == 'tms':
    xyz_y_min = n - 1 - y_max
    xyz_y_max = n - 1 - y_min + 1
else:
    xyz_y_min = y_min
    xyz_y_max = y_max + 1
lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * xyz_y_min / n))))
lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * xyz_y_max / n))))
print(f'{lon_min:.4f},{lat_min:.4f},{lon_max:.4f},{lat_max:.4f}')
print(f'{(lon_min+lon_max)/2:.4f},{(lat_min+lat_max)/2:.4f}')
")

            BBOX=\$(echo "\$BOUNDS" | head -1)
            CENTER=\$(echo "\$BOUNDS" | tail -1)

            sqlite3 "\${MBTILES}" "
                CREATE TABLE IF NOT EXISTS metadata (name text, value text);
                INSERT OR REPLACE INTO metadata (name, value) VALUES ('name', '\${TILESET_NAME}');
                INSERT OR REPLACE INTO metadata (name, value) VALUES ('format', 'png');
                INSERT OR REPLACE INTO metadata (name, value) VALUES ('bounds', '\${BBOX}');
                INSERT OR REPLACE INTO metadata (name, value) VALUES ('center', '\${CENTER},12');
                INSERT OR REPLACE INTO metadata (name, value) VALUES ('minzoom', '\${MIN_Z}');
                INSERT OR REPLACE INTO metadata (name, value) VALUES ('maxzoom', '\${MAX_Z}');
                INSERT OR REPLACE INTO metadata (name, value) VALUES ('type', 'overlay');
                INSERT OR REPLACE INTO metadata (name, value) VALUES ('scheme', '\${SCHEME}');
                INSERT OR REPLACE INTO metadata (name, value) VALUES ('description', '\${COUNTY} __DEM_UPPER__ \${STYLE} hillshade (\${EXAGG}x)');
            "

            # Validate tiles (sample 10 random tiles, check for non-blank content)
            VALIDATION=\$(python3 -c "
import sqlite3, random, io, struct
from PIL import Image
import numpy as np

conn = sqlite3.connect('\${MBTILES}')
tiles = conn.execute('SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles LIMIT 1000').fetchall()
if len(tiles) == 0:
    print('ERROR: no tiles in mbtiles')
    exit(1)

sample_size = min(10, len(tiles))
sample = random.sample(tiles, sample_size)
bad_tiles = []

for z, x, y, data in sample:
    try:
        img = Image.open(io.BytesIO(data))
        arr = np.array(img)
        mean = arr.mean()
        stddev = arr.std()
        # Blank tiles typically have mean near 0 or 255 with stddev near 0
        if stddev < 5.0:
            bad_tiles.append(f'z{z}/{x}/{y}: mean={mean:.1f} std={stddev:.1f}')
    except Exception as e:
        bad_tiles.append(f'z{z}/{x}/{y}: {e}')

if bad_tiles:
    print(f'WARN: {len(bad_tiles)}/{sample_size} sampled tiles appear blank or corrupted')
    for t in bad_tiles:
        print(f'  {t}')
else:
    print(f'OK: {sample_size}/{sample_size} sampled tiles valid')
" 2>&1)
            echo "   Validation: \${VALIDATION}"
            if echo "\${VALIDATION}" | grep -q "^ERROR:"; then
                echo "   ❌ Tile validation failed, skipping checkpoint"
                continue
            fi

            # Mark checkpoint — this combo is fully done
            touch "\${CHECKPOINT}"
            echo "✓ \${COUNTY}/\${STYLE}/\${EXAGG}x: \${MBTILES} (\$(du -h "\${MBTILES}" | cut -f1))"

            # Upload mbtiles to S3 as checkpoint (survives instance termination)
            S3_KEY="s3://__S3_BUCKET__/\${COUNTY}/mbtiles/\$(basename \${MBTILES})"
            echo "   ↑ Uploading mbtiles to \${S3_KEY}..."
            aws s3 cp "\${MBTILES}" "\${S3_KEY}" --quiet 2>/dev/null && echo "   ↑ S3 mbtiles upload complete" || echo "   ⚠️ S3 mbtiles upload failed (non-fatal)"

            # ── Push intermediates to S3 after first successful combo ──────────
            # Reprojected DEM + grayscale TIFs are expensive to regenerate.
            # Upload them now so future runs (new style, retry) can pull them.
            echo "   ↑ Syncing intermediates to S3..."
            for INTERMEDIATE in "\${CACHE}/"*.tif; do
                [[ -f "\${INTERMEDIATE}" ]] || continue
                IKEY="\$(basename \${INTERMEDIATE})"
                ALREADY=\$(aws s3 ls "\${S3_INTERMEDIATES}/\${IKEY}" 2>/dev/null | awk '{print \$3}' || echo "0")
                LOCAL_SIZE=\$(stat -f%z "\${INTERMEDIATE}" 2>/dev/null || stat -c%s "\${INTERMEDIATE}" 2>/dev/null || echo "0")
                if [[ "\${ALREADY:-0}" == "\${LOCAL_SIZE}" ]]; then
                    echo "      ⏩ Already in S3: \${IKEY}"
                else
                    echo "      ↑ Pushing \${IKEY} (\$(du -h "\${INTERMEDIATE}" | cut -f1))..."
                    aws s3 cp "\${INTERMEDIATE}" "\${S3_INTERMEDIATES}/\${IKEY}" --quiet \
                        && echo "      ✓ Pushed \${IKEY}" \
                        || echo "      ⚠️  Push failed for \${IKEY} (non-fatal)"
                fi
            done
            # ────────────────────────────────────────────────────────────────

            # Upload directly to tile server (cloud-to-cloud, no local hop)
            # Requires self-referencing SG rule (run fix-worker-scp.sh first)
            TILE_SERVER="__TILE_SERVER_HOST__"
            if [[ -n "\${TILE_SERVER}" ]]; then
                echo "   ↑ Uploading to tile server \${TILE_SERVER}..."
                scp -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
                    "\${MBTILES}" "ubuntu@\${TILE_SERVER}:/data/tiles/\$(basename \${MBTILES})" 2>/dev/null \
                    && echo "   ↑ Tile server upload complete" \
                    || echo "   ⚠️ Tile server upload failed (non-fatal, may need SG rule)"
            fi
        done
    done

    # Clean up large cached intermediates to free disk for next county
    # NOTE: only delete per-exagg hillshade TIFs; keep DEM + reprojected TIF
    # since they're shared across exaggeration levels
    if [[ "__KEEP_INTERMEDIATES__" != "true" ]]; then
        echo "Cleaning style-specific cache for \${COUNTY}..."
        find "\${CACHE}" -name "*_hillshade_*.tif" -delete 2>/dev/null || true
        # Also purge grayscale TIFs — they're in S3 now, no need to hold disk
        find "\${CACHE}" -name "*_gray_*.tif" -delete 2>/dev/null || true
    else
        echo "Keeping intermediates for \${COUNTY} (--keep-intermediates set)"
    fi
done

echo "=== All counties processed ==="
echo "=== Output files ==="
find /data/output -name "*.mbtiles" -exec ls -lh {} \;

# Signal completion
touch /data/output/DONE
echo "=== DONE at \$(date) ==="
WORKER_SCRIPT

chmod +x /opt/run-hillshade.sh
# Inject build-time values using distinctive __PLACEHOLDER__ tokens
# (no substring collision risk — each token is unique)
sed -i 's|__DEM_UPPER__|${DEM^^}|g' /opt/run-hillshade.sh
sed -i 's|__DEM__|${DEM}|g' /opt/run-hillshade.sh
sed -i 's|__ZOOM__|${ZOOM}|g' /opt/run-hillshade.sh
sed -i "s|__S3_BUCKET__|${S3_BUCKET}|g" /opt/run-hillshade.sh
sed -i "s|__COUNTY__|${COUNTIES[0]}|g" /opt/run-hillshade.sh
sed -i 's|__KEEP_INTERMEDIATES__|${KEEP_INTERMEDIATES}|g' /opt/run-hillshade.sh
sed -i 's|__TILE_SERVER_HOST__|${TILE_SERVER_PRIVATE_IP:-}|g' /opt/run-hillshade.sh

echo "=== Setup complete, launching worker detached at \$(date) ==="
nohup /opt/run-hillshade.sh ${STYLES} ${EXAGGERATIONS} ${COUNTY_LIST} &
CLOUD_INIT
)
USERDATA="${USERDATA//__COUNTY__/${COUNTIES[0]}}"

# Launch instance
SPOT_ARGS=()
if ! $ON_DEMAND; then
    SPOT_ARGS=(--instance-market-options '{"MarketType":"spot","SpotOptions":{"SpotInstanceType":"one-time"}}')
    echo "🚀 Launching spot instance..."
else
    echo "🚀 Launching on-demand instance..."
fi
INSTANCE_ID=$(aws ec2 run-instances \
    --region "$AWS_REGION" \
    --image-id "$AMI" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_PAIR_NAME" \
    --security-group-ids "$SECURITY_GROUP" \
    --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":${DISK_GB},\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" \
    "${SPOT_ARGS[@]}" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=hillshade-worker-${COUNTIES[0]}},{Key=Purpose,Value=hillshade-generation},{Key=AutoTerminate,Value=true}]" \
    --iam-instance-profile "Name=${IAM_INSTANCE_PROFILE}" \
    --user-data "$USERDATA" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "   Instance: $INSTANCE_ID"

# Wait for running
echo "⏳ Waiting for instance to start..."
aws ec2 wait instance-running --region "$AWS_REGION" --instance-ids "$INSTANCE_ID"

WORKER_IP=$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "   IP: $WORKER_IP"

echo ""
echo "✅ Worker launched! Generation running via cloud-init."
echo ""
echo "Monitor progress:"
echo "   ssh -i $TILE_SERVER_KEY ubuntu@$WORKER_IP 'tail -f /var/log/hillshade-gen.log'"
echo ""
echo "When complete, pull results:"
echo "   ssh -i $TILE_SERVER_KEY ubuntu@$WORKER_IP 'find /data/output -name *.mbtiles -exec ls -lh {} \;'"
echo ""

# Save instance info for the pull script
cat > "/tmp/hillshade-worker-${COUNTIES[0]}.env" << EOF
WORKER_INSTANCE_ID=$INSTANCE_ID
WORKER_IP=$WORKER_IP
WORKER_KEY=$TILE_SERVER_KEY
COUNTIES="${COUNTY_LIST}"
DEM=$DEM
STYLES=$STYLES
EXAGGERATIONS=$EXAGGERATIONS
KEEP=$KEEP
EOF

echo "Instance info saved to /tmp/hillshade-worker-${COUNTIES[0]}.env"
echo ""
echo "To pull results and upload to tile server when done:"
echo "   ./pull-aws-tiles.sh ${COUNTIES[0]}"



