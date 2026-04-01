#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-1}"
APP_NAME="${APP_NAME:-mobileid-production}"
ECR_REPOSITORY="${ECR_REPOSITORY:-mobileid-backend}"
ECS_CLUSTER="${ECS_CLUSTER:-mobileid-production}"
LOG_GROUP="${LOG_GROUP:-/ecs/mobileid-production}"
TABLE_PREFIX="${TABLE_PREFIX:-MobileIDProd-}"

require_aws_login() {
  if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "AWS credentials were not found."
    echo "Run 'aws login' first, then re-run this bootstrap script."
    exit 1
  fi
}

ensure_ecr_repository() {
  if aws ecr describe-repositories --repository-names "${ECR_REPOSITORY}" --region "${AWS_REGION}" >/dev/null 2>&1; then
    echo "ECR repository exists: ${ECR_REPOSITORY}"
    return
  fi

  aws ecr create-repository \
    --repository-name "${ECR_REPOSITORY}" \
    --region "${AWS_REGION}" \
    --image-scanning-configuration scanOnPush=true \
    --image-tag-mutability MUTABLE >/dev/null
  echo "Created ECR repository: ${ECR_REPOSITORY}"
}

ensure_log_group() {
  if aws logs describe-log-groups \
    --region "${AWS_REGION}" \
    --log-group-name-prefix "${LOG_GROUP}" \
    --query 'logGroups[?logGroupName==`'"${LOG_GROUP}"'`].logGroupName' \
    --output text | grep -qx "${LOG_GROUP}"; then
    echo "CloudWatch log group exists: ${LOG_GROUP}"
    return
  fi

  aws logs create-log-group --log-group-name "${LOG_GROUP}" --region "${AWS_REGION}"
  aws logs put-retention-policy \
    --log-group-name "${LOG_GROUP}" \
    --retention-in-days 14 \
    --region "${AWS_REGION}"
  echo "Created CloudWatch log group: ${LOG_GROUP}"
}

ensure_ecs_cluster() {
  if aws ecs describe-clusters \
    --clusters "${ECS_CLUSTER}" \
    --region "${AWS_REGION}" \
    --query 'clusters[?clusterName==`'"${ECS_CLUSTER}"'`].clusterName' \
    --output text | grep -qx "${ECS_CLUSTER}"; then
    echo "ECS cluster exists: ${ECS_CLUSTER}"
    return
  fi

  aws ecs create-cluster --cluster-name "${ECS_CLUSTER}" --region "${AWS_REGION}" >/dev/null
  echo "Created ECS cluster: ${ECS_CLUSTER}"
}

print_next_steps() {
  cat <<EOF

Bootstrap completed for low-cost shared resources.

Next steps that still need AWS account-specific values:
  1. Create or identify an internet-facing ALB, target group, security groups, and ECS service.
     - Use `/health/` as the ALB target group health check path.
     - Keep the target group matcher at `200` because the ECS task definition disables backend-side HTTP-to-HTTPS redirects.
  2. Create a CloudFront distribution in front of the backend ALB to get an AWS-managed HTTPS domain.
     - Use CloudFront viewer policy `redirect-to-https` and keep the origin protocol policy `http-only` for the low-cost setup.
  3. Create an Amplify app + branch for the frontend.
  4. Store the Django SECRET_KEY and Django admin bootstrap password in Secrets Manager and note their ARNs.
  5. Configure these GitHub repository variables:
     - ECR_REPOSITORY=${ECR_REPOSITORY}
     - ECS_CLUSTER=${ECS_CLUSTER}
     - ECS_SERVICE=<existing-ecs-service-name>
     - ECS_TASK_FAMILY=${APP_NAME}
     - BACKEND_CLOUDFRONT_DOMAIN=<your-cloudfront-domain>
     - ALLOWED_HOSTS=<comma-separated-hosts>
     - CORS_ALLOWED_ORIGINS=<comma-separated-origins>
     - CSRF_TRUSTED_ORIGINS=<comma-separated-origins>
     - ADMIN_URL_PATH=<non-default-admin-path>
     - EFS_FILE_SYSTEM_ID=<efs-file-system-id>
     - EFS_ACCESS_POINT_ID=<efs-access-point-id>
     - SQLITE_DB_PATH=/var/lib/mobileid/sqlite/db.sqlite3
     - DJANGO_SUPERUSER_USERNAME=<bootstrap-admin-username>
     - DJANGO_SUPERUSER_EMAIL=<bootstrap-admin-email>
     - AMPLIFY_APP_ID=<amplify-app-id>
     - AMPLIFY_BRANCH=<amplify-branch>
  6. Configure these GitHub secrets:
     - AWS_ROLE_ARN
     - ECS_EXECUTION_ROLE_ARN
     - ECS_TASK_ROLE_ARN
     - DJANGO_SECRET_KEY_ARN
     - DJANGO_SUPERUSER_PASSWORD_ARN
  7. Create DynamoDB tables with:
     cd src && python manage.py create_dynamodb_tables

EOF
}

require_aws_login
ensure_ecr_repository
ensure_log_group
ensure_ecs_cluster
print_next_steps
