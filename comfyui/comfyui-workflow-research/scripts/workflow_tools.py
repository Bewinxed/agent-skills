#!/usr/bin/env python3
"""
Programmatic ComfyUI workflow manipulation.
Avoids loading entire workflows into context.

Usage:
    python workflow_tools.py summary workflow.json
    python workflow_tools.py list-nodes workflow.json
    python workflow_tools.py get-node workflow.json NODE_ID
    python workflow_tools.py find-type workflow.json "KSampler"
    python workflow_tools.py set-input workflow.json NODE_ID INPUT_NAME VALUE
    python workflow_tools.py set-widget workflow.json NODE_ID WIDGET_INDEX VALUE
    python workflow_tools.py add-node workflow.json "NodeType" [--pos X Y]
    python workflow_tools.py connect workflow.json SRC_ID OUT_SLOT DST_ID IN_NAME
    python workflow_tools.py disconnect workflow.json NODE_ID INPUT_NAME
    python workflow_tools.py remove-node workflow.json NODE_ID
    python workflow_tools.py duplicate workflow.json NODE_ID [--offset X Y]
    python workflow_tools.py create output.json
    python workflow_tools.py validate workflow.json

    Subgraph commands:
    python workflow_tools.py list-subgraphs workflow.json
    python workflow_tools.py get-subgraph workflow.json UUID
    python workflow_tools.py extract-subgraph workflow.json UUID output.json
    python workflow_tools.py inject-subgraph workflow.json subgraph.json
    python workflow_tools.py find-subgraph-nodes workflow.json  (lists nodes using subgraph types)
"""

import sys
import json
import uuid
import re
from typing import Any, Optional
from pathlib import Path


def is_uuid(s: str) -> bool:
    """Check if string is a UUID (subgraph type identifier)."""
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
    return bool(uuid_pattern.match(s))


def load_workflow(path: str) -> dict:
    """Load workflow JSON."""
    with open(path, 'r') as f:
        return json.load(f)


def save_workflow(path: str, workflow: dict) -> None:
    """Save workflow JSON."""
    with open(path, 'w') as f:
        json.dump(workflow, f, indent=2)
    print(f"Saved: {path}")


def get_nodes(workflow: dict) -> list:
    """Get nodes list, handling both formats."""
    # API format uses dict with string keys
    if "prompt" in workflow:
        return [(int(k), v) for k, v in workflow["prompt"].items()]
    # GUI format uses nodes array
    if "nodes" in workflow:
        return [(n.get("id"), n) for n in workflow["nodes"]]
    # Direct prompt format
    if all(k.isdigit() for k in workflow.keys()):
        return [(int(k), v) for k, v in workflow.items()]
    return []


def summary(workflow: dict) -> None:
    """Print workflow summary without full content."""
    nodes = get_nodes(workflow)
    
    print(f"Total nodes: {len(nodes)}")
    
    # Count by type
    type_counts = {}
    for node_id, node in nodes:
        node_type = node.get("class_type") or node.get("type", "unknown")
        type_counts[node_type] = type_counts.get(node_type, 0) + 1
    
    print(f"\nNode types ({len(type_counts)} unique):")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")
    
    # Links summary
    links = workflow.get("links", [])
    if links:
        print(f"\nConnections: {len(links)}")
    
    # Check for extra workflow data
    if "extra" in workflow:
        extra = workflow["extra"]
        if "ds" in extra:
            print(f"\nCanvas: zoom={extra['ds'].get('scale', 'N/A')}")


def list_nodes(workflow: dict) -> None:
    """List all nodes with IDs and types."""
    nodes = get_nodes(workflow)
    
    print(f"{'ID':<6} {'Type':<40} {'Title'}")
    print("-" * 60)
    
    for node_id, node in sorted(nodes, key=lambda x: x[0]):
        node_type = node.get("class_type") or node.get("type", "?")
        title = node.get("title", node.get("_meta", {}).get("title", ""))
        print(f"{node_id:<6} {node_type:<40} {title}")


