---
name: comfyui-workflow-research
description: Research ComfyUI workflows, LoRAs, custom nodes, and techniques from community sources. Use when building or optimizing ComfyUI workflows, finding LoRAs, researching custom nodes, or troubleshooting. Discovers node schemas from ComfyUI's API and manipulates workflows programmatically to avoid token waste. Includes curated list of maintained efficiency node packs (Jan 2026).
---

# ComfyUI Workflow Research

## Core Principles

1. **Discover, don't assume.** Node APIs evolve. Query ComfyUI for current schemas.
2. **Programmatic workflow manipulation.** Workflows are large JSON—use scripts, not direct editing.
3. **Prefer core nodes.** Only install custom nodes when core lacks functionality.

## Environment Discovery

Check if server running: `curl -s http://localhost:8188/object_info | head -c 100`

If not running, ask user for ComfyUI path.

## Node Schema Discovery

Query `/object_info` endpoint or use `scripts/comfyui_api.py`:
- `list-nodes` - all available nodes
- `node-info NodeName` - detailed schema
- `search "keyword"` - find by name/category

Fallback: grep `NODE_CLASS_MAPPINGS` in custom_nodes source.

## Workflow Manipulation

Use `scripts/workflow_tools.py` to avoid loading full JSON:
- `summary` / `list-nodes` / `get-node` / `find-type` - reading
- `set-input` / `add-node` / `connect` / `remove-node` - modifying
- `list-subgraphs` / `get-subgraph` / `extract-subgraph` / `inject-subgraph` - subgraph ops

Direct JSON only for operations scripts don't support.

**Subgraphs:** Node types with UUID format are subgraph references. See [references/subgraphs.md](references/subgraphs.md) for extraction/reuse workflow.

## Community Research

Search patterns: `site:reddit.com/r/comfyui`, `site:github.com`, `site:civitai.com`

Follow comment links—corrections and version notes often buried there.

Civitai: verify model version—settings differ between versions.

Access failures: try Wayback Machine, search quoted snippets, ask user.

## Custom Node Selection

**Before installing any custom node:**
1. Query core nodes first: `scripts/comfyui_api.py search "switch"`
2. Check if core provides equivalent functionality
3. Verify GitHub activity (last commit date, open issues)
4. Prefer packs with >1k stars and recent maintenance

**When custom nodes are justified:**
- Core lacks the functionality entirely
- Node consolidates 5+ operations into one
- Reduces connection spaghetti significantly

**Efficiency packs reference:** See [references/efficiency-packs.md](references/efficiency-packs.md) for curated list of maintained packs, their focus areas, and consolidation ratios.

**Key signals to check:**
- GitHub stars and last commit date
- FLUX/newer model support if relevant
- Overlap conflicts with already-installed packs

## Documentation

Save findings to prevent re-research. Suggest `[comfyui_path]/user/default/workflows/Docs/`.
