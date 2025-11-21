# Advanced File Filtering Guide

This guide explains the advanced file filtering capabilities in emerge, which enable clean, focused visualizations of large codebases.

## Overview

Emerge now supports comprehensive filtering to help you:
- **Include only specific files** you want to analyze
- **Exclude unwanted files** (tests, generated code, etc.)
- **Filter by code metrics** (SLOC, fan-in, fan-out)
- **Reuse filters** across multiple analyses using profiles

## Table of Contents

1. [File Inclusions](#file-inclusions)
2. [File Exclusions](#file-exclusions)
3. [Metric Filters](#metric-filters)
4. [Filter Profiles](#filter-profiles)
5. [Examples](#examples)

---

## File Inclusions

File inclusions let you specify **exactly which files** to analyze. When inclusions are specified, only matching files are included in the analysis.

### Syntax

```yaml
analyses:
  - analysis_name: my-analysis
    source_directory: /path/to/project

    file_inclusions:
      exact_files:          # List of exact file names
        - "models.py"
        - "orchestrator.py"

      patterns:             # Glob patterns
        - "*_manager.py"    # Matches state_manager.py, git_manager.py, etc.
        - "test_*.py"       # Matches test_config.py, test_models.py, etc.

      directories:          # Include entire directories
        - "src/core/"
        - "src/models/"
```

### How It Works

- **exact_files**: Matches files by name (e.g., `"models.py"` matches `src/models.py`, `lib/models.py`, etc.)
- **patterns**: Uses glob patterns for flexible matching
  - `*` matches any characters
  - `?` matches single character
  - `[abc]` matches a, b, or c
- **directories**: Includes all files within specified directories

### Examples

```yaml
# Include only core architecture files
file_inclusions:
  exact_files:
    - "main.py"
    - "config.py"
  directories:
    - "src/core/"

# Include only manager classes
file_inclusions:
  patterns:
    - "*_manager.py"
    - "*_handler.py"
```

---

## File Exclusions

File exclusions let you **filter out unwanted files** from your analysis.

### Syntax

```yaml
analyses:
  - analysis_name: my-analysis
    source_directory: /path/to/project

    file_exclusions:
      exact_files:          # Exact file names to exclude
        - "__init__.py"
        - "setup.py"

      patterns:             # Glob patterns to exclude
        - "test_*.py"       # Exclude all test files
        - "*.pyc"           # Exclude compiled Python files
        - "*_pb2.py"        # Exclude protocol buffer generated files

      directories:          # Exclude entire directories
        - "tests/"
        - "build/"
        - "__pycache__/"
```

### How It Works

- **exact_files**: Excludes files with exact names
- **patterns**: Excludes files matching glob patterns
- **directories**: Excludes all files within specified directories

### Common Use Cases

```yaml
# Exclude all test files and generated code
file_exclusions:
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "*_pb2.py"        # Protocol buffers
    - "*_pb2_grpc.py"   # gRPC generated files
  directories:
    - "tests/"
    - "build/"
    - "dist/"
    - "__pycache__/"

# Exclude initialization and setup files
file_exclusions:
  exact_files:
    - "__init__.py"
    - "setup.py"
    - "conftest.py"
```

---

## Metric Filters

Metric filters allow you to **filter files based on code metrics** calculated by emerge. This is useful for focusing on complex files, highly coupled files, or other metric-based criteria.

### Syntax

```yaml
analyses:
  - analysis_name: my-analysis
    source_directory: /path/to/project

    metric_filters:
      min_sloc: 50          # Minimum source lines of code
      max_sloc: 500         # Maximum source lines of code
      min_fan_in: 2         # Minimum fan-in (files that depend on this)
      max_fan_in: 20        # Maximum fan-in
      min_fan_out: 5        # Minimum fan-out (dependencies)
      max_fan_out: 30       # Maximum fan-out

    file_scan:
      - source_lines_of_code  # Required for SLOC filters
      - fan_in_out            # Required for fan-in/out filters
```

### Important Notes

- Metric filters are applied **after** metrics are calculated
- You must include the corresponding metric in `file_scan`:
  - `source_lines_of_code` for SLOC filters
  - `fan_in_out` for fan-in/out filters
- Filters are combined with AND logic (all conditions must be met)

### Examples

```yaml
# Find complexity hotspots (large files with many dependencies)
metric_filters:
  min_sloc: 200
  min_fan_out: 15

# Find well-isolated modules (small files, few dependencies)
metric_filters:
  max_sloc: 100
  max_fan_out: 5

# Find highly-used utility files
metric_filters:
  min_fan_in: 10
```

---

## Filter Profiles

Filter profiles let you **define reusable filter sets** that can be applied to multiple analyses.

### Syntax

```yaml
# Define profiles at the project level
filter_profiles:
  - profile_name: "core-modules"
    description: "Core application modules"
    file_inclusions:
      directories:
        - "src/core/"
    file_exclusions:
      patterns:
        - "test_*.py"

  - profile_name: "high-complexity"
    description: "Complex files requiring attention"
    metric_filters:
      min_sloc: 200
      min_fan_out: 10

# Apply profiles to analyses
analyses:
  - analysis_name: core-analysis
    source_directory: /path/to/project
    apply_filter_profile: "core-modules"

  - analysis_name: hotspots
    source_directory: /path/to/project
    apply_filter_profile: "high-complexity"
```

### Features

- **Reusability**: Define once, use in multiple analyses
- **Clarity**: Name and describe your filtering strategy
- **Inline overrides**: Can combine profiles with inline filters
- **Validation**: Emerge will error if profile doesn't exist

### Advanced: Combining Profiles with Inline Filters

```yaml
filter_profiles:
  - profile_name: "production-code"
    file_exclusions:
      directories:
        - "tests/"

analyses:
  - analysis_name: complex-production
    apply_filter_profile: "production-code"
    # Inline filters are combined with profile filters
    metric_filters:
      min_sloc: 100
```

---

## Examples

### Example 1: Analyze Only Core Files

```yaml
project_name: my-project
loglevel: info

analyses:
  - analysis_name: core-only
    source_directory: /path/to/project/src
    only_permit_languages:
      - py
    only_permit_file_extensions:
      - .py

    file_inclusions:
      exact_files:
        - "orchestrator.py"
        - "executor.py"
        - "models.py"
      patterns:
        - "*_manager.py"

    file_scan:
      - dependency_graph
      - source_lines_of_code
      - fan_in_out

    export:
      - directory: ./output
      - graphml
      - d3
```

**Result**: Analyzes only 9 specific files instead of all 66 files in the project.

### Example 2: Exclude Tests and Generated Code

```yaml
project_name: my-project
loglevel: info

analyses:
  - analysis_name: production-only
    source_directory: /path/to/project

    file_exclusions:
      patterns:
        - "test_*.py"
        - "*_test.py"
        - "*_pb2.py"      # Protocol buffer generated files
      directories:
        - "tests/"
        - "build/"
        - "__pycache__/"

    file_scan:
      - dependency_graph

    export:
      - directory: ./output
      - d3
```

**Result**: Clean visualization of production code only.

### Example 3: Find Complexity Hotspots

```yaml
project_name: my-project
loglevel: info

analyses:
  - analysis_name: hotspots
    source_directory: /path/to/project/src

    metric_filters:
      min_sloc: 150       # Large files
      min_fan_out: 10     # High coupling

    file_scan:
      - source_lines_of_code
      - fan_in_out
      - dependency_graph

    export:
      - directory: ./output
      - tabular_console
      - graphml
```

**Result**: Shows only complex, highly-coupled files that may need refactoring.

### Example 4: Multi-Phase Architecture Analysis

```yaml
project_name: multi-phase-project
loglevel: info

filter_profiles:
  - profile_name: "phase1-core"
    description: "Phase 1 core implementation"
    file_inclusions:
      exact_files:
        - "orchestrator.py"
        - "executor.py"
        - "models.py"

  - profile_name: "phase2-features"
    description: "Phase 2 feature additions"
    file_inclusions:
      directories:
        - "src/features/"
    file_exclusions:
      patterns:
        - "test_*.py"

analyses:
  - analysis_name: phase1-analysis
    source_directory: /path/to/project
    apply_filter_profile: "phase1-core"
    file_scan:
      - dependency_graph
      - fan_in_out
    export:
      - directory: ./output/phase1
      - d3

  - analysis_name: phase2-analysis
    source_directory: /path/to/project
    apply_filter_profile: "phase2-features"
    file_scan:
      - dependency_graph
      - fan_in_out
    export:
      - directory: ./output/phase2
      - d3
```

**Result**: Separate visualizations for each architectural phase.

---

## Best Practices

### 1. Start Broad, Then Narrow

```yaml
# First: Analyze everything to understand the codebase
# Then: Use filters to focus on specific areas
```

### 2. Use Profiles for Reusability

```yaml
# Define common filters as profiles
filter_profiles:
  - profile_name: "no-tests"
    file_exclusions:
      patterns: ["test_*.py", "*_test.py"]
      directories: ["tests/"]

# Reuse across analyses
```

### 3. Combine Filters for Precision

```yaml
# Use inclusions + exclusions + metrics together
file_inclusions:
  directories: ["src/"]
file_exclusions:
  patterns: ["test_*.py"]
metric_filters:
  min_sloc: 50
```

### 4. Document Your Filters

```yaml
filter_profiles:
  - profile_name: "production-core"
    description: "Core production code excluding tests, builds, and small files"
    # Clear description helps others understand filtering strategy
```

---

## Troubleshooting

### No Files Match Filters

**Problem**: Analysis produces empty results

**Solution**:
- Check file paths are relative to `source_directory`
- Verify glob patterns are correct
- Use `loglevel: debug` to see which files are being filtered
- Ensure metric filters don't exclude all files

### Profile Not Found

**Error**: `filter profile "profile-name" not found`

**Solution**:
- Check `profile_name` matches exactly (case-sensitive)
- Ensure profile is defined under `filter_profiles` at project level
- Verify YAML indentation is correct

### Metrics Not Available

**Problem**: Metric filters don't work

**Solution**:
- Add required metrics to `file_scan`:
  - `source_lines_of_code` for SLOC filters
  - `fan_in_out` for fan-in/out filters
- Metric filters are applied **after** metrics are calculated

---

## Migration from Old Filtering

### Old Way

```yaml
# Limited functionality, substring matching only
ignore_directories_containing:
  - tests
  - __pycache__

ignore_files_containing:
  - test
```

### New Way

```yaml
# More powerful, glob patterns, multiple filter types
file_exclusions:
  directories:
    - "tests/"
    - "__pycache__/"
  patterns:
    - "test_*.py"
    - "*_test.py"
```

**Note**: Old filtering syntax still works for backward compatibility.

---

## See Also

- Example configurations in `emerge/configs/filtering-example-*.yaml`
- Original emerge documentation for general usage
- GitHub issues for feature requests and bug reports

---

**Need help?** Check the example configurations or open an issue on GitHub!

---

## Path Analysis and Highlighting

Path analysis is a powerful feature that lets you visualize dependency paths from different entry points in your codebase. This is especially useful for understanding code flow, identifying which files are used by different features, and visualizing multi-layered architectures.

### What is Path Analysis?

Path analysis:
1. **Detects or specifies entry points** in your code (main functions, CLI commands, API routes, etc.)
2. **Traces all dependencies** from each entry point through the codebase
3. **Assigns colors** to each path for visual distinction
4. **Highlights overlapping nodes** that are shared between multiple paths
5. **Provides interactive controls** to toggle paths on/off in the visualization

### Configuration

```yaml
analyses:
  - analysis_name: my-analysis
    source_directory: /path/to/project

    path_analysis:
      enabled: true

      # Auto-detect entry points (optional)
      detect_entry_points:
        enabled: true
        patterns:           # Custom patterns (optional)
          - "if __name__ == '__main__'"
          - "@app.route"

      # Manual entry points (optional)
      entry_points:
        - file: "main.py"
          function: "main"
          label: "Main Application"
          color: "#FF0000"

        - file: "cli.py"
          function: "cli"
          label: "CLI Tool"
          color: "#00FF00"
```

### Auto-Detection

Path analysis can automatically detect entry points in various languages:

#### Python:
- `if __name__ == "__main__"` blocks
- `def main()` functions
- Flask routes: `@app.route()`
- FastAPI routes: `@app.get()`, `@app.post()`
- Click CLI: `@click.command()`, `@click.group()`
- Argparse: `ArgumentParser` instances

#### JavaScript/TypeScript:
- Express routes: `app.get()`, `app.post()`
- `export default function` declarations
- `if (require.main === module)` blocks

#### Java:
- `public static void main()` methods
- `@SpringBootApplication` classes
- `@RestController` classes

### Manual Entry Points

For precise control, specify entry points manually:

```yaml
entry_points:
  - file: "orchestrator.py"
    function: "main"
    label: "Core Orchestrator"
    color: "#FF0000"

  - file: "worker.py"
    function: "process"
    label: "Background Worker"
    color: "#00FF00"
```

**Fields:**
- `file`: Relative path to the file
- `function`: Function/method name (or `"main"` for general entry)
- `label`: Display label in the visualization
- `color`: Hex color code for the path

### Visualization

When you export to D3, path analysis adds:

1. **Path Toggle Controls**: Button to show/hide path controls
2. **Individual Path Checkboxes**: Toggle each entry point path independently
3. **"All Paths" Toggle**: Show/hide all paths at once
4. **Color-Coded Nodes**:
   - Nodes in a single path: Solid color
   - Nodes in multiple paths: Multiple colors (gradient/border)
   - Nodes not in any path: Dimmed/gray

5. **Interactive Features**:
   - Click checkboxes to toggle paths
   - See node count for each path
   - Identify shared dependencies by color mixing

### Use Cases

#### 1. Multi-Entry Application

```yaml
# Web app with both UI and API
entry_points:
  - file: "web/server.py"
    function: "create_app"
    label: "Web UI"
    color: "#FF0000"

  - file: "api/server.py"
    function: "create_api"
    label: "REST API"
    color: "#0000FF"
```

**Result**: See which files are shared between UI and API, which are UI-specific, which are API-specific.

#### 2. Microservices Architecture

```yaml
entry_points:
  - file: "services/auth/main.py"
    label: "Auth Service"
    color: "#FF0000"

  - file: "services/users/main.py"
    label: "User Service"
    color: "#00FF00"

  - file: "services/orders/main.py"
    label: "Order Service"
    color: "#0000FF"
```

**Result**: Visualize dependencies for each microservice, identify shared libraries.

#### 3. Layered Architecture (Gear 1/2/3)

```yaml
# Moderator project example
entry_points:
  - file: "orchestrator.py"
    function: "main"
    label: "Gear 1: Orchestration"
    color: "#FF0000"

  - file: "agents/monitor_agent.py"
    function: "run"
    label: "Gear 2: Monitor Agent"
    color: "#00FF00"

  - file: "agents/pr_reviewer.py"
    function: "review"
    label: "Gear 2: PR Reviewer"
    color: "#0000FF"

  - file: "utils/state_manager.py"
    function: "load_state"
    label: "Gear 3: Utilities"
    color: "#FFA500"
```

**Result**: See which files belong to each architectural layer, identify cross-layer dependencies.

#### 4. Feature Analysis

```yaml
# E-commerce platform
entry_points:
  - file: "features/checkout/flow.py"
    label: "Checkout Feature"
    color: "#FF0000"

  - file: "features/search/engine.py"
    label: "Search Feature"
    color: "#00FF00"

  - file: "features/recommendations/algorithm.py"
    label: "Recommendations Feature"
    color: "#0000FF"
```

**Result**: Understand which files each feature depends on, identify shared components.

### Combining with Filters

Path analysis works seamlessly with other filters:

```yaml
analyses:
  - analysis_name: core-paths-only
    source_directory: /path/to/project

    # Filter to core files only
    file_inclusions:
      directories:
        - "src/core/"

    # Then trace paths from entry points
    path_analysis:
      enabled: true
      entry_points:
        - file: "src/core/main.py"
          label: "Core Entry"
          color: "#FF0000"

    file_scan:
      - dependency_graph

    export:
      - d3
```

### Overlapping Paths

When a file is used by multiple entry points, it will show multiple colors:

**Visual Indicators:**
- **Border Color**: Shows secondary path color
- **Thicker Border**: Indicates node is in multiple paths
- **Opacity**: Active paths at 100%, inactive paths at 30%

**Example:**
- `models.py` used by both "Main App" (red) and "CLI Tool" (green)
- Shows red fill with green border
- Tooltip shows: "Part of 2 paths: Main App, CLI Tool"

### Best Practices

1. **Use Descriptive Labels**: Make path purposes clear
   ```yaml
   label: "User Authentication Flow"  # Good
   label: "Path 1"                     # Bad
   ```

2. **Choose Distinct Colors**: Ensure paths are easily distinguishable
   ```yaml
   # Good color palette
   colors: ["#FF0000", "#00FF00", "#0000FF", "#FFA500", "#800080"]
   ```

3. **Limit Number of Paths**: Too many paths (>10) can be confusing
   - For large projects, create separate analyses for different subsystems

4. **Combine with Filtering**: Use filters to focus on specific areas first
   ```yaml
   file_inclusions:
     directories: ["src/"]  # Focus on source only
   path_analysis:
     entry_points: [...]     # Then trace from entry points
   ```

5. **Document Your Paths**: Add comments explaining each entry point
   ```yaml
   entry_points:
     # Main web application entry - serves HTTP requests
     - file: "main.py"
       label: "Web App"
       color: "#FF0000"
   ```

### Troubleshooting

**No entry points detected:**
- Check that auto-detection patterns match your code
- Try manual entry point specification
- Verify file paths are correct relative to `source_directory`

**Paths not showing in visualization:**
- Ensure `dependency_graph` is in `file_scan`
- Check that D3 export is enabled
- Verify entry point files exist in the analyzed codebase

**All nodes showing same color:**
- Check that multiple entry points are defined
- Verify entry points lead to different files
- Ensure path analysis is enabled

**Too many overlapping paths:**
- Reduce number of entry points
- Use file_inclusions to focus on specific areas
- Create separate analyses for different subsystems

---

## Complete Example: Path Analysis + Filtering

Here's a complete example combining filtering and path analysis:

```yaml
project_name: advanced-analysis-example
loglevel: info

# Define reusable filters
filter_profiles:
  - profile_name: "production-code"
    file_exclusions:
      directories: ["tests/", "build/"]
      patterns: ["test_*.py", "*.pyc"]

# Analysis with both filtering and path tracing
analyses:
  - analysis_name: feature-paths
    source_directory: /path/to/project

    # Apply production code filter
    apply_filter_profile: "production-code"

    # Additional filters
    file_inclusions:
      directories:
        - "src/features/"
        - "src/core/"

    metric_filters:
      min_sloc: 50  # Exclude very small files

    # Trace paths from feature entry points
    path_analysis:
      enabled: true
      entry_points:
        - file: "src/features/auth/login.py"
          function: "handle_login"
          label: "Authentication"
          color: "#FF0000"

        - file: "src/features/payments/processor.py"
          function: "process_payment"
          label: "Payment Processing"
          color: "#00FF00"

        - file: "src/features/notifications/sender.py"
          function: "send_notification"
          label: "Notifications"
          color: "#0000FF"

    file_scan:
      - dependency_graph
      - source_lines_of_code
      - fan_in_out

    export:
      - directory: ./output
      - d3  # Interactive visualization with path controls
      - json  # Data for further analysis
```

**This configuration:**
1. Excludes tests and build artifacts (filter profile)
2. Includes only src/features/ and src/core/ directories
3. Filters out files smaller than 50 lines
4. Traces 3 different paths from feature entry points
5. Creates interactive D3 visualization with path toggle controls

---


## 5. Visualization Layers

Visualization layers provide a powerful way to add visual hierarchy and prominence levels to your dependency graphs. By organizing files into layers with different prominence levels, you can create clear visual representations of your architecture without changing the underlying data.

### Why Visualization Layers?

**Problem:** Large codebases have architectural layers (core, services, utilities) but all files look the same in visualizations.

**Solution:** Assign files to layers with prominence levels. High-prominence files (core architecture) are large and opaque, while low-prominence files (utilities) are smaller and dimmer.

**Key Benefits:**
- Immediate visual understanding of architecture
- Focus on what matters by toggling layers
- Multiple visualization perspectives of the same data
- No impact on metadata collection - purely visualization

### 5.1 Basic Layer Configuration

Layers are defined in the `visualization_layers` section of your analysis configuration:

```yaml
analyses:
  - analysis_name: my-analysis
    source_directory: /path/to/src

    visualization_layers:
      enabled: true
      layers:
        - name: "Core Layer"
          prominence: "high"
          color: "#FF0000"
          files:
            - "main.py"
            - "app.py"

        - name: "Business Logic"
          prominence: "medium"
          color: "#00FF00"
          directories:
            - "services"

        - name: "Utilities"
          prominence: "low"
          color: "#0000FF"
          patterns:
            - "*_utils.py"
```

### 5.2 Layer Properties

#### required: `name`
- **Type:** String
- **Description:** Display name for the layer
- **Example:** `"Gear 1: Core Orchestration"`

#### required: `prominence`
- **Type:** String
- **Values:** `high`, `medium`, `low`, `background`
- **Description:** Visual prominence level
- **Effects:**
  - **high:** Opacity 1.0, Radius 1.5x (largest, fully visible)
  - **medium:** Opacity 0.8, Radius 1.0x (normal size, slightly dimmed)
  - **low:** Opacity 0.5, Radius 0.75x (smaller, half visible)
  - **background:** Opacity 0.2, Radius 0.5x (smallest, barely visible)

#### required: `color`
- **Type:** Hex color code
- **Description:** Color used for layer visualization
- **Example:** `"#FF0000"` (red)

#### optional: `files`
- **Type:** List of strings
- **Description:** Exact file names to include in this layer
- **Matching:** Matches against file basename or full path
- **Example:**
```yaml
files:
  - "main.py"
  - "src/core/orchestrator.py"
```

#### optional: `patterns`
- **Type:** List of glob patterns
- **Description:** File patterns to match
- **Matching:** Uses fnmatch (shell-style wildcards)
- **Example:**
```yaml
patterns:
  - "*_agent.py"
  - "test_*.py"
  - "*_manager.py"
```

#### optional: `directories`
- **Type:** List of directory paths
- **Description:** Include all files within these directories
- **Matching:** Matches if directory path is contained in file path
- **Example:**
```yaml
directories:
  - "agents"
  - "src/services"
```

### 5.3 Prominence Levels Explained

Prominence creates visual hierarchy without changing the data:

```
HIGH (1.0 opacity, 1.5x radius)
├── Core orchestration files
├── Main entry points
└── Critical business logic

MEDIUM (0.8 opacity, 1.0x radius)
├── Business services
├── API endpoints
└── Domain models

LOW (0.5 opacity, 0.75x radius)
├── Utilities
├── Helpers
└── Common functions

BACKGROUND (0.2 opacity, 0.5x radius)
├── Configuration
├── Constants
└── Build files
```

Files not assigned to any layer default to **background** prominence.

### 5.4 Layer Matching Rules

A file can belong to **multiple layers**. When this occurs:
1. File is shown in all matching layers
2. Visual prominence uses the **highest** (most prominent) level
3. Color indicates multiple layer membership (thicker borders)

**Example:** A file matching both "Core" (high) and "Services" (medium) will display with **high** prominence.

### 5.5 Interactive Layer Controls

The D3 visualization provides interactive layer controls:

**Toggle Individual Layers:**
- Click checkboxes to show/hide specific layers
- See immediately which files belong to each layer
- Focus on specific architectural concerns

**Toggle All Layers:**
- Master switch to show/hide all layers
- Useful for comparing layered vs. unlayered views

**Visual Indicators:**
- Color swatch shows layer color
- Symbol indicates prominence (★ high, ◆ medium, ○ low, · background)
- Node count shows layer size

### 5.6 Complete Examples

#### Example 1: Simple Three-Layer Architecture

```yaml
---
project_name: simple-layers
loglevel: info

analyses:
  - analysis_name: three-layers
    source_directory: /path/to/src

    visualization_layers:
      enabled: true
      layers:
        # Core application (most prominent)
        - name: "Core"
          prominence: "high"
          color: "#FF0000"
          files:
            - "main.py"
            - "app.py"

        # Business logic (medium prominence)
        - name: "Services"
          prominence: "medium"
          color: "#00FF00"
          directories:
            - "services"
            - "controllers"

        # Utilities (low prominence)
        - name: "Utils"
          prominence: "low"
          color: "#0000FF"
          patterns:
            - "*_utils.py"
            - "*_helper.py"

    file_scan:
      - dependency_graph
      - fan_in_out

    export:
      - directory: ./output
      - d3
```

**Result:** Clear three-tier visualization where core files are immediately obvious, services are clearly visible, and utilities fade into the background.

#### Example 2: Gear 1/2/3 Architecture

```yaml
---
project_name: gear-architecture
loglevel: info

analyses:
  - analysis_name: gears
    source_directory: /path/to/src

    visualization_layers:
      enabled: true
      layers:
        # Gear 1: Core orchestration
        - name: "Gear 1: Orchestration"
          prominence: "high"
          color: "#FF0000"
          files:
            - "orchestrator.py"
            - "main.py"
          directories:
            - "core"

        # Gear 2: Agent execution
        - name: "Gear 2: Agents"
          prominence: "medium"
          color: "#00AA00"
          patterns:
            - "*_agent.py"
            - "*_executor.py"
          directories:
            - "agents"

        # Gear 3: Support services
        - name: "Gear 3: Services"
          prominence: "medium"
          color: "#0066FF"
          patterns:
            - "*_service.py"
            - "*_manager.py"
          directories:
            - "services"

        # Infrastructure
        - name: "Infrastructure"
          prominence: "low"
          color: "#FFA500"
          directories:
            - "infrastructure"
            - "config"

    file_scan:
      - dependency_graph
      - source_lines_of_code
      - fan_in_out

    export:
      - directory: ./output
      - d3
```

**Result:** Multi-gear architecture visualization where:
- Gear 1 (red) dominates: Core orchestration is immediately visible
- Gear 2 (green) is prominent: Agents are clearly important
- Gear 3 (blue) is visible: Services support the agents
- Infrastructure (orange) fades: Background support

**Use Cases:**
- Architecture review: Verify gear separation
- Onboarding: Show new developers the architecture layers
- Code review: Focus on high-prominence changes

#### Example 3: Microservices with Shared Libraries

```yaml
---
project_name: microservices
loglevel: info

analyses:
  - analysis_name: services
    source_directory: /path/to/services

    visualization_layers:
      enabled: true
      layers:
        # API Gateway (entry point)
        - name: "API Gateway"
          prominence: "high"
          color: "#FF0000"
          directories:
            - "api-gateway"

        # Business services
        - name: "User Service"
          prominence: "high"
          color: "#2196F3"
          directories:
            - "services/user-service"

        - name: "Order Service"
          prominence: "high"
          color: "#4CAF50"
          directories:
            - "services/order-service"

        - name: "Payment Service"
          prominence: "high"
          color: "#FF9800"
          directories:
            - "services/payment-service"

        # Shared libraries (lower prominence)
        - name: "Shared: Common"
          prominence: "low"
          color: "#607D8B"
          directories:
            - "shared/common"

        - name: "Shared: Auth"
          prominence: "low"
          color: "#795548"
          directories:
            - "shared/auth"

    file_scan:
      - dependency_graph
      - fan_in_out
      - louvain_modularity

    export:
      - directory: ./output
      - d3
      - graphml
```

**Result:** Service-oriented visualization showing:
- Services as distinct, prominent colored clusters
- Shared libraries as smaller, dimmer nodes
- Clear service boundaries and dependencies

**Analysis:**
- Toggle individual services to see their dependencies
- Toggle shared libraries to see cross-service coupling
- Identify services with excessive dependencies

### 5.7 Combining Layers with Other Features

Visualization layers work seamlessly with other emerge features:

#### Layers + Path Analysis

```yaml
visualization_layers:
  enabled: true
  layers:
    - name: "Core"
      prominence: "high"
      color: "#FF0000"
      files: ["main.py"]

path_analysis:
  enabled: true
  entry_points:
    - file: "main.py"
      function: "main"
      label: "Main Entry"
      color: "#00FF00"
```

**Result:** Path highlighting shows which layers are used by each entry point. High-prominence layers are immediately visible in traced paths.

#### Layers + File Filtering

```yaml
file_inclusions:
  directories:
    - "src"

file_exclusions:
  patterns:
    - "test_*.py"

visualization_layers:
  enabled: true
  layers:
    - name: "Core"
      prominence: "high"
      files: ["main.py"]
```

**Result:** Filters reduce the graph to relevant files, then layers add visual hierarchy to what remains.

#### Layers + Metric Filters

```yaml
metric_filters:
  min_sloc: 50
  min_fan_in: 2

visualization_layers:
  enabled: true
  layers:
    - name: "Core"
      prominence: "high"
      directories: ["core"]
```

**Result:** Metric filters show only significant files, layers highlight their architectural importance.

### 5.8 Best Practices

#### 1. Use Prominence Hierarchy Meaningfully

**Good:**
```yaml
- name: "Core Orchestration"
  prominence: "high"  # 1-2 files, controls everything

- name: "Business Logic"
  prominence: "medium"  # 10-20 files, core features

- name: "Utilities"
  prominence: "low"  # 50+ files, helpers
```

**Avoid:**
```yaml
- name: "Random Files"
  prominence: "high"  # 100 files - defeats the purpose
```

**Guideline:** High prominence should be **rare** (< 5% of files). If everything is high prominence, nothing stands out.

#### 2. Use Descriptive Layer Names

**Good:**
- "Gear 1: Core Orchestration"
- "API Layer"
- "Data Models"

**Avoid:**
- "Layer 1"
- "Important Files"
- "Stuff"

#### 3. Choose Distinct Colors

Use colors that are visually distinct:
- `#FF0000` (red)
- `#00AA00` (green)
- `#0066FF` (blue)
- `#FF9800` (orange)
- `#9C27B0` (purple)

Avoid similar shades that are hard to distinguish.

#### 4. Layer Granularity

**For small projects (< 50 files):**
- 2-3 layers maximum
- Broad categories

**For medium projects (50-200 files):**
- 3-5 layers
- Architectural tiers

**For large projects (> 200 files):**
- 5-8 layers
- Subsystem-based layers

**Avoid:** Too many layers (> 10) makes toggles overwhelming.

#### 5. Test Your Layers

After defining layers:
1. Run analysis: `emerge -c config.yaml`
2. Open D3 visualization
3. Toggle layers individually
4. Verify files are in expected layers
5. Check that prominence makes visual sense

### 5.9 Troubleshooting

#### Problem: Layers don't appear in visualization

**Cause:** Layers not enabled or no nodes assigned

**Solution:**
```yaml
visualization_layers:
  enabled: true  # Must be true
  layers:
    - name: "Test"
      prominence: "high"
      color: "#FF0000"
      files: ["existing_file.py"]  # Verify file exists in results
```

#### Problem: Wrong files in layer

**Cause:** Pattern matching too broad or directory path incorrect

**Debug:**
- Check exact file paths in JSON export
- Test patterns: `*_agent.py` matches `test_agent.py`, `user_agent.py`, etc.
- Verify directory paths are relative to source_directory

**Example:**
```yaml
source_directory: /project/src
layers:
  - directories:
      - "services"  # Matches /project/src/services/...
```

#### Problem: All nodes same size despite prominence

**Cause:** Layer visualization not initialized

**Check:**
1. Browser console for JavaScript errors
2. Verify `emerge_layers.js` is loaded
3. Check that `visualization_layers` variable is defined

#### Problem: Node belongs to multiple layers - which prominence?

**Answer:** Highest prominence wins.

**Example:**
- File matches "Core" (high) and "Utils" (low)
- Displayed with **high** prominence
- Shows multiple colors (thicker border with second color)

### 5.10 Advanced Patterns

#### Pattern 1: Focus Mode

Create a "focus" layer for current work:

```yaml
layers:
  - name: "Current Focus"
    prominence: "high"
    color: "#FF0000"
    files:
      - "feature/authentication.py"
      - "feature/login.py"

  - name: "Everything Else"
    prominence: "background"
    patterns:
      - "*.py"
```

Toggle off "Everything Else" to see only focus files and their immediate dependencies.

#### Pattern 2: Risk-Based Layers

Highlight files by change risk:

```yaml
layers:
  - name: "High Risk"
    prominence: "high"
    color: "#FF0000"
    files:
      - "payment_processor.py"
      - "auth_handler.py"

  - name: "Medium Risk"
    prominence: "medium"
    color: "#FFA500"
    directories:
      - "api"

  - name: "Low Risk"
    prominence: "low"
    color: "#00AA00"
    patterns:
      - "*_utils.py"
```

#### Pattern 3: Team Ownership

Visualize code ownership:

```yaml
layers:
  - name: "Team Alpha"
    prominence: "high"
    color: "#2196F3"
    directories:
      - "features/alpha"

  - name: "Team Beta"
    prominence: "high"
    color: "#4CAF50"
    directories:
      - "features/beta"

  - name: "Shared"
    prominence: "medium"
    color: "#FF9800"
    directories:
      - "shared"
```

### 5.11 Example: Full-Stack Application

Complete example combining all visualization features:

```yaml
---
project_name: fullstack-app
loglevel: info

analyses:
  - analysis_name: app-architecture
    source_directory: /path/to/app/src

    # Filter to relevant code
    file_exclusions:
      patterns:
        - "test_*.py"
        - "*.test.js"

    # Define architectural layers
    visualization_layers:
      enabled: true
      layers:
        - name: "Frontend: Core"
          prominence: "high"
          color: "#FF1744"
          files:
            - "frontend/App.jsx"
            - "frontend/index.js"

        - name: "Frontend: Components"
          prominence: "medium"
          color: "#E91E63"
          directories:
            - "frontend/components"

        - name: "Backend: API"
          prominence: "high"
          color: "#2196F3"
          directories:
            - "backend/api"

        - name: "Backend: Business Logic"
          prominence: "medium"
          color: "#3F51B5"
          directories:
            - "backend/services"

        - name: "Backend: Data"
          prominence: "medium"
          color: "#009688"
          directories:
            - "backend/models"

        - name: "Shared"
          prominence: "low"
          color: "#FF9800"
          directories:
            - "shared"

    # Trace request flows
    path_analysis:
      enabled: true
      detect_entry_points:
        enabled: true

    file_scan:
      - dependency_graph
      - source_lines_of_code
      - fan_in_out

    export:
      - directory: ./output
      - d3
```

**Result:** Comprehensive visualization showing:
- Clear frontend/backend separation
- Visual hierarchy within each tier
- Request flow paths through layers
- Interactive layer and path toggles

---

## 6. Combining All Features

### 6.1 The Power of Multiple Perspectives

Emerge's filtering and visualization features provide multiple ways to view the same codebase:

1. **File Filtering:** What code to analyze
2. **Metric Filtering:** Which files meet significance thresholds
3. **Path Analysis:** How code execution flows
4. **Visualization Layers:** What architectural role each file plays

### 6.2 Complete Workflow Example

```yaml
---
project_name: production-analysis
loglevel: info

# Reusable filters
filter_profiles:
  - profile_name: "production-only"
    file_exclusions:
      patterns:
        - "test_*.py"
        - "*_mock.py"
      directories:
        - "tests"
        - "mocks"

analyses:
  - analysis_name: full-analysis
    source_directory: /path/to/src

    # Step 1: Filter to relevant code
    apply_filter_profile: "production-only"

    file_inclusions:
      directories:
        - "core"
        - "features"

    # Step 2: Focus on significant files
    metric_filters:
      min_sloc: 50
      min_fan_in: 2

    # Step 3: Define visual hierarchy
    visualization_layers:
      enabled: true
      layers:
        - name: "Core"
          prominence: "high"
          color: "#FF0000"
          directories: ["core"]

        - name: "Features"
          prominence: "medium"
          color: "#00FF00"
          directories: ["features"]

        - name: "Utils"
          prominence: "low"
          color: "#0000FF"
          patterns: ["*_utils.py"]

    # Step 4: Trace execution paths
    path_analysis:
      enabled: true
      detect_entry_points:
        enabled: true

    file_scan:
      - dependency_graph
      - source_lines_of_code
      - fan_in_out

    export:
      - directory: ./output
      - d3
      - json
```

**This configuration creates:**
1. Clean dataset (filtered to production code)
2. Focused view (only significant files)
3. Visual hierarchy (layers show architecture)
4. Flow visualization (paths show execution)

### 6.3 Interactive Exploration

The D3 visualization provides multiple exploration modes:

**Focus on Architecture:**
1. Toggle off all layers except "Core"
2. See the architectural foundation
3. Gradually enable more layers

**Focus on Features:**
1. Toggle a specific entry point path
2. Enable relevant layers
3. See feature implementation across layers

**Find Problem Areas:**
1. Enable all layers
2. Look for unexpected connections
3. High-prominence files shouldn't depend on low-prominence

---

This completes the comprehensive guide to emerge's advanced filtering and visualization features!
