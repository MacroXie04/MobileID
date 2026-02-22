#!/usr/bin/env bash
set -euo pipefail

PREFIX="${PREFIX:-i2g-mobileid}"
DISPLAY_NAME="${DISPLAY_NAME:-i2g-MobileID}"
AWS_REGION="${AWS_REGION:-us-west-2}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query 'Account' --output text)}"

VPC_NAME="${PREFIX}-vpc"
VPC_CIDR="10.44.0.0/16"
SUBNET_PUB_A_NAME="${PREFIX}-subnet-public-a"
SUBNET_PUB_B_NAME="${PREFIX}-subnet-public-b"
SUBNET_DB_A_NAME="${PREFIX}-subnet-db-a"
SUBNET_DB_B_NAME="${PREFIX}-subnet-db-b"
SUBNET_PUB_A_CIDR="10.44.0.0/20"
SUBNET_PUB_B_CIDR="10.44.16.0/20"
SUBNET_DB_A_CIDR="10.44.128.0/20"
SUBNET_DB_B_CIDR="10.44.144.0/20"

IGW_NAME="${PREFIX}-igw"
RT_PUBLIC_NAME="${PREFIX}-rt-public"

ALB_SG_NAME="${PREFIX}-alb-sg"
ECS_SG_NAME="${PREFIX}-ecs-sg"
RDS_SG_NAME="${PREFIX}-rds-sg"

DB_SUBNET_GROUP_NAME="${PREFIX}-db-subnet-group"
RDS_INSTANCE_ID="${PREFIX}-mysql"
RDS_DB_NAME="mobileid_prod"
RDS_DB_USER="mobileid_admin"
RDS_CLASS="db.t4g.small"
RDS_STORAGE_GB="20"

ECR_REPO="${PREFIX}-backend"
ECS_CLUSTER="${PREFIX}-cluster"
ECS_SERVICE="${PREFIX}-api-svc"
ECS_TASK_FAMILY="${PREFIX}-api"
ECS_CONTAINER_NAME="${PREFIX}-api"

ALB_NAME="${PREFIX}-alb"
TG_NAME="${PREFIX}-tg"
CF_COMMENT="${DISPLAY_NAME}-backend-api"

AMPLIFY_APP_NAME="${DISPLAY_NAME}"
AMPLIFY_BRANCH="main"

ARTIFACT_BUCKET="${PREFIX}-frontend-artifacts-${ACCOUNT_ID}-${AWS_REGION}"

EXEC_ROLE_NAME="${PREFIX}-ecs-execution-role"
TASK_ROLE_NAME="${PREFIX}-ecs-task-role"
LOG_GROUP="/ecs/${PREFIX}-api"

BOOTSTRAP_SECRET_NAME="${PREFIX}/bootstrap"
APP_SECRET_NAME="${PREFIX}/app"
DB_SECRET_NAME="${PREFIX}/db"

for forbidden in "itg-" "i2g-prod-" "innovate-to-grow-frontend" "E2866C7XYF6J3G"; do
  if [[ "$PREFIX" == *"$forbidden"* || "$DISPLAY_NAME" == *"$forbidden"* ]]; then
    echo "Refusing to proceed due to forbidden pattern: $forbidden"
    exit 1
  fi
done

if [[ "$PREFIX" != i2g-mobileid* ]]; then
  echo "PREFIX must start with i2g-mobileid"
  exit 1
fi

if [[ "$ACCOUNT_ID" != "394167325273" ]]; then
  echo "Unexpected AWS account: $ACCOUNT_ID"
  exit 1
fi

aws() {
  command aws --region "$AWS_REGION" "$@"
}

ensure_tag() {
  local resource_id="$1"
  local name="$2"
  command aws ec2 create-tags --region "$AWS_REGION" --resources "$resource_id" --tags \
    "Key=Name,Value=$name" \
    "Key=Project,Value=$DISPLAY_NAME" \
    "Key=ManagedBy,Value=MigrationScript" >/dev/null
}

ensure_vpc() {
  local vpc_id
  vpc_id="$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=$VPC_NAME" --query 'Vpcs[0].VpcId' --output text)"
  if [[ -z "$vpc_id" || "$vpc_id" == "None" ]]; then
    vpc_id="$(aws ec2 create-vpc --cidr-block "$VPC_CIDR" --query 'Vpc.VpcId' --output text)"
    ensure_tag "$vpc_id" "$VPC_NAME"
    aws ec2 modify-vpc-attribute --vpc-id "$vpc_id" --enable-dns-support '{"Value":true}'
    aws ec2 modify-vpc-attribute --vpc-id "$vpc_id" --enable-dns-hostnames '{"Value":true}'
  fi
  echo "$vpc_id"
}

