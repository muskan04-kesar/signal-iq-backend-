import re
import os

def convert():
    base_dir = r"d:\signalIQ\signal-iq"
    backend_dir = r"d:\signalIQ\signal-iq-backend-\backend\simulation"

    with open(os.path.join(base_dir, "data", "civilLinesEdges.ts"), "r") as f:
        edges_ts = f.read()

    with open(os.path.join(base_dir, "data", "civilLinesSignals.ts"), "r") as f:
        signals_ts = f.read()

    # Extract block
    edges_match = re.search(r"export const CIVIL_LINES_EDGES_? = \[\n(.*?)\n\];", edges_ts, re.DOTALL)
    if edges_match:
        edges_str = edges_match.group(1)
    else:
        edges_match2 = re.search(r"export const CIVIL_LINES_EDGES = \[\n(.*?)\n\];", edges_ts, re.DOTALL)
        if not edges_match2:
            edges_str = re.sub(r"export const CIVIL_LINES_EDGES = \[", "[", edges_ts)
            edges_str = re.sub(r"\];", "]", edges_str)
        else:
            edges_str = edges_match2.group(1)

    signals_str = signals_ts
    signals_str = re.sub(r"export const CIVIL_LINES_SIGNALS = \[", "[", signals_str)
    signals_str = re.sub(r"\];", "]", signals_str)
    
    edges_str = edges_ts
    edges_str = re.sub(r"export const CIVIL_LINES_EDGES = \[", "[", edges_str)
    edges_str = re.sub(r"\];", "]", edges_str)

    # Replace keys
    for key in ['id', 'lat', 'lng', 'armAngles', 'source', 'target', 'distance']:
        signals_str = re.sub(fr"\b{key}:", f'"{key}":', signals_str)
        edges_str = re.sub(fr"\b{key}:", f'"{key}":', edges_str)

    # replace single quotes with double quotes
    signals_str = signals_str.replace("'", '"')
    edges_str = edges_str.replace("'", '"')

    out = f"""# Auto-generated topology from TS

CIVIL_LINES_SIGNALS = {signals_str.strip()}

CIVIL_LINES_EDGES = {edges_str.strip()}

# Helper dictionaries
topology_signals = {{s["id"]: s for s in CIVIL_LINES_SIGNALS}}

# Build adjacency
adjacency = {{s["id"]: [] for s in CIVIL_LINES_SIGNALS}}
for edge in CIVIL_LINES_EDGES:
    source = edge["source"]
    target = edge["target"]
    dist = edge["distance"]
    if source in adjacency and target in adjacency:
        # Undirected graph for routing? Yes, frontend routing says "It's an undirected graph physically"
        adjacency[source].append({{"target": target, "distance": dist}})
        adjacency[target].append({{"target": source, "distance": dist}})
"""
    with open(os.path.join(backend_dir, "topology.py"), "w") as f:
        f.write(out)

if __name__ == "__main__":
    convert()
