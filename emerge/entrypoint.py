"""
Detects entry points in code and traces dependency paths for visualization.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, List, Set, Optional, Any
import re
import logging
import coloredlogs

from emerge.log import Logger

LOGGER = Logger(logging.getLogger('entrypoint'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class EntryPoint:
    """Represents a code entry point (main function, API route, CLI command, etc.)"""

    def __init__(self, file_path: str, name: str, entry_type: str, line_number: Optional[int] = None):
        self.file_path = file_path
        self.name = name
        self.type = entry_type
        self.line_number = line_number
        self.label = f"{name} ({file_path})"
        self.color = None  # Will be assigned later

    def __repr__(self):
        return f"EntryPoint({self.file_path}:{self.name}, type={self.type})"

    def __eq__(self, other):
        if isinstance(other, EntryPoint):
            return self.file_path == other.file_path and self.name == other.name
        return False

    def __hash__(self):
        return hash((self.file_path, self.name))


class EntryPointDetector:
    """Detects entry points in source code based on patterns and conventions."""

    # Common entry point patterns for different languages
    PYTHON_PATTERNS = [
        (r'if\s+__name__\s*==\s*["\']__main__["\']', 'python_main', 'Python main guard'),
        (r'def\s+main\s*\(', 'python_main_function', 'Main function'),
        (r'@app\.route\(', 'flask_route', 'Flask route'),
        (r'@click\.command\(', 'click_command', 'Click CLI command'),
        (r'@click\.group\(', 'click_group', 'Click CLI group'),
        (r'parser\s*=\s*argparse\.ArgumentParser', 'argparse_cli', 'Argparse CLI'),
        (r'FastAPI\(', 'fastapi_app', 'FastAPI application'),
        (r'@fastapi\.get\(|@fastapi\.post\(', 'fastapi_route', 'FastAPI route'),
    ]

    JAVASCRIPT_PATTERNS = [
        (r'app\.get\(|app\.post\(|app\.put\(|app\.delete\(', 'express_route', 'Express route'),
        (r'export\s+default\s+function', 'default_export', 'Default export function'),
        (r'if\s*\(\s*require\.main\s*===\s*module\s*\)', 'node_main', 'Node.js main'),
    ]

    JAVA_PATTERNS = [
        (r'public\s+static\s+void\s+main\s*\(', 'java_main', 'Java main method'),
        (r'@SpringBootApplication', 'spring_boot_app', 'Spring Boot application'),
        (r'@RestController', 'spring_controller', 'Spring REST controller'),
    ]

    def __init__(self, analysis):
        """Initialize the entry point detector.

        Args:
            analysis: The Analysis object containing file results and configuration.
        """
        self.analysis = analysis
        self.detected_entry_points: List[EntryPoint] = []
        self.manual_entry_points: List[EntryPoint] = []

    def detect_all_entry_points(self) -> List[EntryPoint]:
        """Detect all entry points in the analyzed files.

        Returns:
            List of detected EntryPoint objects.
        """
        LOGGER.info_start('detecting entry points in analyzed files')

        # First, add any manually specified entry points
        if hasattr(self.analysis, 'path_analysis') and self.analysis.path_analysis:
            if 'entry_points' in self.analysis.path_analysis:
                for ep_config in self.analysis.path_analysis['entry_points']:
                    entry_point = EntryPoint(
                        file_path=ep_config.get('file', ''),
                        name=ep_config.get('function', ep_config.get('name', 'unknown')),
                        entry_type='manual'
                    )
                    entry_point.label = ep_config.get('label', entry_point.label)
                    entry_point.color = ep_config.get('color', None)
                    self.manual_entry_points.append(entry_point)
                    LOGGER.debug(f'added manual entry point: {entry_point}')

        # Auto-detect entry points if enabled
        if hasattr(self.analysis, 'path_analysis') and self.analysis.path_analysis:
            if self.analysis.path_analysis.get('detect_entry_points', True):
                self._auto_detect_entry_points()

        # Combine manual and detected entry points
        all_entry_points = list(set(self.manual_entry_points + self.detected_entry_points))

        LOGGER.info_done(f'found {len(all_entry_points)} entry points')
        return all_entry_points

    def _auto_detect_entry_points(self):
        """Auto-detect entry points by scanning file content."""

        # Get patterns from config or use defaults
        custom_patterns = []
        if hasattr(self.analysis, 'path_analysis') and self.analysis.path_analysis:
            detect_config = self.analysis.path_analysis.get('detect_entry_points', {})
            if isinstance(detect_config, dict) and 'patterns' in detect_config:
                custom_patterns = detect_config['patterns']

        # Scan all file results
        for file_path, file_result in self.analysis.file_results.items():
            # Get file content from filesystem graph if available
            filesystem_graph = self.analysis.graph_representations.get('filesystem_graph')
            if not filesystem_graph:
                continue

            filesystem_node = filesystem_graph.filesystem_nodes.get(file_path)
            if not filesystem_node or not filesystem_node.content:
                continue

            content = filesystem_node.content

            # Detect Python entry points
            if file_path.endswith('.py'):
                self._detect_python_entry_points(file_path, content)

            # Detect JavaScript entry points
            elif file_path.endswith('.js') or file_path.endswith('.ts'):
                self._detect_javascript_entry_points(file_path, content)

            # Detect Java entry points
            elif file_path.endswith('.java'):
                self._detect_java_entry_points(file_path, content)

            # Apply custom patterns if specified
            if custom_patterns:
                self._apply_custom_patterns(file_path, content, custom_patterns)

    def _detect_python_entry_points(self, file_path: str, content: str):
        """Detect Python entry points."""
        lines = content.split('\n')

        for i, line in enumerate(lines):
            for pattern, entry_type, description in self.PYTHON_PATTERNS:
                if re.search(pattern, line):
                    # Extract function name if possible
                    name_match = re.search(r'def\s+(\w+)', line)
                    name = name_match.group(1) if name_match else entry_type

                    entry_point = EntryPoint(file_path, name, entry_type, i + 1)

                    if entry_point not in self.detected_entry_points:
                        self.detected_entry_points.append(entry_point)
                        LOGGER.debug(f'detected {description} at {file_path}:{i+1}')

    def _detect_javascript_entry_points(self, file_path: str, content: str):
        """Detect JavaScript/TypeScript entry points."""
        lines = content.split('\n')

        for i, line in enumerate(lines):
            for pattern, entry_type, description in self.JAVASCRIPT_PATTERNS:
                if re.search(pattern, line):
                    # Extract function or route name if possible
                    name_match = re.search(r'function\s+(\w+)|[\'"]([^\'\"]+)[\'"]', line)
                    name = name_match.group(1) or name_match.group(2) if name_match else entry_type

                    entry_point = EntryPoint(file_path, name, entry_type, i + 1)

                    if entry_point not in self.detected_entry_points:
                        self.detected_entry_points.append(entry_point)
                        LOGGER.debug(f'detected {description} at {file_path}:{i+1}')

    def _detect_java_entry_points(self, file_path: str, content: str):
        """Detect Java entry points."""
        lines = content.split('\n')

        for i, line in enumerate(lines):
            for pattern, entry_type, description in self.JAVA_PATTERNS:
                if re.search(pattern, line):
                    # Extract class name if possible
                    name_match = re.search(r'class\s+(\w+)', content)
                    name = name_match.group(1) if name_match else entry_type

                    entry_point = EntryPoint(file_path, name, entry_type, i + 1)

                    if entry_point not in self.detected_entry_points:
                        self.detected_entry_points.append(entry_point)
                        LOGGER.debug(f'detected {description} at {file_path}:{i+1}')

    def _apply_custom_patterns(self, file_path: str, content: str, patterns: List[str]):
        """Apply custom user-defined patterns for entry point detection."""
        lines = content.split('\n')

        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    entry_point = EntryPoint(file_path, 'custom', 'custom_pattern', i + 1)

                    if entry_point not in self.detected_entry_points:
                        self.detected_entry_points.append(entry_point)
                        LOGGER.debug(f'detected custom pattern at {file_path}:{i+1}')


class PathTracer:
    """Traces dependency paths from entry points through the codebase."""

    def __init__(self, analysis):
        """Initialize the path tracer.

        Args:
            analysis: The Analysis object with graph representations.
        """
        self.analysis = analysis
        self.entry_point_paths: Dict[str, Dict[str, Any]] = {}

    def trace_all_paths(self, entry_points: List[EntryPoint]) -> Dict[str, Dict[str, Any]]:
        """Trace dependency paths from all entry points.

        Args:
            entry_points: List of EntryPoint objects to trace from.

        Returns:
            Dictionary mapping entry point identifiers to path data.
        """
        LOGGER.info_start(f'tracing dependency paths from {len(entry_points)} entry points')

        # Get the dependency graph
        dep_graph_repr = self.analysis.graph_representations.get('file_result_dependency_graph')
        if not dep_graph_repr or not dep_graph_repr.digraph:
            LOGGER.warning('no dependency graph available for path tracing')
            return {}

        graph = dep_graph_repr.digraph

        # Assign colors to entry points if not already assigned
        self._assign_colors(entry_points)

        # Trace paths from each entry point
        for entry_point in entry_points:
            path_id = f"{entry_point.file_path}:{entry_point.name}"

            # Find the entry point node in the graph
            matching_nodes = [n for n in graph.nodes() if entry_point.file_path in n]

            if not matching_nodes:
                LOGGER.debug(f'entry point not found in graph: {entry_point.file_path}')
                continue

            entry_node = matching_nodes[0]

            # Trace all reachable nodes (dependencies) from this entry point
            try:
                import networkx as nx
                reachable_nodes = nx.descendants(graph, entry_node)
                reachable_nodes.add(entry_node)  # Include the entry point itself

                # Get all edges in the subgraph
                edges = []
                for node in reachable_nodes:
                    for successor in graph.successors(node):
                        if successor in reachable_nodes:
                            edges.append({'from': node, 'to': successor})

                self.entry_point_paths[path_id] = {
                    'entry_point': entry_point.file_path,
                    'name': entry_point.name,
                    'label': entry_point.label,
                    'color': entry_point.color,
                    'type': entry_point.type,
                    'nodes': list(reachable_nodes),
                    'edges': edges,
                    'node_count': len(reachable_nodes),
                    'edge_count': len(edges)
                }

                LOGGER.debug(f'traced {len(reachable_nodes)} nodes from {entry_point.name}')

            except Exception as e:
                LOGGER.warning(f'error tracing path from {entry_point.name}: {e}')

        LOGGER.info_done(f'traced {len(self.entry_point_paths)} dependency paths')
        return self.entry_point_paths

    def _assign_colors(self, entry_points: List[EntryPoint]):
        """Assign colors to entry points that don't have colors."""

        # Default color palette
        default_colors = [
            '#FF0000',  # Red
            '#00FF00',  # Green
            '#0000FF',  # Blue
            '#FFA500',  # Orange
            '#800080',  # Purple
            '#FFD700',  # Gold
            '#00CED1',  # Dark Turquoise
            '#FF1493',  # Deep Pink
            '#32CD32',  # Lime Green
            '#FF4500',  # Orange Red
        ]

        color_index = 0
        for entry_point in entry_points:
            if not entry_point.color:
                entry_point.color = default_colors[color_index % len(default_colors)]
                color_index += 1

    def get_node_colors(self) -> Dict[str, List[str]]:
        """Get colors for each node based on which paths it belongs to.

        Returns:
            Dictionary mapping node names to list of colors.
        """
        node_colors: Dict[str, List[str]] = {}

        for path_id, path_data in self.entry_point_paths.items():
            color = path_data['color']
            for node in path_data['nodes']:
                if node not in node_colors:
                    node_colors[node] = []
                if color not in node_colors[node]:
                    node_colors[node].append(color)

        return node_colors