ensure_subnet() {
  local vpc_id="$1" name="$2" cidr="$3" az="$4" map_public="$5"
  local subnet_id
  subnet_id="$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpc_id" "Name=tag:Name,Values=$name" --query 'Subnets[0].SubnetId' --output text)"
  if [[ -z "$subnet_id" || "$subnet_id" == "None" ]]; then
    subnet_id="$(aws ec2 create-subnet --vpc-id "$vpc_id" --cidr-block "$cidr" --availability-zone "$az" --query 'Subnet.SubnetId' --output text)"
    ensure_tag "$subnet_id" "$name"
    if [[ "$map_public" == "true" ]]; then
      aws ec2 modify-subnet-attribute --subnet-id "$subnet_id" --map-public-ip-on-launch
    fi
  fi
  echo "$subnet_id"
}

ensure_igw_and_routes() {
  local vpc_id="$1" pub_a="$2" pub_b="$3"
  local igw_id rt_id

  igw_id="$(aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$vpc_id" --query 'InternetGateways[0].InternetGatewayId' --output text)"
  if [[ -z "$igw_id" || "$igw_id" == "None" ]]; then
    igw_id="$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)"
    ensure_tag "$igw_id" "$IGW_NAME"
    aws ec2 attach-internet-gateway --internet-gateway-id "$igw_id" --vpc-id "$vpc_id"
  fi

  rt_id="$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$vpc_id" "Name=tag:Name,Values=$RT_PUBLIC_NAME" --query 'RouteTables[0].RouteTableId' --output text)"
  if [[ -z "$rt_id" || "$rt_id" == "None" ]]; then
    rt_id="$(aws ec2 create-route-table --vpc-id "$vpc_id" --query 'RouteTable.RouteTableId' --output text)"
    ensure_tag "$rt_id" "$RT_PUBLIC_NAME"
  fi

  aws ec2 create-route --route-table-id "$rt_id" --destination-cidr-block 0.0.0.0/0 --gateway-id "$igw_id" >/dev/null 2>&1 || true
  aws ec2 associate-route-table --route-table-id "$rt_id" --subnet-id "$pub_a" >/dev/null 2>&1 || true
  aws ec2 associate-route-table --route-table-id "$rt_id" --subnet-id "$pub_b" >/dev/null 2>&1 || true
}

ensure_sg() {
  local vpc_id="$1" name="$2" desc="$3"
  local sg_id
  sg_id="$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$vpc_id" "Name=group-name,Values=$name" --query 'SecurityGroups[0].GroupId' --output text)"
  if [[ -z "$sg_id" || "$sg_id" == "None" ]]; then
    sg_id="$(aws ec2 create-security-group --group-name "$name" --description "$desc" --vpc-id "$vpc_id" --query 'GroupId' --output text)"
    ensure_tag "$sg_id" "$name"
  fi
  echo "$sg_id"
}

ensure_secret() {
  local name="$1" value="$2"
  local arn
  arn="$(aws secretsmanager describe-secret --secret-id "$name" --query 'ARN' --output text 2>/dev/null || true)"
  if [[ -z "$arn" || "$arn" == "None" ]]; then
    arn="$(aws secretsmanager create-secret --name "$name" --secret-string "$value" --query 'ARN' --output text)"
  else
    aws secretsmanager put-secret-value --secret-id "$name" --secret-string "$value" >/dev/null
  fi
  echo "$arn"
}

ensure_iam_role() {
  local role_name="$1" trust_json="$2"
  local role_arn
  role_arn="$(aws iam get-role --role-name "$role_name" --query 'Role.Arn' --output text 2>/dev/null || true)"
  if [[ -z "$role_arn" || "$role_arn" == "None" ]]; then
    role_arn="$(aws iam create-role --role-name "$role_name" --assume-role-policy-document "$trust_json" --query 'Role.Arn' --output text)"
  fi
  echo "$role_arn"
}

echo "Bootstrapping isolated AWS resources for $DISPLAY_NAME in $AWS_REGION (account $ACCOUNT_ID)..."

VPC_ID="$(ensure_vpc)"
PUB_A="$(ensure_subnet "$VPC_ID" "$SUBNET_PUB_A_NAME" "$SUBNET_PUB_A_CIDR" "${AWS_REGION}a" true)"
PUB_B="$(ensure_subnet "$VPC_ID" "$SUBNET_PUB_B_NAME" "$SUBNET_PUB_B_CIDR" "${AWS_REGION}b" true)"
DB_A="$(ensure_subnet "$VPC_ID" "$SUBNET_DB_A_NAME" "$SUBNET_DB_A_CIDR" "${AWS_REGION}a" false)"
DB_B="$(ensure_subnet "$VPC_ID" "$SUBNET_DB_B_NAME" "$SUBNET_DB_B_CIDR" "${AWS_REGION}b" false)"
ensure_igw_and_routes "$VPC_ID" "$PUB_A" "$PUB_B"

