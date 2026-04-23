#!/usr/bin/env bash
set -euo pipefail

# Launch an EC2 spot instance to generate tiles for a specific zoom level
# from an existing grayscale hillshade in S3.
#
# Usage:
#   aws/launch-zoom.sh --gray s3://bucket/path/gray.tif --zoom 14
#   aws/launch-zoom.sh --gray s3://bucket/gray.tif --zoom 15 --styles dark,light
#
# Options:
#   --gray S3_URI        S3 path to grayscale hillshade (required)
#   --zoom LEVEL         Zoom level to generate (required)
#   --styles STYLES      Comma-separated themes [default: dark,light]
#   --name NAME          Display name prefix [default: Hillshade]
#   --s3-output S3_URI   S3 prefix for output mbtiles [default: derived from --gray]
#   --instance TYPE      EC2 instance type
#   --disk SIZE          EBS volume in GB [default: 50]
#   --keep               Don't auto-terminate

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
DISK_GB=50  # Override default — zoom jobs are small

GRAY_S3=""
ZOOM=""
STYLES="dark,light"
NAME="Hillshade"
S3_OUTPUT=""
KEEP=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --gray)      GRAY_S3="$2"; shift 2 ;;
        --zoom|-z)   ZOOM="$2"; shift 2 ;;
        --styles)    STYLES="$2"; shift 2 ;;
        --name)      NAME="$2"; shift 2 ;;
        --s3-output) S3_OUTPUT="$2"; shift 2 ;;
        --instance)  INSTANCE_TYPE="$2"; shift 2 ;;
        --disk)      DISK_GB="$2"; shift 2 ;;
        --keep)      KEEP=true; shift ;;
        --dry-run)   DRY_RUN=true; shift ;;
        -h|--help)
            sed -n '3,/^$/p' "$0" | sed 's/^# \?//'
            exit 0 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

[[ -z "$GRAY_S3" ]] && { echo "❌ --gray required"; exit 1; }
[[ -z "$ZOOM" ]] && { echo "❌ --zoom required"; exit 1; }
require_var SECURITY_GROUP

[[ -z "$S3_OUTPUT" ]] && S3_OUTPUT="$(echo "$GRAY_S3" | sed 's|/intermediates/.*|/mbtiles|')"

echo "🗺️  Zoom-Level Tile Generator"
echo "   Grayscale: $GRAY_S3"
echo "   Zoom:      $ZOOM"
echo "   Styles:    $STYLES"
echo "   S3 output: $S3_OUTPUT"
echo "   Instance:  $INSTANCE_TYPE"
echo ""

$DRY_RUN && { echo "[DRY RUN]"; exit 0; }

AMI=$(get_ubuntu_arm64_ami)
echo "🔍 AMI: $AMI"

IAM_ARGS=()
[[ -n "${IAM_INSTANCE_PROFILE:-}" ]] && IAM_ARGS=(--iam-instance-profile "Name=${IAM_INSTANCE_PROFILE}")

USERDATA_FILE=$(mktemp)
cat > "$USERDATA_FILE" << USERDATA
#!/bin/bash
set -euo pipefail
export HOME=/root DEBIAN_FRONTEND=noninteractive
LOG=/var/log/ilhmp.log
exec > >(tee -a "\$LOG") 2>&1

apt-get update -qq
apt-get install -y -qq gdal-bin python3-gdal python3-pil python3-numpy python3-pip sqlite3
pip3 install --break-system-packages awscli 2>/dev/null || true
export PATH=\$PATH:/usr/local/bin:/root/.local/bin

WORKDIR="/data/zoom-${ZOOM}"
mkdir -p "\$WORKDIR" && cd "\$WORKDIR"

echo "=== z${ZOOM} tiles — \$(date) ==="

echo "--- Pulling grayscale ---"
aws s3 cp "${GRAY_S3}" ./gray.tif 2>&1 | tail -1

echo "--- Tiling z${ZOOM} (\$(nproc) cores) ---"
mkdir -p tiles/gray
gdal2tiles.py --zoom=${ZOOM} --processes=\$(nproc) --resampling=bilinear \\
    --tiledriver=PNG --webviewer=none --xyz gray.tif tiles/gray
echo "  \$(find tiles/gray -name '*.png' | wc -l) gray tiles"

cat > /tmp/tint.py << 'PYEOF'
import os, sys, glob; from PIL import Image; import numpy as np
T={"dark":(0.30,0.40,0.60),"light":(0.85,0.82,0.78)}
s,t,d=sys.argv[1],sys.argv[2],sys.argv[3]; r,g,b=T[t]; c=0
for p in glob.glob(os.path.join(s,"*","*","*.png")):
    o=os.path.join(d,os.path.relpath(p,s)); os.makedirs(os.path.dirname(o),exist_ok=True)
    a=np.array(Image.open(p).convert("L"),dtype=np.float32)
    Image.fromarray(np.stack([np.clip(a*r,0,255).astype(np.uint8),np.clip(a*g,0,255).astype(np.uint8),np.clip(a*b,0,255).astype(np.uint8),np.where(a>5,255,0).astype(np.uint8)],axis=-1),"RGBA").save(o,"PNG")
    c+=1
    if c%2000==0: print(f"  {c}...",flush=True)
