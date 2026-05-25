# Design Agent

AI-powered design-to-deployment agent. Describe a website in plain language → get a live URL.

Uses [Google Stitch](https://stitch.withgoogle.com/) for screen design, [21st.dev](https://21st.dev/) for React components, and deploys to AWS (S3 + CloudFront).

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/DressPD/design-agent.git
cd design-agent
python -m venv .venv && source .venv/bin/activate
pip install -e .
playwright install chromium
```

### 2. Configure

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Where to get it |
|----------|----------------|
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |
| `TWENTYFIRST_API_KEY` | [21st.dev](https://21st.dev/) |
| `GITHUB_TOKEN` | [GitHub Settings → Developer settings → Fine-grained tokens](https://github.com/settings/tokens?type=beta) (scopes: `repo`, `delete_repo`) |
| `AWS_ACCESS_KEY_ID` | AWS IAM user with the policy in `infra/iam-policy.json` |
| `AWS_SECRET_ACCESS_KEY` | Same IAM user |
| `AWS_DEFAULT_REGION` | `eu-central-1` |

### 3. Run

```bash
source .env    # or: set -a; source .env; set +a
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
3. **Component** — Finds production React components from 21st.dev
4. **Build** — Scaffolds a Vite + React + Tailwind project
5. **Deploy** — Uploads to S3, serves via CloudFront
6. **Publish** — Pushes source to a public GitHub repo under your account
7. **Destroy** — Cleans up everything (S3 prefix, CloudFront cache, GitHub repo)

## Infrastructure

Pre-provisioned S3 bucket + CloudFront distribution. Each project deploys to its own URL prefix (`/{project-name}/`).

See `infra/iam-policy.json` for required AWS permissions.

## Technical Details

See [TECHNICAL_DOCS.md](TECHNICAL_DOCS.md) for architecture, project structure, and test documentation.
