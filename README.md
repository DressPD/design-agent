# Design Agent

AI-powered design-to-deployment agent. Describe a website in plain language → get a live URL.

Uses [Google Stitch](https://stitch.withgoogle.com/) for AI screen design and deploys to AWS (S3 + CloudFront).

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/DressPD/design-agent.git
cd design-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` with your keys:

| Variable | Where to get it |
|----------|----------------|
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |
| `GITHUB_TOKEN` | [GitHub Settings → Tokens](https://github.com/settings/tokens) — scopes: `repo`, `delete_repo` |
| `AWS_DEFAULT_REGION` | `eu-central-1` |

**AWS auth** — pick one:
- **SSO**: add `AWS_PROFILE=your-profile` to `.env`
- **Static keys**: add `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` to `.env`

### 3. Run

```bash
set -a; source .env; set +a
design-agent
```

### 4. Talk to it

```
You: Create a landing page for a coffee shop called "Brew & Bean"
     with a hero section, menu, and contact form

Agent: [designs screens in Stitch, finds components, scaffolds React app,
        deploys to CloudFront, pushes to GitHub]

Your site is live at: https://djth7oc46jvbj.cloudfront.net/brew-and-bean/
GitHub repo: https://github.com/YourUsername/brew-and-bean
```

The agent iterates with you — ask for changes, new sections, different colors. When satisfied, it builds and deploys.

Say **"destroy [project-name]"** to tear down AWS resources and delete the GitHub repo.

## Docker

```bash
cp .env.example .env   # fill in keys
docker compose up --build
```

## What it does

1. **Design** — Creates UI screens using Google Stitch (AI design tool)
2. **Iterate** — Refines based on your feedback
3. **Build** — Writes React components from approved designs, scaffolds Vite + Tailwind project
4. **Deploy** — Uploads to S3, serves via CloudFront
5. **Publish** — Pushes source to a public GitHub repo under your account
6. **Destroy** — Cleans up everything (S3 prefix, CloudFront cache, GitHub repo)

## Tests

```bash
pytest tests/ -v
```

89 tests covering all tools and config.

## Infrastructure

Pre-provisioned S3 bucket + CloudFront distribution. Each project deploys to its own URL prefix (`/{project-name}/`).

To use your own infrastructure, run `terraform apply` in `infra/terraform/` and set `DESIGN_AGENT_S3_BUCKET`, `DESIGN_AGENT_CF_DIST_ID`, `DESIGN_AGENT_CF_DOMAIN` in `.env`.

See `infra/iam-policy.json` for required AWS permissions.

## Technical Details

See [TECHNICAL_DOCS.md](TECHNICAL_DOCS.md) for architecture, project structure, and test documentation.