print(f"  Tinted {c} tiles")
PYEOF

cat > /tmp/pack.py << 'PYEOF'
import sqlite3,os,sys,glob
d,o,n,z=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]
db=sqlite3.connect(o)
db.execute("CREATE TABLE IF NOT EXISTS tiles(zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_data BLOB)")
db.execute("CREATE TABLE IF NOT EXISTS metadata(name TEXT,value TEXT)")
db.execute("CREATE UNIQUE INDEX IF NOT EXISTS tile_index ON tiles(zoom_level,tile_column,tile_row)")
c=0
for p in glob.glob(os.path.join(d,"*","*","*.png")):
    ps=p.split(os.sep);zl,x=int(ps[-3]),int(ps[-2]);y=(1<<zl)-1-int(ps[-1].replace(".png",""))
    with open(p,"rb") as f: db.execute("INSERT OR REPLACE INTO tiles VALUES(?,?,?,?)",(zl,x,y,f.read()))
    c+=1
    if c%5000==0: db.commit()
db.commit()
for k,v in[("name",n),("format","png"),("minzoom",z),("maxzoom",z),("type","overlay")]:
    db.execute("INSERT OR REPLACE INTO metadata VALUES(?,?)",(k,v))
db.commit();db.close();print(f"Packed {c} tiles")
PYEOF

echo "--- Tinting ---"
IFS=',' read -ra THEMES <<< "${STYLES}"
for T in "\${THEMES[@]}"; do
    echo "  \$T..."; mkdir -p "tiles/\$T"
    python3 /tmp/tint.py tiles/gray "\$T" "tiles/\$T"
done

echo "--- Packing ---"
for T in "\${THEMES[@]}"; do
    M="\$WORKDIR/z${ZOOM}-\${T}.mbtiles"; rm -f "\$M"
    python3 /tmp/pack.py "tiles/\$T" "\$M" "${NAME} z${ZOOM} \${T}" "${ZOOM}"
    du -h "\$M"
done

echo "--- Upload ---"
for T in "\${THEMES[@]}"; do
    aws s3 cp "\$WORKDIR/z${ZOOM}-\${T}.mbtiles" "${S3_OUTPUT}/" --quiet
    echo "  uploaded z${ZOOM}-\${T}.mbtiles"
done

mkdir -p /data/output; touch /data/output/DONE
echo "=== DONE at \$(date) ==="
USERDATA

USERDATA_B64=$(base64 < "$USERDATA_FILE")
rm -f "$USERDATA_FILE"

echo "🚀 Launching spot instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --region "$AWS_REGION" \
    --image-id "$AMI" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_PAIR_NAME" \
    --security-group-ids "$SECURITY_GROUP" \
    "${IAM_ARGS[@]}" \
    --instance-market-options '{"MarketType":"spot","SpotOptions":{"SpotInstanceType":"one-time"}}' \
    --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":${DISK_GB},\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" \
    --user-data "$USERDATA_B64" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=ilhmp-z${ZOOM}},{Key=Purpose,Value=ilhmp-zoom}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "   Instance: $INSTANCE_ID"
aws ec2 wait instance-running --region "$AWS_REGION" --instance-ids "$INSTANCE_ID"
WORKER_IP=$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "   IP: $WORKER_IP"

cat > "/tmp/ilhmp-zoom-z${ZOOM}.env" << EOF
WORKER_INSTANCE_ID=$INSTANCE_ID
WORKER_IP=$WORKER_IP
WORKER_KEY=$SSH_KEY
ZOOM=$ZOOM
STYLES=$STYLES
S3_OUTPUT=$S3_OUTPUT
KEEP=$KEEP
EOF

echo ""
echo "✅ Worker launched!"
echo "Monitor: ssh -i $SSH_KEY ubuntu@$WORKER_IP 'tail -f /var/log/ilhmp.log'"
echo "Check:   ssh -i $SSH_KEY ubuntu@$WORKER_IP 'test -f /data/output/DONE && echo DONE || echo RUNNING'"
echo ""
echo "When done, patch into combined mbtiles:"
for T in $(echo "$STYLES" | tr ',' ' '); do
    echo "   aws/patch-zoom.sh --source ${S3_OUTPUT}/z${ZOOM}-${T}.mbtiles --target <combined-${T}.mbtiles> --zoom ${ZOOM}"
done
echo ""
echo "Terminate: aws ec2 terminate-instances --region $AWS_REGION --instance-ids $INSTANCE_ID"