def get_node(workflow: dict, node_id: int) -> None:
    """Get detailed info for a specific node."""
    nodes = dict(get_nodes(workflow))
    
    if node_id not in nodes:
        print(f"Node {node_id} not found")
        return
    
    node = nodes[node_id]
    
    print(f"Node ID: {node_id}")
    print(f"Type: {node.get('class_type') or node.get('type', '?')}")
    
    if "title" in node:
        print(f"Title: {node['title']}")
    
    # Inputs - API format
    if "inputs" in node and isinstance(node["inputs"], dict):
        print("\nInputs:")
        for name, value in node["inputs"].items():
            if isinstance(value, list) and len(value) == 2:
                # Link reference [node_id, output_slot]
                print(f"  {name}: <- Node {value[0]} [slot {value[1]}]")
            else:
                print(f"  {name}: {value}")
    
    # Inputs - GUI format
    if "inputs" in node and isinstance(node["inputs"], list):
        print("\nInput slots:")
        for inp in node["inputs"]:
            link = inp.get("link")
            link_str = f" <- link {link}" if link else " (unconnected)"
            print(f"  {inp.get('name', '?')}: {inp.get('type', '?')}{link_str}")
    
    # Widget values - GUI format
    if "widgets_values" in node:
        print("\nWidget values:")
        for i, val in enumerate(node["widgets_values"]):
            # Truncate long values
            val_str = str(val)
            if len(val_str) > 60:
                val_str = val_str[:60] + "..."
            print(f"  [{i}]: {val_str}")
    
    # Outputs - GUI format
    if "outputs" in node:
        print("\nOutputs:")
        for out in node["outputs"]:
            links = out.get("links", [])
            link_str = f" -> {len(links)} connection(s)" if links else ""
            print(f"  {out.get('name', '?')}: {out.get('type', '?')}{link_str}")
    
    # Position
    if "pos" in node:
        print(f"\nPosition: {node['pos']}")


def find_type(workflow: dict, type_pattern: str) -> None:
    """Find all nodes matching a type pattern."""
    nodes = get_nodes(workflow)
    pattern_lower = type_pattern.lower()
    
    matches = []
    for node_id, node in nodes:
        node_type = node.get("class_type") or node.get("type", "")
        if pattern_lower in node_type.lower():
            matches.append((node_id, node_type))
    
    if not matches:
        print(f"No nodes matching '{type_pattern}'")
        return
    
    print(f"Found {len(matches)} nodes matching '{type_pattern}':")
    for node_id, node_type in matches:
        print(f"  ID {node_id}: {node_type}")


def set_input(workflow: dict, path: str, node_id: int, input_name: str, value: str) -> None:
    """Set an input value on a node (API format)."""
    # Try to parse value as JSON (for numbers, bools, etc.)
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value
    
    # Handle API format
    if str(node_id) in workflow:
        workflow[str(node_id)]["inputs"][input_name] = parsed_value
        save_workflow(path, workflow)
        print(f"Set node {node_id}.{input_name} = {parsed_value}")
        return
    
    if "prompt" in workflow and str(node_id) in workflow["prompt"]:
        workflow["prompt"][str(node_id)]["inputs"][input_name] = parsed_value
        save_workflow(path, workflow)
        print(f"Set node {node_id}.{input_name} = {parsed_value}")
        return
    
    print(f"Node {node_id} not found in API format. Use set-widget for GUI format.")


def set_widget(workflow: dict, path: str, node_id: int, widget_index: int, value: str) -> None:
    """Set a widget value by index (GUI format)."""
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value
    
    if "nodes" not in workflow:
        print("Not a GUI format workflow")
        return
    
    for node in workflow["nodes"]:
        if node.get("id") == node_id:
            if "widgets_values" not in node:
                node["widgets_values"] = []
            
            # Extend if needed
            while len(node["widgets_values"]) <= widget_index:
                node["widgets_values"].append(None)
            
            node["widgets_values"][widget_index] = parsed_value
            save_workflow(path, workflow)
            print(f"Set node {node_id} widget[{widget_index}] = {parsed_value}")
            return
    
    print(f"Node {node_id} not found")


def add_node(workflow: dict, path: str, node_type: str, pos: tuple = (100, 100)) -> None:
    """Add a new node to the workflow."""
    # Find max ID
    nodes = get_nodes(workflow)
    max_id = max((n[0] for n in nodes), default=0)
    new_id = max_id + 1
    
    # GUI format
    if "nodes" in workflow:
        new_node = {
            "id": new_id,
            "type": node_type,
            "pos": list(pos),
            "size": [200, 100],
            "inputs": [],
            "outputs": [],
            "widgets_values": []
        }
        workflow["nodes"].append(new_node)
        save_workflow(path, workflow)
        print(f"Added node {new_id} of type {node_type}")
        return
    
    # API format
    target = workflow.get("prompt", workflow)
    target[str(new_id)] = {
        "class_type": node_type,
        "inputs": {}
    }
    save_workflow(path, workflow)
    print(f"Added node {new_id} of type {node_type}")


