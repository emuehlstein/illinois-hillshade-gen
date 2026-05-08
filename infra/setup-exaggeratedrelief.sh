#!/usr/bin/env bash
# Setup AWS infrastructure for exaggeratedrelief.com
# Run once to create: S3 bucket, CloudFront distribution, Route 53 hosted zone, ACM cert
#
# Prerequisites:
#   - AWS CLI configured with admin access
#   - Domain: exaggeratedrelief.com (currently at GoDaddy)
#
# After running:
#   1. Update GoDaddy nameservers to the Route 53 NS records printed at the end
#   2. Wait for DNS propagation (~15-60 min)
#   3. Run ./setup-exaggeratedrelief.sh --validate-cert to complete ACM validation

set -euo pipefail

DOMAIN="exaggeratedrelief.com"
BUCKET="exaggeratedrelief"
REGION="us-east-2"
# ACM certs for CloudFront MUST be in us-east-1
CERT_REGION="us-east-1"

echo "🗺️  Setting up infrastructure for ${DOMAIN}"
echo ""

# ─── Step 1: S3 Bucket ───────────────────────────────────────────────
echo "📦 Step 1: Creating S3 bucket '${BUCKET}' in ${REGION}..."

if aws s3api head-bucket --bucket "${BUCKET}" 2>/dev/null; then
    echo "   Bucket already exists, skipping."
else
    aws s3 mb "s3://${BUCKET}" --region "${REGION}"
    echo "   ✅ Bucket created."
fi

# Block public access (CloudFront will use OAC)
aws s3api put-public-access-block \
    --bucket "${BUCKET}" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
echo "   ✅ Public access blocked (CloudFront OAC will provide access)."

# CORS for PMTiles range requests
aws s3api put-bucket-cors \
    --bucket "${BUCKET}" \
    --cors-configuration '{
        "CORSRules": [
            {
                "AllowedOrigins": ["*"],
                "AllowedMethods": ["GET", "HEAD"],
                "AllowedHeaders": ["Range", "If-Match", "If-None-Match"],
                "ExposeHeaders": ["Content-Range", "Content-Length", "ETag", "Accept-Ranges"],
                "MaxAgeSeconds": 86400
            }
        ]
    }'
echo "   ✅ CORS configured for PMTiles range requests."

# ─── Step 2: Route 53 Hosted Zone ────────────────────────────────────
echo ""
echo "🌐 Step 2: Creating Route 53 hosted zone for ${DOMAIN}..."

EXISTING_ZONE=$(aws route53 list-hosted-zones-by-name \
    --dns-name "${DOMAIN}" \
    --query "HostedZones[?Name=='${DOMAIN}.'].Id" \
    --output text 2>/dev/null || true)

if [[ -n "${EXISTING_ZONE}" && "${EXISTING_ZONE}" != "None" ]]; then
    ZONE_ID=$(echo "${EXISTING_ZONE}" | sed 's|/hostedzone/||')
    echo "   Hosted zone already exists: ${ZONE_ID}"
else
    ZONE_RESULT=$(aws route53 create-hosted-zone \
        --name "${DOMAIN}" \
        --caller-reference "ilhmp-$(date +%s)" \
        --query 'HostedZone.Id' \
        --output text)
    ZONE_ID=$(echo "${ZONE_RESULT}" | sed 's|/hostedzone/||')
    echo "   ✅ Hosted zone created: ${ZONE_ID}"
fi

# Get NS records
echo ""
echo "   📋 Route 53 nameservers (update these at GoDaddy):"
aws route53 get-hosted-zone --id "${ZONE_ID}" \
    --query 'DelegationSet.NameServers' \
    --output text | tr '\t' '\n' | sed 's/^/      /'

# ─── Step 3: ACM Certificate ─────────────────────────────────────────
echo ""
echo "🔒 Step 3: Requesting ACM certificate in ${CERT_REGION}..."

EXISTING_CERT=$(aws acm list-certificates \
    --region "${CERT_REGION}" \
    --query "CertificateSummaryList[?DomainName=='${DOMAIN}'].CertificateArn" \
    --output text 2>/dev/null || true)

if [[ -n "${EXISTING_CERT}" && "${EXISTING_CERT}" != "None" ]]; then
    CERT_ARN="${EXISTING_CERT}"
    echo "   Certificate already exists: ${CERT_ARN}"
