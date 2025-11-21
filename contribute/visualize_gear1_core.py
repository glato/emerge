#!/usr/bin/env python3
"""
Generate a clean, focused visualization of Gear 1 core architecture.
This filters out noise and shows only the essential dependencies.
"""

import json
import subprocess
from pathlib import Path

def generate_core_dot():
    """Generate GraphViz DOT file for Gear 1 core only."""

    # Load the dependency data
    with open('emerge-file_result_dependency_graph-data.json', 'r') as f:
        data = json.load(f)

    links = data.get('links', [])

    # Define Gear 1 core files
    gear1_core = {
        'orchestrator.py': 'Orchestrator\n(Main Coordinator)',
        'decomposer.py': 'Decomposer\n(Task Breakdown)',
        'executor.py': 'Executor\n(Sequential)',
        'state_manager.py': 'State Manager\n(Persistence)',
        'git_manager.py': 'Git Manager\n(Branches/PRs)',
        'backend.py': 'Backend\n(Adapters)',
        'models.py': 'Models\n(Data Layer)',
        'logger.py': 'Logger\n(Structured)',
        'main.py': 'Main\n(CLI)'
    }

    # Start DOT file
    dot = ['digraph GearOne {']
    dot.append('  rankdir=TB;')
    dot.append('  node [shape=box, style=filled, fillcolor=lightblue, fontname="Arial"];')
    dot.append('  edge [color=gray40];')
    dot.append('')

    # Add nodes with labels
    for file, label in gear1_core.items():
        node_id = file.replace('.py', '').replace('_', '')
        dot.append(f'  {node_id} [label="{label}"];')

    dot.append('')
    dot.append('  // Dependencies')

    # Add edges (only between core files)
    edges_added = set()
    for link in links:
        source = link.get('source', '')
        target = link.get('target', '')

        # Find which core files are involved
        source_file = None
        target_file = None

        for core_file in gear1_core.keys():
            if core_file in source:
                source_file = core_file
            if core_file in target:
                target_file = core_file

        if source_file and target_file and source_file != target_file:
            src_id = source_file.replace('.py', '').replace('_', '')
            tgt_id = target_file.replace('.py', '').replace('_', '')
            edge = (src_id, tgt_id)

            if edge not in edges_added:
                dot.append(f'  {src_id} -> {tgt_id};')
                edges_added.add(edge)

    # Add layer grouping
    dot.append('')
    dot.append('  // Layer grouping')
    dot.append('  {rank=same; main;}')
    dot.append('  {rank=same; orchestrator;}')
    dot.append('  {rank=same; decomposer; executor; gitmanager; statemanager; backend; logger;}')
    dot.append('  {rank=same; models;}')

    dot.append('}')

    return '\n'.join(dot)

def generate_community_dot():
    """Generate GraphViz DOT file showing module communities."""

    with open('emerge-file_result_dependency_graph-data.json', 'r') as f:
        data = json.load(f)

    nodes = data.get('nodes', [])

    # Group by community
    communities = {}
    for node in nodes:
        file_path = node.get('id', '')
        community = node.get('louvain_modularity', 0)

        # Only src files, not tests
        if '/src/' in file_path and '/test' not in file_path.lower():
            if community not in communities:
                communities[community] = []

            clean_name = file_path.split('/')[-1].replace('.py', '')
            communities[community].append(clean_name)

    # Generate DOT
    dot = ['digraph Communities {']
    dot.append('  rankdir=LR;')
    dot.append('  node [shape=box, style=filled];')
    dot.append('')

    colors = ['lightblue', 'lightgreen', 'lightyellow', 'lightpink', 'lightgray',
              'lavender', 'peachpuff', 'lightcyan']

    for i, (comm_id, files) in enumerate(sorted(communities.items(),
                                                  key=lambda x: len(x[1]),
                                                  reverse=True)[:8]):
        color = colors[i % len(colors)]
        dot.append(f'  subgraph cluster_{comm_id} {{')
        dot.append(f'    label="Community {comm_id} ({len(files)} files)";')
        dot.append(f'    color={color};')
        dot.append(f'    style=filled;')

        # Show up to 5 files per community
        for file in sorted(files)[:5]:
            node_id = f'c{comm_id}_{file}'.replace('-', '').replace('_', '')
            dot.append(f'    {node_id} [label="{file}"];')

        if len(files) > 5:
            node_id = f'c{comm_id}_more'
            dot.append(f'    {node_id} [label="... {len(files)-5} more", shape=plaintext];')

        dot.append('  }')
        dot.append('')

    dot.append('}')

    return '\n'.join(dot)

if __name__ == '__main__':
    print("Generating Gear 1 Core Architecture Diagram...")

    # Generate DOT files
    core_dot = generate_core_dot()
    with open('gear1_core.dot', 'w') as f:
        f.write(core_dot)

    community_dot = generate_community_dot()
    with open('communities.dot', 'w') as f:
        f.write(community_dot)

    print("✓ Generated gear1_core.dot")
    print("✓ Generated communities.dot")
    print()

    # Try to generate PNG if graphviz is installed
    try:
        subprocess.run(['dot', '-V'], capture_output=True, check=True)

        print("Generating PNG images...")
        subprocess.run(['dot', '-Tpng', 'gear1_core.dot', '-o', 'gear1_core.png'], check=True)
        subprocess.run(['dot', '-Tpng', 'communities.dot', '-o', 'communities.png'], check=True)

        print("✓ Generated gear1_core.png")
        print("✓ Generated communities.png")
        print()
        print("Open the PNG files to view clean visualizations!")

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("GraphViz not installed. Install with:")
        print("  sudo apt install graphviz")
        print()
        print("Or view DOT files online at:")
        print("  https://dreampuf.github.io/GraphvizOnline/")
        print()
        print("Just paste the contents of gear1_core.dot or communities.dot")

    print()
    print("Also generated: ARCHITECTURE_ANALYSIS.md (detailed report)")