ALB_SG_ID="$(ensure_sg "$VPC_ID" "$ALB_SG_NAME" "ALB SG for $DISPLAY_NAME")"
ECS_SG_ID="$(ensure_sg "$VPC_ID" "$ECS_SG_NAME" "ECS SG for $DISPLAY_NAME")"
RDS_SG_ID="$(ensure_sg "$VPC_ID" "$RDS_SG_NAME" "RDS SG for $DISPLAY_NAME")"

aws ec2 authorize-security-group-ingress --group-id "$ALB_SG_ID" --ip-permissions 'IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0,Description="public-http"}]' >/dev/null 2>&1 || true
aws ec2 authorize-security-group-ingress --group-id "$ECS_SG_ID" --ip-permissions "IpProtocol=tcp,FromPort=8080,ToPort=8080,UserIdGroupPairs=[{GroupId=$ALB_SG_ID,Description=alb-to-ecs}]" >/dev/null 2>&1 || true
aws ec2 authorize-security-group-ingress --group-id "$RDS_SG_ID" --ip-permissions "IpProtocol=tcp,FromPort=3306,ToPort=3306,UserIdGroupPairs=[{GroupId=$ECS_SG_ID,Description=ecs-to-rds}]" >/dev/null 2>&1 || true

if [[ -n "${TEMP_IMPORT_CIDR:-}" ]]; then
  aws ec2 authorize-security-group-ingress --group-id "$RDS_SG_ID" --protocol tcp --port 3306 --cidr "$TEMP_IMPORT_CIDR" >/dev/null 2>&1 || true
fi

if [[ "$(aws rds describe-db-subnet-groups --db-subnet-group-name "$DB_SUBNET_GROUP_NAME" --query 'DBSubnetGroups[0].DBSubnetGroupName' --output text 2>/dev/null || true)" == "None" || -z "$(aws rds describe-db-subnet-groups --db-subnet-group-name "$DB_SUBNET_GROUP_NAME" --query 'DBSubnetGroups[0].DBSubnetGroupName' --output text 2>/dev/null || true)" ]]; then
  aws rds create-db-subnet-group \
    --db-subnet-group-name "$DB_SUBNET_GROUP_NAME" \
    --db-subnet-group-description "$DISPLAY_NAME DB subnet group" \
    --subnet-ids "$DB_A" "$DB_B" >/dev/null
fi

aws ecr describe-repositories --repository-names "$ECR_REPO" >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name "$ECR_REPO" --image-scanning-configuration scanOnPush=true >/dev/null

aws ecs describe-clusters --clusters "$ECS_CLUSTER" --query 'clusters[0].clusterArn' --output text >/dev/null 2>&1 || true
if [[ "$(aws ecs describe-clusters --clusters "$ECS_CLUSTER" --query 'clusters[0].clusterArn' --output text 2>/dev/null || true)" == "None" ]]; then
  aws ecs create-cluster --cluster-name "$ECS_CLUSTER" >/dev/null
fi

aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --query 'logGroups[0].logGroupName' --output text | grep -q "$LOG_GROUP" || \
  aws logs create-log-group --log-group-name "$LOG_GROUP" >/dev/null
aws logs put-retention-policy --log-group-name "$LOG_GROUP" --retention-in-days 14 >/dev/null

TRUST_DOC='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
EXEC_ROLE_ARN="$(ensure_iam_role "$EXEC_ROLE_NAME" "$TRUST_DOC")"
TASK_ROLE_ARN="$(ensure_iam_role "$TASK_ROLE_NAME" "$TRUST_DOC")"

aws iam attach-role-policy --role-name "$EXEC_ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy >/dev/null 2>&1 || true

RDS_PASSWORD="$(aws secretsmanager get-secret-value --secret-id "$BOOTSTRAP_SECRET_NAME" --query 'SecretString' --output text 2>/dev/null | python3 -c 'import json,sys; s=sys.stdin.read().strip(); print(json.loads(s).get("RDS_MASTER_PASSWORD",""))' 2>/dev/null || true)"
if [[ -z "$RDS_PASSWORD" ]]; then
  RDS_PASSWORD="$(openssl rand -base64 30 | tr -dc 'A-Za-z0-9' | cut -c1-28)"
  ensure_secret "$BOOTSTRAP_SECRET_NAME" "{\"RDS_MASTER_PASSWORD\":\"$RDS_PASSWORD\"}" >/dev/null
