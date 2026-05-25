# Design Agent

AI agent that creates React frontends from natural language. Uses [Google Stitch](https://stitch.withgoogle.com/) for AI screen design, then scaffolds React + Tailwind projects and deploys to AWS (S3 + CloudFront).

Built with [Strands Agents](https://github.com/strands-agents/sdk-python) on Amazon Bedrock (Claude Sonnet 4.6).

## Prerequisites

- Python 3.11+
- Node.js 18+ (for Vite builds)
- AWS credentials (SSO profile or static keys)
- GitHub CLI (`gh`) authenticated, or `GITHUB_TOKEN` set
- Playwright browsers installed

## Setup

```bash
cd ~/design-agent

python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"

# Install playwright browsers
playwright install chromium
```

### API Keys

Create a `.env` file in the project root (see `.env.example`):

```
GOOGLE_API_KEY=<your-stitch-api-key>
GITHUB_TOKEN=<your-github-pat>
```

The agent reads keys from environment variables first, falling back to the project `.env` file.

### Infrastructure

S3 bucket and CloudFront distribution are pre-provisioned via Terraform:

```
S3 bucket:       design-agent-sites-363437155153
CloudFront:      E13CVD2UT1V127
CloudFront URL:  https://djth7oc46jvbj.cloudfront.net
```

Each project deploys to its own URL prefix (`/{project-name}/`). A CloudFront Function handles per-prefix SPA routing.

To re-provision from scratch:

```bash
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform apply
# Update .env with DESIGN_AGENT_S3_BUCKET, DESIGN_AGENT_CF_DIST_ID, DESIGN_AGENT_CF_DOMAIN
```

## Usage

```bash
set -a; source .env; set +a
design-agent
# or: python -m src.agent
```

### Example Session — Creating a Landing Page

```
You: Create a modern landing page for a coffee shop called "Bean & Brew".
     Dark theme, warm tones, hero section with a tagline, menu highlights,
     and a footer with opening hours.

Agent: I'll start by creating a design in Stitch. Let me set up a dark,
       warm-toned design system first...
       [creates Stitch project, generates screens]
       Here's the initial design. What do you think?

You: Love it, but make the hero bigger and add a "Order Online" button.

Agent: [edits screens in Stitch]
       Updated. The hero now takes the full viewport with a prominent
       CTA button. Shall I proceed to build this?

You: Yes, build and deploy it.

Agent: [writes React components from approved Stitch designs]
       [scaffolds Vite + React + Tailwind project]
       [deploys to S3 + CloudFront]
       [creates public GitHub repo: bean-and-brew]
       [takes desktop + mobile screenshots]

       Done! Here are your links:
       - Live site: https://djth7oc46jvbj.cloudfront.net/bean-and-brew/
       - GitHub: https://github.com/your-user/bean-and-brew
       - Screenshots saved to /tmp/design-agent-screenshots/bean-and-brew/

You: Looks great. Now destroy it.

Agent: [empties S3 prefix, invalidates CloudFront, deletes GitHub repo]
       All resources for "bean-and-brew" have been destroyed.
```

### Quick Test — Verify the Full Pipeline

To test without the interactive loop, you can exercise each tool individually:

```bash
# 1. Activate venv + load env
source .venv/bin/activate
set -a; source .env; set +a

# 2. Test scaffold (creates a minimal React app)
python -c "
from src.tools.scaffold import scaffold_react_app
result = scaffold_react_app(
    project_name='test-app',
    components_json='[]',
    title='Test App',
    description='Pipeline test'
)
print(result)
"

# 3. Test deploy (uploads the built app to S3 + CF)
python -c "
from src.tools.deploy import deploy_to_aws
result = deploy_to_aws(
    project_name='test-app',
    dist_path='/tmp/design-agent-builds/test-app/dist',
    s3_bucket='design-agent-sites-363437155153',
    cloudfront_distribution_id='E13CVD2UT1V127'
)
print(result)
"

# 4. Verify it's live
curl -s https://djth7oc46jvbj.cloudfront.net/test-app/ | head -5

# 5. Test screenshot
python -c "
from src.tools.screenshot import take_screenshots
result = take_screenshots(
    url='https://djth7oc46jvbj.cloudfront.net/test-app/',
    project_name='test-app'
)
print(result)
"

# 6. Cleanup — remove from S3
python -c "
from src.tools.destroy import _destroy_s3
_destroy_s3('design-agent-sites-363437155153', 'test-app')
"
```

## Tests

```bash
pytest tests/ -v
```

89 unit tests covering all tools, config, and MCP client setup. All external calls (AWS, GitHub, npm, Playwright) are mocked.

## Project Structure

```
design-agent/
├── src/
│   ├── agent.py          # Main agent loop (Strands + Rich UI)
│   ├── config.py          # API key loading (env vars → project .env fallback)
│   ├── infra_config.py    # S3/CF resource IDs (env var overrides)
│   ├── mcp/
│   │   └── clients.py     # Stitch MCP client (HTTP/SSE)
│   └── tools/
│       ├── scaffold.py    # Vite + React + Tailwind project generator
│       ├── github.py      # Public repo creation via gh CLI / GITHUB_TOKEN
│       ├── deploy.py      # S3 sync (per-prefix) + CloudFront invalidation
│       ├── destroy.py     # Tear down project resources (S3 prefix, GH repo)
│       ├── screenshot.py  # Playwright desktop + mobile captures
│       └── manifest.py    # Resource tracking (JSON per project)
├── tests/                 # 89 unit tests
├── infra/
│   ├── terraform/         # S3 + CloudFront + CF Function IaC
│   └── iam-policy.json    # Required AWS permissions
├── Dockerfile
├── docker-compose.yml
├── manifests/             # Runtime: project resource manifests
├── .env.example           # Template for required env vars
└── pyproject.toml
```