def connect(workflow: dict, path: str, src_id: int, out_slot: int, dst_id: int, in_name: str) -> None:
    """Connect two nodes."""
    # API format - just set the input reference
    if str(dst_id) in workflow or ("prompt" in workflow and str(dst_id) in workflow.get("prompt", {})):
        target = workflow.get("prompt", workflow)
        target[str(dst_id)]["inputs"][in_name] = [str(src_id), out_slot]
        save_workflow(path, workflow)
        print(f"Connected: Node {src_id}[{out_slot}] -> Node {dst_id}.{in_name}")
        return
    
    # GUI format - need to add link
    if "nodes" in workflow:
        links = workflow.setdefault("links", [])
        max_link_id = max((l[0] for l in links), default=0)
        new_link_id = max_link_id + 1
        
        # Find output type from source node
        out_type = "unknown"
        for node in workflow["nodes"]:
            if node["id"] == src_id and "outputs" in node:
                if out_slot < len(node["outputs"]):
                    out_type = node["outputs"][out_slot].get("type", "unknown")
                    node["outputs"][out_slot].setdefault("links", []).append(new_link_id)
        
        # Find input slot index on destination
        in_slot = 0
        for node in workflow["nodes"]:
            if node["id"] == dst_id and "inputs" in node:
                for i, inp in enumerate(node["inputs"]):
                    if inp.get("name") == in_name:
                        in_slot = i
                        inp["link"] = new_link_id
                        break
        
        # [link_id, src_id, src_slot, dst_id, dst_slot, type]
        links.append([new_link_id, src_id, out_slot, dst_id, in_slot, out_type])
        save_workflow(path, workflow)
        print(f"Connected: Node {src_id}[{out_slot}] -> Node {dst_id}.{in_name} (link {new_link_id})")
        return
    
    print("Could not find nodes to connect")


def remove_node(workflow: dict, path: str, node_id: int) -> None:
    """Remove a node and its connections."""
    # API format
    if str(node_id) in workflow:
        del workflow[str(node_id)]
        # Clean up references
        for nid, node in workflow.items():
            if not isinstance(node, dict):
                continue
            inputs = node.get("inputs", {})
            for k, v in list(inputs.items()):
                if isinstance(v, list) and len(v) >= 1 and str(v[0]) == str(node_id):
                    del inputs[k]
        save_workflow(path, workflow)
        print(f"Removed node {node_id}")
        return
    
    # GUI format
    if "nodes" in workflow:
        workflow["nodes"] = [n for n in workflow["nodes"] if n.get("id") != node_id]
        # Remove links involving this node
        if "links" in workflow:
            workflow["links"] = [l for l in workflow["links"] 
                                if l[1] != node_id and l[3] != node_id]
        save_workflow(path, workflow)
        print(f"Removed node {node_id}")
        return
    
    print(f"Node {node_id} not found")


def duplicate_node(workflow: dict, path: str, node_id: int, offset: tuple = (50, 50)) -> None:
    """Duplicate a node."""
    nodes = dict(get_nodes(workflow))
    
    if node_id not in nodes:
        print(f"Node {node_id} not found")
        return
    
    source = nodes[node_id]
    max_id = max(nodes.keys())
    new_id = max_id + 1
    
    # Deep copy
    new_node = json.loads(json.dumps(source))
    
    if "id" in new_node:
        new_node["id"] = new_id
    
    if "pos" in new_node:
        new_node["pos"] = [new_node["pos"][0] + offset[0], 
                          new_node["pos"][1] + offset[1]]
    
    # Clear connections
    if "inputs" in new_node and isinstance(new_node["inputs"], list):
        for inp in new_node["inputs"]:
            inp["link"] = None
    if "outputs" in new_node:
        for out in new_node["outputs"]:
            out["links"] = []
    
    if "nodes" in workflow:
        workflow["nodes"].append(new_node)
    else:
        target = workflow.get("prompt", workflow)
        target[str(new_id)] = new_node
    
    save_workflow(path, workflow)
    print(f"Duplicated node {node_id} -> {new_id}")


def create_workflow(path: str) -> None:
    """Create a new empty workflow."""
    workflow = {
        "last_node_id": 0,
        "last_link_id": 0,
        "nodes": [],
        "links": [],
        "groups": [],
        "config": {},
        "extra": {
            "ds": {"scale": 1, "offset": [0, 0]}
        },
        "version": 0.4
    }
    save_workflow(path, workflow)


