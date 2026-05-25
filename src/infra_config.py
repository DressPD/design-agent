import os

S3_BUCKET = os.environ.get(
    "DESIGN_AGENT_S3_BUCKET", "design-agent-sites-363437155153"
)
CLOUDFRONT_DISTRIBUTION_ID = os.environ.get(
    "DESIGN_AGENT_CF_DIST_ID", "E13CVD2UT1V127"
)
CLOUDFRONT_DOMAIN = os.environ.get(
    "DESIGN_AGENT_CF_DOMAIN", "djth7oc46jvbj.cloudfront.net"
)
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-central-1")
