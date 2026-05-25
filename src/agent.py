import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models import BedrockModel

from src.infra_config import CLOUDFRONT_DISTRIBUTION_ID, CLOUDFRONT_DOMAIN, S3_BUCKET
from src.mcp.clients import create_stitch_client, create_twentyfirst_client
from src.tools import (
    deploy_to_aws,
    destroy_resources,
    github_create_and_push,
    load_manifest,
    save_manifest,
    scaffold_react_app,
    take_screenshots,
)

MODEL_ID = "eu.anthropic.claude-sonnet-4-6"
BEDROCK_REGION = "eu-central-1"

SYSTEM_PROMPT = """\
You are a Design Agent that creates beautiful, mobile-first React applications from natural language descriptions.

## Your Capabilities

You have TWO design tool suites (via MCP) plus deployment tools:

### Stitch (Google) — Screen Design
- create_project: Start a new Stitch project
- generate_screen_from_text: Generate full-page designs from descriptions
- edit_screens: Modify existing screens with text prompts
- generate_variants: Create design alternatives
- create_design_system / apply_design_system: Set visual theme (colors, fonts, shapes)
- list_screens / get_screen: Inspect generated designs

### 21st.dev — React Components
- 21st_magic_component_builder: Generate production-ready React components
- 21st_magic_component_inspiration: Browse component examples for ideas
- 21st_magic_component_refiner: Improve existing components

### Deployment Tools
- scaffold_react_app: Build a Vite + React + Tailwind project from components
- github_create_and_push: Create a public GitHub repo and push code
- deploy_to_aws: Deploy to S3 + CloudFront under a project prefix, returns live URL
- take_screenshots: Capture desktop + mobile screenshots of the live site
- save_manifest / load_manifest: Track provisioned resources per project
- destroy_resources: Tear down GitHub repo and clean S3 prefix for a project

## Workflow

1. UNDERSTAND: Ask clarifying questions about the user's vision — purpose, target audience, style, key pages/sections.
2. DESIGN: Create a Stitch project and design system first (choose colors, fonts, shape). Then generate screens. Present results and ask for feedback.
3. ITERATE: Edit screens based on feedback. Generate variants if the user wants alternatives. Repeat until approved.
4. COMPONENT: Use 21st.dev to build React components matching the approved designs. Prefer 21st_magic_component_builder for custom components; use 21st_magic_component_inspiration to find existing components that fit.
5. BUILD: scaffold_react_app creates a complete Vite+React+Tailwind project. Pass all component code in components_json. The project_name becomes the URL path prefix.
6. DEPLOY: deploy_to_aws (with project_name) → github_create_and_push → take_screenshots → save_manifest.
7. DELIVER: Return the live URL (https://{{cf_domain}}/{{project_name}}/), GitHub repo link, and screenshots.
8. DESTROY: When asked, load_manifest then destroy_resources. This deletes the S3 prefix and GitHub repo.

## Multi-Project Architecture

The S3 bucket and CloudFront distribution are shared across ALL projects.
Each project deploys to its own prefix: s3://{{bucket}}/{{project_name}}/.
Multiple projects coexist — deploying one never affects another.
The live URL for each project: https://{{cf_domain}}/{{project_name}}/

## Critical Rules

- ALWAYS create a Stitch design system before generating screens. Pick a color palette and font pairing that match the brand.
- ALWAYS get explicit approval on the design before deploying.
- ALWAYS save_manifest after every deploy so destroy works later. Include s3_prefix in the manifest.
- ALWAYS pass project_name to deploy_to_aws — it determines the URL path.
- Mobile-first: every design must work on 375px width.
- GitHub repos are public by default so the user can share the source.
- When the user says "destroy" or "tear down", load_manifest and call destroy_resources.
- Keep the conversation natural. You're a design collaborator, not a form-filler.
- If a tool fails, tell the user what happened and suggest a fix. Don't silently retry.

## Pre-Provisioned Infrastructure

- S3 bucket: {s3_bucket}
- CloudFront distribution ID: {cf_dist_id}
- CloudFront domain: https://{cf_domain}
""".format(s3_bucket=S3_BUCKET, cf_dist_id=CLOUDFRONT_DISTRIBUTION_ID, cf_domain=CLOUDFRONT_DOMAIN)

console = Console()


def _print_response(response: str) -> None:
    console.print(Panel(Markdown(str(response)), title="Design Agent", border_style="blue"))


def main() -> None:
    console.print(Panel(
        "[bold blue]Design Agent[/bold blue]\n"
        "Describe the app you want to build. I'll design it, build it, and deploy it.\n"
        "Type [bold]quit[/bold] to exit, [bold]destroy <project>[/bold] to tear down resources.",
        border_style="blue",
    ))

    stitch = create_stitch_client()
    twentyfirst = create_twentyfirst_client()

    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=BEDROCK_REGION,
        temperature=0.3,
    )

    agent = Agent(
        model=model,
        tools=[
            stitch,
            twentyfirst,
            scaffold_react_app,
            github_create_and_push,
            deploy_to_aws,
            destroy_resources,
            take_screenshots,
            save_manifest,
            load_manifest,
        ],
        system_prompt=SYSTEM_PROMPT,
        conversation_manager=SlidingWindowConversationManager(window_size=40),
    )

    while True:
        try:
            user_input = console.input("\n[bold green]You:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye.[/dim]")
            break

        with console.status("[bold blue]Thinking...[/bold blue]"):
            response = agent(user_input)

        _print_response(response)


if __name__ == "__main__":
    main()
