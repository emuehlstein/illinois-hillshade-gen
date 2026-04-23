#!/usr/bin/env bash
# Shared configuration for ilhmp AWS scripts.
# Sources aws/.env if present, then sets defaults.

AWS_DIR="$(cd "$(dirname "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}")" && pwd)"

if [[ -f "$AWS_DIR/.env" ]]; then
    # shellcheck disable=SC1091
    source "$AWS_DIR/.env"
fi

: "${AWS_REGION:=us-east-2}"
: "${SSH_KEY:=$HOME/.ssh/mapserver-ec2.pem}"
: "${KEY_PAIR_NAME:=mapserver}"
: "${INSTANCE_TYPE:=c7g.2xlarge}"
: "${DISK_GB:=200}"
: "${TILE_SERVER_TILES_DIR:=/data/tiles}"

require_var() {
    local name="$1"
    if [[ -z "${!name:-}" ]]; then
        echo "❌ Required: $name (set in aws/.env or environment)"
        exit 1
    fi
}

get_ubuntu_arm64_ami() {
    aws ec2 describe-images \
        --region "$AWS_REGION" \
        --owners 099720109477 \
        --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-arm64-server-*" \
        --query 'sort_by(Images,&CreationDate)[-1].ImageId' \
        --output text
}
