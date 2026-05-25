"""Deploy static site to S3 + CloudFront."""

import json
import subprocess
import time

import boto3
from strands import tool


@tool
def deploy_to_aws(
    project_name: str,
    dist_path: str,
    s3_bucket: str,
    cloudfront_distribution_id: str,
) -> str:
    """Deploy a built React application to AWS S3 under a project-specific prefix.

    Syncs dist/ to s3://{bucket}/{project_name}/, then invalidates the CloudFront cache
    for that prefix only. Multiple projects can coexist on the same bucket/distribution.

    Args:
        project_name: Project identifier used as the S3 key prefix (e.g. 'bean-and-brew').
        dist_path: Absolute path to the built dist/ directory.
        s3_bucket: Target S3 bucket name.
        cloudfront_distribution_id: CloudFront distribution ID for cache invalidation.

    Returns:
        JSON with the live URL (https://{domain}/{project_name}/), bucket, and status.
    """
    s3_prefix = f"s3://{s3_bucket}/{project_name}/"

    sync_result = subprocess.run(
        [
            "aws", "s3", "sync", dist_path, s3_prefix,
            "--delete",
            "--cache-control", "public,max-age=31536000,immutable",
            "--exclude", "index.html",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if sync_result.returncode != 0:
        return json.dumps({"error": "s3 sync failed", "stderr": sync_result.stderr[:500]})

    subprocess.run(
        [
            "aws", "s3", "cp",
            f"{dist_path}/index.html", f"{s3_prefix}index.html",
            "--cache-control", "no-cache,no-store,must-revalidate",
            "--content-type", "text/html",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    cf_client = boto3.client("cloudfront")
    cf_client.create_invalidation(
        DistributionId=cloudfront_distribution_id,
        InvalidationBatch={
            "Paths": {"Quantity": 1, "Items": [f"/{project_name}/*"]},
            "CallerReference": f"design-agent-{int(time.time())}-{project_name}",
        },
    )

    dist_config = cf_client.get_distribution(Id=cloudfront_distribution_id)
    domain = dist_config["Distribution"]["DomainName"]

    return json.dumps({
        "live_url": f"https://{domain}/{project_name}/",
        "cloudfront_domain": f"https://{domain}",
        "s3_bucket": s3_bucket,
        "s3_prefix": project_name,
        "cloudfront_distribution_id": cloudfront_distribution_id,
        "deploy_status": "success",
    })