fi

RDS_EXISTS="$(aws rds describe-db-instances --db-instance-identifier "$RDS_INSTANCE_ID" --query 'DBInstances[0].DBInstanceIdentifier' --output text 2>/dev/null || true)"
if [[ -z "$RDS_EXISTS" || "$RDS_EXISTS" == "None" ]]; then
  aws rds create-db-instance \
    --db-instance-identifier "$RDS_INSTANCE_ID" \
    --db-instance-class "$RDS_CLASS" \
    --engine mysql \
    --engine-version 8.0.43 \
    --master-username "$RDS_DB_USER" \
    --master-user-password "$RDS_PASSWORD" \
    --allocated-storage "$RDS_STORAGE_GB" \
    --storage-type gp3 \
    --multi-az \
    --db-subnet-group-name "$DB_SUBNET_GROUP_NAME" \
    --vpc-security-group-ids "$RDS_SG_ID" \
    --no-publicly-accessible \
    --db-name "$RDS_DB_NAME" \
    --backup-retention-period 7 \
    --deletion-protection >/dev/null
fi

aws rds wait db-instance-available --db-instance-identifier "$RDS_INSTANCE_ID"
RDS_ENDPOINT="$(aws rds describe-db-instances --db-instance-identifier "$RDS_INSTANCE_ID" --query 'DBInstances[0].Endpoint.Address' --output text)"
DB_URL="mysql://${RDS_DB_USER}:${RDS_PASSWORD}@${RDS_ENDPOINT}:3306/${RDS_DB_NAME}"

APP_SECRET_ARN="$(ensure_secret "$APP_SECRET_NAME" '{"SECRET_KEY":"CHANGE_ME","ALLOWED_HOSTS":"*","CORS_ALLOWED_ORIGINS":"","CSRF_TRUSTED_ORIGINS":"","ADMIN_URL_PATH":"admin","DJANGO_SUPERUSER_USERNAME":"admin","DJANGO_SUPERUSER_EMAIL":"admin@example.com","DJANGO_SUPERUSER_PASSWORD":"CHANGE_ME"}')"
DB_SECRET_ARN="$(ensure_secret "$DB_SECRET_NAME" "{\"DATABASE_URL_AWS\":\"$DB_URL\"}")"

INLINE_POLICY_NAME="${PREFIX}-ecs-secrets-read"
cat > /tmp/secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": ["$APP_SECRET_ARN", "$DB_SECRET_ARN"]
    }
  ]
}
EOF
aws iam put-role-policy --role-name "$EXEC_ROLE_NAME" --policy-name "$INLINE_POLICY_NAME" --policy-document file:///tmp/secrets-policy.json >/dev/null

ALB_ARN="$(aws elbv2 describe-load-balancers --names "$ALB_NAME" --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || true)"
if [[ -z "$ALB_ARN" || "$ALB_ARN" == "None" ]]; then
  ALB_ARN="$(aws elbv2 create-load-balancer --name "$ALB_NAME" --subnets "$PUB_A" "$PUB_B" --security-groups "$ALB_SG_ID" --scheme internet-facing --type application --query 'LoadBalancers[0].LoadBalancerArn' --output text)"
fi

TG_ARN="$(aws elbv2 describe-target-groups --names "$TG_NAME" --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || true)"
if [[ -z "$TG_ARN" || "$TG_ARN" == "None" ]]; then
  TG_ARN="$(aws elbv2 create-target-group --name "$TG_NAME" --protocol HTTP --port 8080 --vpc-id "$VPC_ID" --target-type ip --health-check-path /health/ --health-check-protocol HTTP --health-check-port traffic-port --query 'TargetGroups[0].TargetGroupArn' --output text)"
fi

LISTENER_ARN="$(aws elbv2 describe-listeners --load-balancer-arn "$ALB_ARN" --query 'Listeners[?Port==`80`].ListenerArn' --output text 2>/dev/null || true)"
if [[ -z "$LISTENER_ARN" || "$LISTENER_ARN" == "None" ]]; then
  aws elbv2 create-listener --load-balancer-arn "$ALB_ARN" --protocol HTTP --port 80 --default-actions "Type=forward,TargetGroupArn=$TG_ARN" >/dev/null
fi

ALB_DNS="$(aws elbv2 describe-load-balancers --load-balancer-arns "$ALB_ARN" --query 'LoadBalancers[0].DNSName' --output text)"

