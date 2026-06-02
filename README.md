# agent-skills

A skill marketplace containing reusable agent skills for AI assistants.

## Marketplaces

This repo is published under **two** marketplace formats so it works with multiple consumers:

- [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) — Claude Code's native plugin marketplace format. Install with:
  ```
  /plugin marketplace add Bewinxed/agent-skills
  /plugin install svelte-house-rules@bewinxed-agent-skills
  ```
- [`marketplace.json`](./marketplace.json) — custom catalog format following [`marketplace.schema.json`](./marketplace.schema.json), for other consumers that read this layout.

Both point at the same plugin/skill directories.

## Skills

| Skill | Description |
|-------|-------------|
| [build-check](./build-check/) | Runs a structured "build vs. buy vs. borrow" analysis to prevent unnecessary building and surface modern alternatives |
| [snoonu](./snoonu.com/) | Adds grocery items to cart via the Snoonu delivery platform in Qatar using browser automation |
| [comfyui-workflow-research](./comfyui/comfyui-workflow-research/) | Researches ComfyUI workflows, LoRAs, and custom nodes from community sources |
| [svelte-house-rules](./svelte-house-rules/) | Process discipline, library preferences, engineering taste, styling tokens, animations, mobile fixes, error handling, PostHog analytics, and swipe carousels for Svelte 5 / SvelteKit on Cloudflare Workers |

## Structure

Each skill directory contains:

- **`SKILL.md`** — Instructions for the AI agent with YAML frontmatter (`name`, `description`, optional `allowed-tools`)
- **`skill.json`** — Machine-readable skill manifest
- **`<name>.skill`** — Packaged `.skill` archive (zip) ready for installation

## Adding a Skill

1. Create a new directory under the relevant category (or at root level)
2. Add a `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: my-skill
   description: What the skill does and when to invoke it.
   allowed-tools: Read, Bash   # optional
   ---
   ```
3. Add a `skill.json` manifest following the schema in `marketplace.schema.json`
4. Package the skill: `zip -r my-skill.skill my-skill/`
5. Add the skill entry to `marketplace.json`
