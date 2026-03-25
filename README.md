# agent-skills

A compliant skill marketplace containing reusable agent skills for AI assistants.

## Marketplace

The [`marketplace.json`](./marketplace.json) file is the root catalog for this marketplace. It lists all available skills with their metadata and follows the schema defined in [`marketplace.schema.json`](./marketplace.schema.json).

## Skills

| Skill | Description |
|-------|-------------|
| [build-check](./build-check/) | Runs a structured "build vs. buy vs. borrow" analysis to prevent unnecessary building and surface modern alternatives |
| [snoonu](./snoonu.com/) | Adds grocery items to cart via the Snoonu delivery platform in Qatar using browser automation |
| [comfyui-workflow-research](./comfyui/comfyui-workflow-research/) | Researches ComfyUI workflows, LoRAs, and custom nodes from community sources |

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