def validate(workflow: dict) -> None:
    """Validate workflow structure."""
    issues = []

    nodes = get_nodes(workflow)
    node_ids = set(n[0] for n in nodes)

    # Check for duplicate IDs
    if len(node_ids) != len(nodes):
        issues.append("Duplicate node IDs detected")

    # Check links reference valid nodes (GUI format)
    for link in workflow.get("links", []):
        if link[1] not in node_ids:
            issues.append(f"Link {link[0]} references missing source node {link[1]}")
        if link[3] not in node_ids:
            issues.append(f"Link {link[0]} references missing target node {link[3]}")

    # Check input references (API format)
    for node_id, node in nodes:
        if isinstance(node.get("inputs"), dict):
            for name, val in node["inputs"].items():
                if isinstance(val, list) and len(val) >= 1:
                    ref_id = int(val[0]) if isinstance(val[0], str) else val[0]
                    if ref_id not in node_ids:
                        issues.append(f"Node {node_id}.{name} references missing node {ref_id}")

    if issues:
        print(f"Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Workflow is valid")


# ============ SUBGRAPH COMMANDS ============

def get_subgraphs(workflow: dict) -> list:
    """Get all subgraph definitions from workflow."""
    definitions = workflow.get("definitions", {})
    return definitions.get("subgraphs", [])


def list_subgraphs(workflow: dict) -> None:
    """List all subgraph definitions in workflow."""
    subgraphs = get_subgraphs(workflow)

    if not subgraphs:
        print("No subgraph definitions in this workflow")
        return

    print(f"Found {len(subgraphs)} subgraph definition(s):\n")

    for sg in subgraphs:
        sg_id = sg.get("id", "?")
        name = sg.get("name", "Unnamed")
        inputs = sg.get("inputs", [])
        outputs = sg.get("outputs", [])
        nodes = sg.get("nodes", [])

        print(f"UUID: {sg_id}")
        print(f"  Name: {name}")
        print(f"  Inputs: {len(inputs)} - {[i.get('name', '?') for i in inputs]}")
        print(f"  Outputs: {len(outputs)} - {[o.get('name', '?') for o in outputs]}")
        print(f"  Internal nodes: {len(nodes)}")
        print()


def get_subgraph(workflow: dict, sg_uuid: str) -> None:
    """Get detailed info about a specific subgraph."""
    subgraphs = get_subgraphs(workflow)

    target = None
    for sg in subgraphs:
        if sg.get("id") == sg_uuid:
            target = sg
            break

    if not target:
        print(f"Subgraph {sg_uuid} not found")
        return

    print(f"Subgraph: {target.get('name', 'Unnamed')}")
    print(f"UUID: {target.get('id')}")
    print(f"Version: {target.get('version', 'N/A')}")

    print("\nInputs:")
    for inp in target.get("inputs", []):
        print(f"  {inp.get('name', '?')}: {inp.get('type', '?')}")

    print("\nOutputs:")
    for out in target.get("outputs", []):
        print(f"  {out.get('name', '?')}: {out.get('type', '?')}")

    print("\nInternal nodes:")
    for node in target.get("nodes", []):
        node_type = node.get("type", "?")
        title = node.get("title", "")
        print(f"  {node.get('id', '?')}: {node_type} {f'({title})' if title else ''}")


