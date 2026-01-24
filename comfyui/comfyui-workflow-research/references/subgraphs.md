# ComfyUI Subgraphs Reference

## What Are Subgraphs

Subgraphs (component nodes) are reusable nested workflows that appear as single nodes. Node types with UUID format (e.g., `a08c6e6f-a4af-4edf-90e1-e75883176677`) are subgraph references.

## Storage Locations

- **Blueprints (built-in):** `ComfyUI/blueprints/*.json`
- **Custom node subgraphs:** `custom_nodes/<pack>/subgraphs/*.json`
- **Workflow-embedded:** Inside workflow JSON under `definitions.subgraphs[]`

## JSON Structure

```json
{
  "definitions": {
    "subgraphs": [{
      "id": "uuid-here",
      "version": 1,
      "name": "My Subgraph",
      "inputs": [{"name": "model", "type": "MODEL", "id": "uuid"}],
      "outputs": [{"name": "latent", "type": "LATENT", "id": "uuid"}],
      "nodes": [/* internal node graph */],
      "links": [/* internal connections */]
    }]
  }
}
```

## Script Commands

```bash
# List all subgraph definitions in workflow
workflow_tools.py list-subgraphs workflow.json

# Get detailed subgraph info
workflow_tools.py get-subgraph workflow.json UUID

# Extract subgraph to standalone file (for reuse)
workflow_tools.py extract-subgraph workflow.json UUID output.json

# Inject subgraph from file into workflow
workflow_tools.py inject-subgraph workflow.json subgraph.json

# Find nodes that use subgraph types
workflow_tools.py find-subgraph-nodes workflow.json
```

## Reuse Workflow

1. **Extract** working subgraph from source workflow
2. **Store** in `ComfyUI/blueprints/` or custom location
3. **Inject** into new workflows as needed

## Key Points

- Subgraph UUIDs are SHA256-based, generated at creation
- Internal nodes execute during workflow run (expanded dynamically)
- Subgraphs can expose inner widget values via `proxyWidgets`
- Entry IDs for discovery: `SHA256(source + file_path)`
