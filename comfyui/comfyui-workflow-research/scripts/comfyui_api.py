#!/usr/bin/env python3
"""
Query ComfyUI's API for node schemas and information.

Usage:
    python comfyui_api.py list-nodes [--category CATEGORY]
    python comfyui_api.py node-info NodeName [NodeName2 ...]
    python comfyui_api.py search "keyword"
    python comfyui_api.py categories
    python comfyui_api.py inputs NodeName
    python comfyui_api.py outputs NodeName
"""

import sys
import json
import urllib.request
import urllib.error
from typing import Optional

DEFAULT_URL = "http://localhost:8188"


def fetch_object_info(base_url: str = DEFAULT_URL) -> dict:
    """Fetch all node definitions from ComfyUI."""
    url = f"{base_url}/object_info"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"Error: Cannot connect to ComfyUI at {base_url}", file=sys.stderr)
        print(f"Make sure ComfyUI is running with --listen flag", file=sys.stderr)
        sys.exit(1)


def list_nodes(data: dict, category: Optional[str] = None) -> None:
    """List all available nodes, optionally filtered by category."""
    nodes = []
    for name, info in data.items():
        cat = info.get("category", "uncategorized")
        if category is None or category.lower() in cat.lower():
            nodes.append((cat, name))
    
    nodes.sort()
    current_cat = None
    for cat, name in nodes:
        if cat != current_cat:
            print(f"\n[{cat}]")
            current_cat = cat
        print(f"  {name}")


def node_info(data: dict, node_names: list) -> None:
    """Show detailed information for specific nodes."""
    for name in node_names:
        if name not in data:
            print(f"Node '{name}' not found.\n")
            continue
        
        info = data[name]
        print(f"{'='*60}")
        print(f"Node: {name}")
        print(f"Category: {info.get('category', 'N/A')}")
        print(f"Description: {info.get('description', 'N/A')}")
        
        # Inputs
        input_info = info.get("input", {})
        required = input_info.get("required", {})
        optional = input_info.get("optional", {})
        
        if required:
            print(f"\nRequired Inputs:")
            for inp_name, inp_spec in required.items():
                print_input_spec(inp_name, inp_spec)
        
        if optional:
            print(f"\nOptional Inputs:")
            for inp_name, inp_spec in optional.items():
                print_input_spec(inp_name, inp_spec)
        
        # Outputs
        output_types = info.get("output", [])
        output_names = info.get("output_name", [])
        if output_types:
            print(f"\nOutputs:")
            for i, out_type in enumerate(output_types):
                out_name = output_names[i] if i < len(output_names) else f"output_{i}"
                print(f"  [{i}] {out_name}: {out_type}")
        
        print()


def print_input_spec(name: str, spec: list) -> None:
    """Format and print an input specification."""
    if not spec:
        print(f"  {name}: (unknown)")
        return
    
    type_info = spec[0]
    constraints = spec[1] if len(spec) > 1 else {}
    
    # Type can be a string or list of options
    if isinstance(type_info, list):
        # Enum/dropdown - show options (truncate if too many)
        if len(type_info) <= 5:
            type_str = f"[{' | '.join(str(x) for x in type_info)}]"
        else:
            type_str = f"[{' | '.join(str(x) for x in type_info[:3])} | ... ({len(type_info)} options)]"
    else:
        type_str = str(type_info)
    
    # Add constraints if present
    constraint_parts = []
    if isinstance(constraints, dict):
        if "default" in constraints:
            constraint_parts.append(f"default={constraints['default']}")
        if "min" in constraints:
            constraint_parts.append(f"min={constraints['min']}")
        if "max" in constraints:
            constraint_parts.append(f"max={constraints['max']}")
        if "step" in constraints:
            constraint_parts.append(f"step={constraints['step']}")
    
    constraint_str = f" ({', '.join(constraint_parts)})" if constraint_parts else ""
    print(f"  {name}: {type_str}{constraint_str}")


def search_nodes(data: dict, keyword: str) -> None:
    """Search for nodes by keyword in name, category, or description."""
    keyword_lower = keyword.lower()
    matches = []
    
    for name, info in data.items():
        cat = info.get("category", "")
        desc = info.get("description", "")
        
        if (keyword_lower in name.lower() or 
            keyword_lower in cat.lower() or 
            keyword_lower in desc.lower()):
            matches.append((cat, name, desc[:80] if desc else ""))
    
    if not matches:
        print(f"No nodes found matching '{keyword}'")
        return
    
    matches.sort()
    print(f"Found {len(matches)} nodes matching '{keyword}':\n")
    for cat, name, desc in matches:
        print(f"  {name}")
        print(f"    Category: {cat}")
        if desc:
            print(f"    {desc}...")
        print()


def list_categories(data: dict) -> None:
    """List all node categories."""
    categories = set()
    for info in data.values():
        categories.add(info.get("category", "uncategorized"))
    
    for cat in sorted(categories):
        count = sum(1 for i in data.values() if i.get("category") == cat)
        print(f"  {cat} ({count} nodes)")


def show_inputs(data: dict, node_name: str) -> None:
    """Show just the inputs for a node (compact view)."""
    if node_name not in data:
        print(f"Node '{node_name}' not found.")
        return
    
    info = data[node_name]
    input_info = info.get("input", {})
    
    print(f"Inputs for {node_name}:")
    for section, inputs in [("required", input_info.get("required", {})), 
                            ("optional", input_info.get("optional", {}))]:
        if inputs:
            print(f"\n  [{section}]")
            for name, spec in inputs.items():
                print_input_spec(name, spec)


def show_outputs(data: dict, node_name: str) -> None:
    """Show just the outputs for a node."""
    if node_name not in data:
        print(f"Node '{node_name}' not found.")
        return
    
    info = data[node_name]
    output_types = info.get("output", [])
    output_names = info.get("output_name", [])
    
    print(f"Outputs for {node_name}:")
    for i, out_type in enumerate(output_types):
        out_name = output_names[i] if i < len(output_names) else f"output_{i}"
        print(f"  [{i}] {out_name}: {out_type}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    # Check for custom URL
    base_url = DEFAULT_URL
    if "--url" in sys.argv:
        idx = sys.argv.index("--url")
        base_url = sys.argv[idx + 1]
        sys.argv.pop(idx)
        sys.argv.pop(idx)
    
    data = fetch_object_info(base_url)
    
    if cmd == "list-nodes":
        category = None
        if "--category" in sys.argv:
            idx = sys.argv.index("--category")
            category = sys.argv[idx + 1]
        list_nodes(data, category)
    
    elif cmd == "node-info" and len(sys.argv) >= 3:
        node_info(data, sys.argv[2:])
    
    elif cmd == "search" and len(sys.argv) >= 3:
        search_nodes(data, sys.argv[2])
    
    elif cmd == "categories":
        list_categories(data)
    
    elif cmd == "inputs" and len(sys.argv) >= 3:
        show_inputs(data, sys.argv[2])
    
    elif cmd == "outputs" and len(sys.argv) >= 3:
        show_outputs(data, sys.argv[2])
    
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