CF_ID="$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='${CF_COMMENT}'].Id | [0]" --output text 2>/dev/null || true)"
CF_DOMAIN=""
if [[ -z "$CF_ID" || "$CF_ID" == "None" ]]; then
  caller_ref="${PREFIX}-$(date +%s)"
  cat > /tmp/cf-config.json <<EOF
{
  "CallerReference": "$caller_ref",
  "Comment": "$CF_COMMENT",
  "Enabled": true,
  "PriceClass": "PriceClass_100",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "alb-origin",
        "DomainName": "$ALB_DNS",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only",
          "OriginSslProtocols": {
            "Quantity": 1,
            "Items": ["TLSv1.2"]
          }
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "alb-origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 7,
      "Items": ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "POST", "DELETE"],
      "CachedMethods": {
        "Quantity": 3,
        "Items": ["GET", "HEAD", "OPTIONS"]
      }
    },
    "Compress": true,
    "ForwardedValues": {
      "QueryString": true,
      "Cookies": {"Forward": "all"}
    },
    "MinTTL": 0,
    "DefaultTTL": 0,
    "MaxTTL": 0
  },
  "Restrictions": {
    "GeoRestriction": {
      "RestrictionType": "none",
      "Quantity": 0
    }
  },
  "ViewerCertificate": {
    "CloudFrontDefaultCertificate": true
  }
}
EOF
  CF_ID="$(aws cloudfront create-distribution --distribution-config file:///tmp/cf-config.json --query 'Distribution.Id' --output text)"
fi
CF_DOMAIN="$(aws cloudfront get-distribution --id "$CF_ID" --query 'Distribution.DomainName' --output text)"

APP_ID="$(aws amplify list-apps --query "apps[?name=='${AMPLIFY_APP_NAME}'].appId | [0]" --output text)"
if [[ -z "$APP_ID" || "$APP_ID" == "None" ]]; then
  APP_ID="$(aws amplify create-app --name "$AMPLIFY_APP_NAME" --platform WEB --query 'app.appId' --output text)"
fi

if [[ "$(aws amplify get-branch --app-id "$APP_ID" --branch-name "$AMPLIFY_BRANCH" --query 'branch.branchName' --output text 2>/dev/null || true)" == "None" ]]; then
  aws amplify create-branch --app-id "$APP_ID" --branch-name "$AMPLIFY_BRANCH" >/dev/null
fi

if [[ "$(aws s3api head-bucket --bucket "$ARTIFACT_BUCKET" >/dev/null 2>&1; echo $?)" != "0" ]]; then
  aws s3api create-bucket --bucket "$ARTIFACT_BUCKET" --create-bucket-configuration "LocationConstraint=$AWS_REGION" >/dev/null
fi

cat <<EOF

Bootstrap complete.

Use these GitHub secrets:
AWS_REGION=$AWS_REGION
AWS_ACCOUNT_ID=$ACCOUNT_ID
AWS_ECR_REPOSITORY=$ECR_REPO
AWS_ECS_CLUSTER=$ECS_CLUSTER
AWS_ECS_SERVICE=$ECS_SERVICE
AWS_ECS_TASK_FAMILY=$ECS_TASK_FAMILY
AWS_ECS_CONTAINER_NAME=$ECS_CONTAINER_NAME
AWS_ECS_SUBNET_IDS=$PUB_A,$PUB_B
AWS_ECS_SECURITY_GROUP_ID=$ECS_SG_ID
AWS_ECS_EXECUTION_ROLE_ARN=$EXEC_ROLE_ARN
AWS_ECS_TASK_ROLE_ARN=$TASK_ROLE_ARN
AWS_ECS_TARGET_GROUP_ARN=$TG_ARN
AWS_ALB_NAME=$ALB_NAME
AWS_TARGET_GROUP_NAME=$TG_NAME
AWS_DB_SECRET_ARN=$DB_SECRET_ARN
AWS_APP_SECRET_ARN=$APP_SECRET_ARN
AWS_FRONTEND_AMPLIFY_APP_ID=$APP_ID
AWS_FRONTEND_AMPLIFY_APP_NAME=$AMPLIFY_APP_NAME
AWS_FRONTEND_AMPLIFY_BRANCH=$AMPLIFY_BRANCH
AWS_FRONTEND_ARTIFACT_BUCKET=$ARTIFACT_BUCKET
VITE_API_BASE_URL_AWS=https://$CF_DOMAIN
AWS_BACKEND_HEALTHCHECK_URL=https://$CF_DOMAIN

RDS endpoint:
$RDS_ENDPOINT

EOF
