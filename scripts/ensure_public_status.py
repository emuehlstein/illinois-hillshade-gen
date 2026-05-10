#!/usr/bin/env python3
"""Ensure s3://exaggeratedrelief/status/* has a public read policy statement."""
import json
import subprocess
import sys

BUCKET = "exaggeratedrelief"
STATEMENT = {
    "Sid": "PublicReadStatus",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": f"arn:aws:s3:::{BUCKET}/status/*",
}

# Fetch existing policy
result = subprocess.run(
    ["aws", "s3api", "get-bucket-policy", "--bucket", BUCKET,
     "--query", "Policy", "--output", "text"],
    capture_output=True, text=True,
)
if result.returncode == 0 and result.stdout.strip():
    policy = json.loads(result.stdout.strip())
else:
    policy = {"Version": "2012-10-17", "Statement": []}

stmts = policy.get("Statement", [])

# Check if already covered
if any(
    "status" in str(s.get("Resource", "")) and s.get("Effect") == "Allow"
    for s in stmts
):
    print("status/* already public read — nothing to do")
    sys.exit(0)

stmts.append(STATEMENT)
policy["Statement"] = stmts

put = subprocess.run(
    ["aws", "s3api", "put-bucket-policy", "--bucket", BUCKET,
     "--policy", json.dumps(policy)],
    capture_output=True, text=True,
)
if put.returncode == 0:
    print(f"✅ Added PublicReadStatus to {BUCKET} bucket policy")
else:
    print(f"❌ put-bucket-policy failed: {put.stderr}", file=sys.stderr)
    sys.exit(1)
