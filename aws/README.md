# AWS EC2 Deployment

Run `ilhmp` on transient EC2 spot instances for large-county processing without tying up your machine.

## Setup

```bash
# 1. Copy and edit configuration
cp aws/env.example aws/.env

# 2. Create an IAM instance profile with S3 access (optional, for caching)
#    - Create role: "ilhmp-worker"
#    - Attach policy: S3 PutObject/GetObject/ListBucket on your cache bucket
#    - Create instance profile with the same name

# 3. Create or reuse a security group that allows SSH (port 22) inbound

# 4. Create or reuse an EC2 key pair, save the .pem file
```

## Workflows

### Generate hillshades for a county

```bash
# Launch worker, run ilhmp, results land in /data/output/
aws/launch.sh cook --dem dtm --style dark,light --zoom 10-16

# Monitor progress
ssh -i ~/.ssh/mykey.pem ubuntu@<worker-ip> 'tail -f /var/log/ilhmp.log'

# Pull results to local machine (or tile server)
aws/pull.sh cook

# Or pull to a tile server directly
TILE_SERVER_SSH=ubuntu@tiles.example.com aws/pull.sh cook
```

### Generate tiles for a specific zoom (from existing grayscale in S3)

For when you already have a large grayscale hillshade cached in S3 and want to generate tinted tiles for one zoom level at a time.

```bash
# Generate z14 tiles from existing S3 grayscale
aws/launch-zoom.sh \
    --gray s3://my-bucket/cook/intermediates/cook_lidar_gray_9x.tif \
    --zoom 14 \
    --styles dark,light \
    --name "Cook LiDAR 9x"

# When done, patch into combined mbtiles
aws/patch-zoom.sh \
    --source s3://my-bucket/cook/mbtiles/z14-dark.mbtiles \
    --target /data/tiles/cook-combined-dark.mbtiles \
    --zoom 14
```

## Configuration

All scripts source `aws/.env` if present. Override any variable via environment.

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | `us-east-2` |
| `SSH_KEY` | Path to EC2 key pair .pem | `~/.ssh/mapserver-ec2.pem` |
| `KEY_PAIR_NAME` | AWS key pair name | `mapserver` |
| `SECURITY_GROUP` | Security group ID (needs SSH) | *(required)* |
| `IAM_INSTANCE_PROFILE` | Instance profile for S3 access | *(optional)* |
| `INSTANCE_TYPE` | Worker instance type | `c7g.2xlarge` |
| `DISK_GB` | EBS volume size | `200` |
| `TILE_SERVER_SSH` | Tile server SSH (user@host) | *(optional)* |
| `TILE_SERVER_TILES_DIR` | Mbtiles dir on tile server | `/data/tiles` |

## Cost Estimates

| Instance | vCPUs | RAM | Spot Price | Typical County |
|----------|-------|-----|------------|----------------|
| c7g.xlarge | 4 | 8GB | ~$0.07/hr | Small (Putnam) |
| c7g.2xlarge | 8 | 16GB | ~$0.14/hr | Medium (Kane) |
| c7g.4xlarge | 16 | 32GB | ~$0.28/hr | Large (Cook) |

Most counties finish in 1-4 hours. A typical run costs $0.15-0.50.

## Scripts

| Script | Purpose |
|--------|---------|
| `launch.sh` | Launch EC2 worker for county generation |
| `pull.sh` | Pull results from worker, optionally upload to tile server |
| `launch-zoom.sh` | Launch worker for single-zoom tile generation |
| `patch-zoom.sh` | Patch z-level tiles into combined mbtiles |
| `config.sh` | Shared configuration loader |
