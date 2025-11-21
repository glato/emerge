"""
Handles visualization layer definitions and node prominence assignments.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import List, Dict, Any, Optional
import logging
import fnmatch
from pathlib import Path

from emerge.log import Logger

LOGGER = Logger(logging.getLogger('layers'))


class LayerDefinition:
    """Represents a visualization layer with its files and prominence."""

    def __init__(self, layer_name: str, prominence: str, color: str,
                 files: Optional[List[str]] = None,
                 patterns: Optional[List[str]] = None,
                 directories: Optional[List[str]] = None):
        """Initialize a layer definition.

        Args:
            layer_name: Name of the layer (e.g., "Gear 1: Core")
            prominence: Prominence level: "high", "medium", "low", or "background"
            color: Hex color code for the layer (e.g., "#FF0000")
            files: Optional list of exact file names
            patterns: Optional list of glob patterns (e.g., "*_manager.py")
            directories: Optional list of directories (matches files within)
        """
        self.layer_name = layer_name
        self.prominence = prominence.lower()
        self.color = color
        self.files = files or []
        self.patterns = patterns or []
        self.directories = directories or []

        # Validate prominence level
        valid_prominence = ['high', 'medium', 'low', 'background']
        if self.prominence not in valid_prominence:
            LOGGER.warning(f'Invalid prominence "{self.prominence}" for layer "{layer_name}". '
                         f'Using "medium". Valid values: {valid_prominence}')
            self.prominence = 'medium'

    def matches_file(self, file_path: str) -> bool:
        """Check if a file belongs to this layer.

        Args:
            file_path: The file path to check

        Returns:
            True if the file matches this layer's criteria
        """
        # Normalize path for comparison
        normalized_path = file_path.replace('\\', '/')
        file_name = Path(file_path).name

        # Check exact file names
        if file_name in self.files or normalized_path in self.files:
            return True

        # Check glob patterns
        for pattern in self.patterns:
            if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(normalized_path, pattern):
                return True

        # Check directories
        for directory in self.directories:
            normalized_dir = directory.replace('\\', '/')
            if normalized_dir in normalized_path:
                return True

        return False


class LayerProcessor:
    """Processes layer definitions and assigns nodes to layers."""

    def __init__(self, analysis):
        """Initialize the layer processor.

        Args:
            analysis: The Analysis object containing configuration
        """
        self.analysis = analysis
        self.layers: List[LayerDefinition] = []

    def process_layers(self) -> Dict[str, Any]:
        """Process layer configuration and assign nodes to layers.

        Returns:
            Dictionary containing:
            - layer_definitions: List of layer metadata
            - node_layer_assignments: Mapping of node_id to layer assignments
            - node_prominence: Mapping of node_id to prominence level
        """
        if not self.analysis.visualization_layers:
            LOGGER.debug('No visualization layers configured')
            return {}

        config = self.analysis.visualization_layers

        # Check if layers are enabled
        if not config.get('enabled', False):
            LOGGER.debug('Visualization layers disabled in config')
            return {}

        # Parse layer definitions
        layer_configs = config.get('layers', [])
        if not layer_configs:
            LOGGER.warning('Visualization layers enabled but no layers defined')
            return {}

        LOGGER.info(f'Processing {len(layer_configs)} visualization layers')

        # Create LayerDefinition objects
        for layer_config in layer_configs:
            layer_name = layer_config.get('name', 'Unnamed Layer')
            prominence = layer_config.get('prominence', 'medium')
            color = layer_config.get('color', '#999999')
            files = layer_config.get('files', [])
            patterns = layer_config.get('patterns', [])
            directories = layer_config.get('directories', [])

            layer_def = LayerDefinition(
                layer_name=layer_name,
                prominence=prominence,
                color=color,
                files=files,
                patterns=patterns,
                directories=directories
            )

            self.layers.append(layer_def)
            LOGGER.debug(f'Added layer: {layer_name} (prominence: {prominence})')

        # Assign nodes to layers
        node_layer_assignments = {}
        node_prominence = {}

        # Get the dependency graph to find all nodes
        graph = self.analysis.graph_representations.get('file_result_dependency_graph')
        if not graph or not graph.digraph:
            LOGGER.warning('No dependency graph available for layer processing')
            return {}

        # Process each node in the graph
        for node in graph.digraph.nodes():
            matching_layers = []
            highest_prominence_level = self._prominence_to_level('background')
            assigned_prominence = 'background'

            # Check which layers this node belongs to
            for layer in self.layers:
                if layer.matches_file(node):
                    matching_layers.append(layer.layer_name)

                    # Track highest prominence (lower level number = higher prominence)
                    node_prominence_level = self._prominence_to_level(layer.prominence)
                    if node_prominence_level < highest_prominence_level:
                        highest_prominence_level = node_prominence_level
                        assigned_prominence = layer.prominence

            # Assign layers and prominence to node
            if matching_layers:
                node_layer_assignments[node] = matching_layers
                node_prominence[node] = assigned_prominence
                LOGGER.debug(f'Node {node}: layers={matching_layers}, prominence={assigned_prominence}')

        # Store results in analysis object
        self.analysis.layer_definitions = [
            {
                'name': layer.layer_name,
                'prominence': layer.prominence,
                'color': layer.color,
                'node_count': sum(1 for layers in node_layer_assignments.values() if layer.layer_name in layers)
            }
            for layer in self.layers
        ]

        self.analysis.node_layer_assignments = node_layer_assignments

        LOGGER.info(f'Assigned {len(node_layer_assignments)} nodes to layers')

        return {
            'layer_definitions': self.analysis.layer_definitions,
            'node_layer_assignments': node_layer_assignments,
            'node_prominence': node_prominence
        }

    @staticmethod
    def _prominence_to_level(prominence: str) -> int:
        """Convert prominence string to numeric level (lower = more prominent).

        Args:
            prominence: Prominence string

        Returns:
            Numeric level (0-3)
        """
        prominence_levels = {
            'high': 0,
            'medium': 1,
            'low': 2,
            'background': 3
        }
        return prominence_levels.get(prominence.lower(), 3)

    @staticmethod
    def get_prominence_opacity(prominence: str) -> float:
        """Get opacity value for a prominence level.

        Args:
            prominence: Prominence string

        Returns:
            Opacity value (0.0-1.0)
        """
        opacity_map = {
            'high': 1.0,
            'medium': 0.8,
            'low': 0.5,
            'background': 0.2
        }
        return opacity_map.get(prominence.lower(), 0.5)

    @staticmethod
    def get_prominence_radius_multiplier(prominence: str) -> float:
        """Get radius multiplier for a prominence level.

        Args:
            prominence: Prominence string

        Returns:
            Radius multiplier (0.5-1.5)
        """
        multiplier_map = {
            'high': 1.5,
            'medium': 1.0,
            'low': 0.75,
            'background': 0.5
        }
        return multiplier_map.get(prominence.lower(), 1.0)
