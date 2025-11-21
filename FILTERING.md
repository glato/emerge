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