else
    CERT_ARN=$(aws acm request-certificate \
        --region "${CERT_REGION}" \
        --domain-name "${DOMAIN}" \
        --subject-alternative-names "*.${DOMAIN}" \
        --validation-method DNS \
        --query 'CertificateArn' \
        --output text)
    echo "   ✅ Certificate requested: ${CERT_ARN}"
fi

# Get DNS validation records
echo "   Waiting for validation details..."
sleep 5

VALIDATION_JSON=$(aws acm describe-certificate \
    --region "${CERT_REGION}" \
    --certificate-arn "${CERT_ARN}" \
    --query 'Certificate.DomainValidationOptions[0].ResourceRecord' \
    --output json 2>/dev/null || echo "{}")

VALIDATION_NAME=$(echo "${VALIDATION_JSON}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Name',''))" 2>/dev/null || true)
VALIDATION_VALUE=$(echo "${VALIDATION_JSON}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Value',''))" 2>/dev/null || true)

if [[ -n "${VALIDATION_NAME}" ]]; then
    echo "   Adding DNS validation CNAME to Route 53..."
    aws route53 change-resource-record-sets \
        --hosted-zone-id "${ZONE_ID}" \
        --change-batch "{
            \"Changes\": [{
                \"Action\": \"UPSERT\",
                \"ResourceRecordSet\": {
                    \"Name\": \"${VALIDATION_NAME}\",
                    \"Type\": \"CNAME\",
                    \"TTL\": 300,
                    \"ResourceRecords\": [{\"Value\": \"${VALIDATION_VALUE}\"}]
                }
            }]
        }" > /dev/null
    echo "   ✅ Validation CNAME added. Certificate will auto-validate once NS records propagate."
else
    echo "   ⚠️  Could not get validation record yet. Run: aws acm describe-certificate --region ${CERT_REGION} --certificate-arn ${CERT_ARN}"
fi

# ─── Step 4: CloudFront Distribution ─────────────────────────────────
echo ""
echo "☁️  Step 4: Creating CloudFront distribution..."

# Check for existing distribution
EXISTING_DIST=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Aliases.Items[0]=='${DOMAIN}'].Id" \
    --output text 2>/dev/null || true)

if [[ -n "${EXISTING_DIST}" && "${EXISTING_DIST}" != "None" ]]; then
    echo "   Distribution already exists: ${EXISTING_DIST}"
    DIST_ID="${EXISTING_DIST}"
else
    # Create OAC for S3
    OAC_ID=$(aws cloudfront create-origin-access-control \
        --origin-access-control-config "{
            \"Name\": \"${BUCKET}-oac\",
            \"Description\": \"OAC for ${DOMAIN}\",
            \"SigningProtocol\": \"sigv4\",
            \"SigningBehavior\": \"always\",
            \"OriginAccessControlOriginType\": \"s3\"
        }" \
        --query 'OriginAccessControl.Id' \
        --output text 2>/dev/null || true)

    if [[ -z "${OAC_ID}" ]]; then
        # OAC might already exist
        OAC_ID=$(aws cloudfront list-origin-access-controls \
            --query "OriginAccessControlList.Items[?Name=='${BUCKET}-oac'].Id" \
            --output text 2>/dev/null || true)
    fi
    echo "   OAC: ${OAC_ID}"

    # Create distribution
    DIST_CONFIG=$(cat <<EOF
{
    "CallerReference": "ilhmp-$(date +%s)",
    "Aliases": {
        "Quantity": 2,
        "Items": ["${DOMAIN}", "www.${DOMAIN}"]
    },
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [{
            "Id": "S3-${BUCKET}",
            "DomainName": "${BUCKET}.s3.${REGION}.amazonaws.com",
            "OriginAccessControlId": "${OAC_ID}",
            "S3OriginConfig": {
                "OriginAccessIdentity": ""
            }
        }]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-${BUCKET}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        },
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": { "Forward": "none" },
            "Headers": {
                "Quantity": 0
            }
        },
        "Compress": true,
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000
    },
    "CacheBehaviors": {
        "Quantity": 1,
        "Items": [{
            "PathPattern": "tiles/*",
            "TargetOriginId": "S3-${BUCKET}",
            "ViewerProtocolPolicy": "redirect-to-https",
            "AllowedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"],
                "CachedMethods": {
                    "Quantity": 2,
                    "Items": ["GET", "HEAD"]
                }
            },
            "ForwardedValues": {
                "QueryString": false,
                "Cookies": { "Forward": "none" },
                "Headers": {
                    "Quantity": 0
                }
            },
            "Compress": false,
            "MinTTL": 0,
            "DefaultTTL": 604800,
            "MaxTTL": 31536000
        }]
    },
    "ViewerCertificate": {
        "ACMCertificateArn": "${CERT_ARN}",
        "SSLSupportMethod": "sni-only",
        "MinimumProtocolVersion": "TLSv1.2_2021"
    },
    "Comment": "exaggeratedrelief.com - Illinois hillshade tiles",
    "Enabled": true,
    "HttpVersion": "http2and3",
    "PriceClass": "PriceClass_100"
}
EOF
)

    DIST_ID=$(aws cloudfront create-distribution \
        --distribution-config "${DIST_CONFIG}" \
        --query 'Distribution.Id' \
        --output text)
    echo "   ✅ Distribution created: ${DIST_ID}"
