# Design Agent

AI agent that creates React frontends from natural language. Uses [Stitch](https://stitch.googleapis.com) for screen design and [21st.dev](https://21st.dev) for React components, then deploys to AWS (S3 + CloudFront).

Built with [Strands Agents](https://github.com/strands-agents/sdk-python) on Amazon Bedrock (Claude Sonnet 4.6).

## Prerequisites

- Python 3.11+
- Node.js 18+ (for Vite builds)
- AWS CLI configured with `hyver-prod` profile
- GitHub CLI (`gh`) authenticated
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

The agent reads keys from `~/.config/opencode/.env` (auto-loaded by `.zshrc`). Required vars:

```
GOOGLE_API_KEY=<your-stitch-api-key>
TWENTYFIRST_API_KEY=<your-21st-dev-api-key>
```

If these are already set as environment variables, the `.env` file is not needed.

### Infrastructure

S3 bucket and CloudFront distribution are pre-provisioned via Terraform:

```
S3 bucket:       design-agent-sites-363437155153
CloudFront:      E13CVD2UT1V127
CloudFront URL:  https://djth7oc46jvbj.cloudfront.net
```

To re-provision from scratch:

```bash
AWS_PROFILE=hyver-prod terraform -chdir=infra/terraform init
AWS_PROFILE=hyver-prod terraform -chdir=infra/terraform apply
# Update src/infra_config.py with new output values
```

## Usage

```bash
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

Agent: [generates React components via 21st.dev]
       [scaffolds Vite + React + Tailwind project]
       [creates GitHub repo: bean-and-brew]
       [deploys to S3 + CloudFront]
       [takes desktop + mobile screenshots]

       Done! Here are your links:
       - Live site: https://djth7oc46jvbj.cloudfront.net
       - GitHub: https://github.com/your-user/bean-and-brew
       - Screenshots saved to /tmp/design-agent-screenshots/bean-and-brew/

You: Looks great. Now destroy it.

Agent: [empties S3, disables CloudFront, deletes GitHub repo]
       All resources for "bean-and-brew" have been destroyed.
```

### Quick Test — Verify the Full Pipeline

To test without the interactive loop, you can exercise each tool individually:

```bash
# 1. Activate venv
source .venv/bin/activate

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
    dist_path='/tmp/design-agent-builds/test-app/dist',
    s3_bucket='design-agent-sites-363437155153',
    cloudfront_distribution_id='E13CVD2UT1V127'
)
print(result)
"

# 4. Verify it's live
curl -s https://djth7oc46jvbj.cloudfront.net | head -5

# 5. Test screenshot
python -c "
from src.tools.screenshot import take_screenshots
result = take_screenshots(
    url='https://djth7oc46jvbj.cloudfront.net',
    project_name='test-app'
)
print(result)
"

# 6. Cleanup — remove from S3
AWS_PROFILE=hyver-prod aws s3 rm s3://design-agent-sites-363437155153/ --recursive
```

## Tests

```bash
pytest tests/ -v
```

96 unit tests covering all tools, config, and MCP client setup. All external calls (AWS, GitHub, npm, Playwright) are mocked.

## Project Structure

```
design-agent/
├── src/
│   ├── agent.py          # Main agent loop (Strands + Rich UI)
│   ├── config.py          # API key loading (~/.config/opencode/.env fallback)
│   ├── infra_config.py    # Pre-provisioned S3/CF resource IDs
│   ├── mcp/
│   │   └── clients.py     # Stitch (HTTP) + 21st.dev (stdio) MCP clients
│   └── tools/
│       ├── scaffold.py    # Vite + React + Tailwind project generator
│       ├── github.py      # Private repo creation via gh CLI
│       ├── deploy.py      # S3 sync + CloudFront invalidation
│       ├── destroy.py     # Tear down all resources
│       ├── screenshot.py  # Playwright desktop + mobile captures
│       └── manifest.py    # Resource tracking (JSON per project)
├── tests/                 # 96 unit tests
├── infra/terraform/       # S3 + CloudFront IaC
├── manifests/             # Runtime: project resource manifests
└── pyproject.toml
```