def extract_subgraph(workflow: dict, sg_uuid: str, output_path: str) -> None:
    """Extract a subgraph definition to a separate file."""
    subgraphs = get_subgraphs(workflow)

    target = None
    for sg in subgraphs:
        if sg.get("id") == sg_uuid:
            target = sg
            break

    if not target:
        print(f"Subgraph {sg_uuid} not found")
        return

    # Create standalone subgraph file format
    output = {
        "definitions": {
            "subgraphs": [target]
        }
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Extracted subgraph '{target.get('name', 'Unnamed')}' to {output_path}")


def inject_subgraph(workflow: dict, path: str, subgraph_path: str) -> None:
    """Inject a subgraph definition from file into workflow."""
    with open(subgraph_path, 'r') as f:
        sg_data = json.load(f)

    # Handle both formats: direct subgraph or wrapped in definitions
    if "definitions" in sg_data and "subgraphs" in sg_data["definitions"]:
        new_subgraphs = sg_data["definitions"]["subgraphs"]
    elif "id" in sg_data and "nodes" in sg_data:
        new_subgraphs = [sg_data]
    else:
        print("Invalid subgraph file format")
        return

    # Ensure workflow has definitions structure
    if "definitions" not in workflow:
        workflow["definitions"] = {}
    if "subgraphs" not in workflow["definitions"]:
        workflow["definitions"]["subgraphs"] = []

    existing_ids = {sg.get("id") for sg in workflow["definitions"]["subgraphs"]}

    added = 0
    for sg in new_subgraphs:
        if sg.get("id") not in existing_ids:
            workflow["definitions"]["subgraphs"].append(sg)
            added += 1
            print(f"Injected: {sg.get('name', 'Unnamed')} ({sg.get('id')})")
        else:
            print(f"Skipped (already exists): {sg.get('name', 'Unnamed')}")

    if added > 0:
        save_workflow(path, workflow)


def find_subgraph_nodes(workflow: dict) -> None:
    """Find all nodes that use subgraph types (UUIDs)."""
    nodes = get_nodes(workflow)

    subgraph_nodes = []
    for node_id, node in nodes:
        node_type = node.get("class_type") or node.get("type", "")
        if is_uuid(node_type):
            subgraph_nodes.append((node_id, node_type, node.get("title", "")))

    if not subgraph_nodes:
        print("No nodes using subgraph types found")
        return

    # Map UUIDs to names if definitions exist
    subgraphs = get_subgraphs(workflow)
    uuid_to_name = {sg.get("id"): sg.get("name", "?") for sg in subgraphs}

    print(f"Found {len(subgraph_nodes)} node(s) using subgraph types:\n")

    for node_id, sg_uuid, title in subgraph_nodes:
        sg_name = uuid_to_name.get(sg_uuid, "Unknown subgraph")
        print(f"Node {node_id}: {sg_name}")
        print(f"  UUID: {sg_uuid}")
        if title:
            print(f"  Title: {title}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "create" and len(sys.argv) >= 3:
        create_workflow(sys.argv[2])
        return
    
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    path = sys.argv[2]
    workflow = load_workflow(path)
    
    if cmd == "summary":
        summary(workflow)
    
    elif cmd == "list-nodes":
        list_nodes(workflow)
    
    elif cmd == "get-node" and len(sys.argv) >= 4:
        get_node(workflow, int(sys.argv[3]))
    
    elif cmd == "find-type" and len(sys.argv) >= 4:
        find_type(workflow, sys.argv[3])
    
    elif cmd == "set-input" and len(sys.argv) >= 6:
        set_input(workflow, path, int(sys.argv[3]), sys.argv[4], sys.argv[5])
    
    elif cmd == "set-widget" and len(sys.argv) >= 6:
        set_widget(workflow, path, int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
    
    elif cmd == "add-node" and len(sys.argv) >= 4:
        pos = (100, 100)
        if "--pos" in sys.argv:
            idx = sys.argv.index("--pos")
            pos = (int(sys.argv[idx+1]), int(sys.argv[idx+2]))
        add_node(workflow, path, sys.argv[3], pos)
    
    elif cmd == "connect" and len(sys.argv) >= 7:
        connect(workflow, path, int(sys.argv[3]), int(sys.argv[4]), 
                int(sys.argv[5]), sys.argv[6])
    
    elif cmd == "remove-node" and len(sys.argv) >= 4:
        remove_node(workflow, path, int(sys.argv[3]))
    
    elif cmd == "duplicate" and len(sys.argv) >= 4:
        offset = (50, 50)
        if "--offset" in sys.argv:
            idx = sys.argv.index("--offset")
            offset = (int(sys.argv[idx+1]), int(sys.argv[idx+2]))
        duplicate_node(workflow, path, int(sys.argv[3]), offset)
    
    elif cmd == "validate":
        validate(workflow)

    # Subgraph commands
    elif cmd == "list-subgraphs":
        list_subgraphs(workflow)

    elif cmd == "get-subgraph" and len(sys.argv) >= 4:
        get_subgraph(workflow, sys.argv[3])

    elif cmd == "extract-subgraph" and len(sys.argv) >= 5:
        extract_subgraph(workflow, sys.argv[3], sys.argv[4])

    elif cmd == "inject-subgraph" and len(sys.argv) >= 4:
        inject_subgraph(workflow, path, sys.argv[3])

    elif cmd == "find-subgraph-nodes":
        find_subgraph_nodes(workflow)

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