fi

# Get distribution domain
DIST_DOMAIN=$(aws cloudfront get-distribution \
    --id "${DIST_ID}" \
    --query 'Distribution.DomainName' \
    --output text)
echo "   CloudFront domain: ${DIST_DOMAIN}"

# ─── Step 5: S3 Bucket Policy for CloudFront OAC ─────────────────────
echo ""
echo "🔑 Step 5: Setting bucket policy for CloudFront access..."

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)

aws s3api put-bucket-policy \
    --bucket "${BUCKET}" \
    --policy "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [{
            \"Sid\": \"AllowCloudFrontServicePrincipal\",
            \"Effect\": \"Allow\",
            \"Principal\": {
                \"Service\": \"cloudfront.amazonaws.com\"
            },
            \"Action\": \"s3:GetObject\",
            \"Resource\": \"arn:aws:s3:::${BUCKET}/*\",
            \"Condition\": {
                \"StringEquals\": {
                    \"AWS:SourceArn\": \"arn:aws:cloudfront::${AWS_ACCOUNT_ID}:distribution/${DIST_ID}\"
                }
            }
        }]
    }"
echo "   ✅ Bucket policy set."

# ─── Step 6: Route 53 DNS Records ────────────────────────────────────
echo ""
echo "🔗 Step 6: Creating DNS records..."

aws route53 change-resource-record-sets \
    --hosted-zone-id "${ZONE_ID}" \
    --change-batch "{
        \"Changes\": [
            {
                \"Action\": \"UPSERT\",
                \"ResourceRecordSet\": {
                    \"Name\": \"${DOMAIN}\",
                    \"Type\": \"A\",
                    \"AliasTarget\": {
                        \"HostedZoneId\": \"Z2FDTNDATAQYW2\",
                        \"DNSName\": \"${DIST_DOMAIN}\",
                        \"EvaluateTargetHealth\": false
                    }
                }
            },
            {
                \"Action\": \"UPSERT\",
                \"ResourceRecordSet\": {
                    \"Name\": \"www.${DOMAIN}\",
                    \"Type\": \"A\",
                    \"AliasTarget\": {
                        \"HostedZoneId\": \"Z2FDTNDATAQYW2\",
                        \"DNSName\": \"${DIST_DOMAIN}\",
                        \"EvaluateTargetHealth\": false
                    }
                }
            }
        ]
    }" > /dev/null
echo "   ✅ DNS A records (alias) created for ${DOMAIN} and www.${DOMAIN}"

# ─── Summary ──────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Infrastructure setup complete!"
echo ""
echo "  S3 Bucket:    s3://${BUCKET}"
echo "  CloudFront:   ${DIST_ID} (${DIST_DOMAIN})"
echo "  Route 53:     ${ZONE_ID}"
echo "  ACM Cert:     ${CERT_ARN}"
echo ""
echo "⚠️  NEXT STEPS:"
echo ""
echo "  1. Update GoDaddy nameservers to Route 53 NS records above"
echo "  2. Wait for DNS propagation (15-60 min)"
echo "  3. ACM cert will auto-validate via Route 53 DNS"
echo "  4. Upload content: aws s3 cp index.html s3://${BUCKET}/"
echo "  5. Test: https://${DOMAIN}"
echo "═══════════════════════════════════════════════════════════════"

# Save IDs for other scripts
cat > "$(dirname "$0")/.infra-ids" <<EOF
ZONE_ID=${ZONE_ID}
DIST_ID=${DIST_ID}
DIST_DOMAIN=${DIST_DOMAIN}
CERT_ARN=${CERT_ARN}
BUCKET=${BUCKET}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
EOF
echo ""
echo "   IDs saved to infra/.infra-ids"
