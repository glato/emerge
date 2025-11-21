# Emerge Enhancement Requirements
**For: Claude Code Web**
**Date: 2024-11-20**
**Project: emerge (https://github.com/glato/emerge)**

---

## Executive Summary

We need to **fork and enhance emerge** with better filtering and visualization capabilities for multi-phase software projects (like our Moderator project with Gear 1, 2, 3 architecture).

**Goal:** Enable emerge to generate clean, focused visualizations by filtering to specific subsets of files based on patterns, directories, or custom criteria.

---

## Current Limitations

### Problem 1: File Exclusion Doesn't Work Well

**Current Config Syntax (Attempted):**
```yaml
file_scan_exclusions:
  - "*/test*"
  - "*/dashboard/*"
  - "*/agents/*"
```

**Result:** Still scans all 66 files (exclusions appear to be ignored or syntax is wrong)

**Expected:** Should exclude directories/files matching patterns

### Problem 2: No Way to Filter to Specific Files Only

**What We Want:**
```yaml
file_scan_inclusions:  # NEW FEATURE
  - "src/orchestrator.py"
  - "src/decomposer.py"
  - "src/executor.py"
  - "src/models.py"
  - "src/state_manager.py"
  - "src/git_manager.py"
  - "src/backend.py"
  - "src/logger.py"
  - "src/main.py"
```

**Current Workaround:** Post-process JSON output with custom Python script

### Problem 3: D3 Visualization Cluttered with Large Codebases

**Issue:** 66 files create unusable hairball diagram
**Need:** Built-in "focus mode" or preset filters

**Example Use Cases:**
- Show only Gear 1 core (9 files)
- Show only agents/ directory
- Show only files with >10 dependencies
- Show only files modified in last 30 days

---

## Proposed Enhancements

### Feature 1: Robust File Filtering (Priority: HIGH)

#### 1A. Inclusion Filters (Whitelist)
```yaml
analyses:
- analysis_name: gear1-core-only
  source_directory: /path/to/project/src

  # NEW: Include ONLY these files
  file_inclusions:
    # Option 1: Explicit file list
    exact_files:
      - "src/orchestrator.py"
      - "src/decomposer.py"
      - "src/executor.py"

    # Option 2: Pattern matching
    patterns:
      - "src/*_manager.py"
      - "src/backend*.py"

    # Option 3: By directory
    directories:
      - "src/core/"
```

#### 1B. Exclusion Filters (Blacklist) - Fix Current Implementation
```yaml
  # FIXED: Make this actually work
  file_exclusions:
    # Exclude directories
    directories:
      - "tests/"
      - "src/dashboard/"
      - "src/agents/"

    # Exclude by pattern
    patterns:
      - "test_*.py"
      - "*_test.py"
      - "*/conftest.py"

    # Exclude specific files
    exact_files:
      - "src/__init__.py"
```

#### 1C. Conditional Filters (Advanced)
```yaml
  # NEW: Filter by metrics
  metric_filters:
    min_sloc: 50           # Only files with >50 lines
    max_sloc: 500          # Only files with <500 lines
    min_fan_out: 5         # Only files with >5 dependencies
    max_fan_in: 20         # Only files imported by <20 others
```

### Feature 2: Preset Filter Profiles (Priority: MEDIUM)

Allow users to define reusable filter profiles:

```yaml
filter_profiles:
  - profile_name: "gear1-core"
    description: "Gear 1 core implementation files"
    include_patterns:
      - "src/orchestrator.py"
      - "src/decomposer.py"
      - "src/executor.py"
      - "src/*_manager.py"
      - "src/backend.py"
      - "src/models.py"
      - "src/logger.py"
      - "src/main.py"

  - profile_name: "agents-only"
    description: "Multi-agent system components"
    include_directories:
      - "src/agents/"

  - profile_name: "high-complexity"
    description: "Files with high coupling"
    metric_filters:
      min_fan_out: 10

# Use profile in analysis
analyses:
- analysis_name: core-analysis
  source_directory: /path/to/src
  apply_filter_profile: "gear1-core"  # NEW
```

### Feature 3: Multiple Analyses in One Run (Priority: MEDIUM)

```yaml
# Run multiple filtered analyses in parallel
analyses:
  - analysis_name: gear1-core
    apply_filter_profile: "gear1-core"
    export:
      - directory: ./emerge-output/gear1/
      - graphml
      - d3

  - analysis_name: agents-system
    apply_filter_profile: "agents-only"
    export:
      - directory: ./emerge-output/agents/
      - graphml
      - d3

  - analysis_name: full-project
    # No filters - analyze everything
    export:
      - directory: ./emerge-output/full/
      - json
```

### Feature 4: Improved D3 Visualization (Priority: LOW-MEDIUM)

#### 4A. Filter Controls in Web UI
Add controls to `emerge.html`:
- [ ] Dropdown: "Show: All Files | Core Only | High Complexity | Custom"
- [ ] Sliders: Min/Max SLOC, Fan-in, Fan-out
- [ ] Search: Filter by filename pattern
- [ ] Checkboxes: Hide tests, Hide __init__, Hide low-complexity

#### 4B. Layout Improvements
- [ ] Better force-directed layout for <20 nodes
- [ ] Hierarchical layout option (layers: entry → core → models)
- [ ] Community-based clustering with clearer boundaries

---

## Implementation Guidance

### Phase 1: Core Filtering (1-2 days)
1. **Fix existing exclusion logic** (file_scan_exclusions)
   - Debug why patterns aren't working
   - Add proper glob matching
   - Add tests

2. **Implement inclusion filters** (file_inclusions)
   - Add YAML schema for new fields
   - Implement exact_files, patterns, directories
   - Add validation and error messages

3. **Add metric-based filtering** (metric_filters)
   - Apply filters after metrics calculation
   - Allow combinations (AND/OR logic)

### Phase 2: Preset Profiles (1 day)
1. Add filter_profiles to YAML schema
2. Implement profile loading and application
3. Create example profiles (include in docs)

### Phase 3: Multiple Analyses (0.5 days)
1. Already supported - just document it better
2. Add validation that output directories don't conflict
3. Add progress reporting for multiple analyses

### Phase 4: UI Improvements (2-3 days - optional)
1. Add filter controls to D3 template
2. Implement client-side filtering (no re-run needed)
3. Add layout options
4. Improve legend and tooltips

---

## Test Cases

### Test 1: Exact File Inclusion
```yaml
file_inclusions:
  exact_files:
    - "src/models.py"
    - "src/orchestrator.py"
```
**Expected:** Only 2 files analyzed, dependency graph shows only links between these

### Test 2: Pattern Inclusion
```yaml
file_inclusions:
  patterns:
    - "src/*_manager.py"
```
**Expected:** Matches state_manager.py, git_manager.py (2 files)

### Test 3: Directory Exclusion
```yaml
file_exclusions:
  directories:
    - "tests/"
    - "src/dashboard/"
```
**Expected:** 0 test files, 0 dashboard files in output

### Test 4: Metric Filter
```yaml
metric_filters:
  min_fan_out: 10
```
**Expected:** Only files with ≥10 dependencies (orchestrator.py, monitor_agent.py, etc.)

### Test 5: Combined Filters
```yaml
file_inclusions:
  directories:
    - "src/core/"
file_exclusions:
  patterns:
    - "*_test.py"
metric_filters:
  max_sloc: 300
```
**Expected:** Core directory files, no tests, <300 lines each

---

## Success Criteria

### Must Have (Blocking)
- ✅ File inclusion filters work (exact_files, patterns, directories)
- ✅ File exclusion filters work correctly (fix current bugs)
- ✅ Metric-based filters work (min/max sloc, fan-in, fan-out)
- ✅ All filters have unit tests
- ✅ Documentation updated with examples
- ✅ Backward compatible (existing configs still work)

### Should Have (Important)
- ✅ Filter profiles (reusable named filters)
- ✅ Clear error messages when filters match 0 files
- ✅ Performance: Filtering happens early (don't parse excluded files)
- ✅ Multiple analyses in one run documented

### Nice to Have (Optional)
- ⭐ D3 UI filter controls
- ⭐ Layout options (hierarchical, community-clustered)
- ⭐ Export filter definitions with results (reproducibility)
- ⭐ CLI flag: --filter-profile <name>

---

## Example: Our Use Case (Moderator Project)

### Config We Want to Write:
```yaml
---
project_name: moderator
loglevel: info

# Define reusable filters
filter_profiles:
  gear1-core:
    description: "Gear 1 implementation (9 core files)"
    include_exact_files:
      - "src/orchestrator.py"
      - "src/decomposer.py"
      - "src/executor.py"
      - "src/state_manager.py"
      - "src/git_manager.py"
      - "src/backend.py"
      - "src/models.py"
      - "src/logger.py"
      - "src/main.py"

  gear2-additions:
    description: "Gear 2 new components"
    include_directories:
      - "src/agents/"
    include_patterns:
      - "src/*pr_reviewer*.py"
      - "src/communication/*.py"

  high-complexity:
    description: "Files with high coupling"
    metric_filters:
      min_fan_out: 8

# Run three analyses
analyses:
  - analysis_name: gear1-clean
    source_directory: /home/thh3/personal/moderator/src
    apply_filter_profile: "gear1-core"
    export:
      - directory: /home/thh3/personal/moderator/emerge-output/gear1/
      - graphml
      - d3
      - json

  - analysis_name: gear2-components
    source_directory: /home/thh3/personal/moderator/src
    apply_filter_profile: "gear2-additions"
    export:
      - directory: /home/thh3/personal/moderator/emerge-output/gear2/
      - graphml
      - d3

  - analysis_name: complexity-hotspots
    source_directory: /home/thh3/personal/moderator/src
    apply_filter_profile: "high-complexity"
    export:
      - directory: /home/thh3/personal/moderator/emerge-output/hotspots/
      - graphml
```

### Expected Output:
```
emerge-output/
├── gear1/
│   ├── emerge.html          # Clean 9-node graph
│   └── emerge-*.graphml     # Only Gear 1 dependencies
├── gear2/
│   ├── emerge.html          # Agent system only
│   └── emerge-*.graphml
└── hotspots/
    ├── emerge.html          # High-coupling files
    └── emerge-*.graphml
```

---

## Repository Information

**Original Repo:** https://github.com/glato/emerge
**Language:** Python
**License:** MIT (fork-friendly)
**Version:** 2.0.7

### Files Likely to Modify:
1. **emerge/analysis.py** - Add filtering logic
2. **emerge/config.py** - Parse new YAML fields
3. **emerge/scanner.py** - Skip excluded files early
4. **emerge/metrics.py** - Apply metric filters
5. **tests/** - Add comprehensive filter tests
6. **docs/** - Update documentation
7. **emerge/templates/d3_template.html** - UI improvements (optional)

---

## Questions for Implementation

1. **Should filters apply before or after parsing?**
   - Before = faster (don't parse excluded files)
   - After = more flexible (can filter by metrics)
   - **Recommendation:** Support both - structural filters before, metric filters after

2. **How to handle empty result sets?**
   - Error out?
   - Warning + create empty output?
   - **Recommendation:** Error with helpful message: "Filters matched 0 files. Check patterns."

3. **Should filters affect dependency resolution?**
   - Show dependencies only within filtered set?
   - Show all dependencies (may point outside filtered set)?
   - **Recommendation:** Make configurable via `show_external_dependencies: true|false`

4. **Backward compatibility strategy?**
   - All new fields optional?
   - Deprecation path for old syntax?
   - **Recommendation:** All optional, existing configs work unchanged

---

## Deliverables

### Code
1. ✅ Forked repository with feature branch
2. ✅ Implementation of filtering features
3. ✅ Unit tests (>80% coverage on new code)
4. ✅ Integration tests with example projects
5. ✅ Updated documentation

### Documentation
1. ✅ README with filtering examples
2. ✅ YAML schema documentation
3. ✅ Migration guide (if syntax changes)
4. ✅ Example filter profiles for common use cases

### Examples
1. ✅ Moderator project config (Gear 1/2/3 filters)
2. ✅ Monorepo example (filter by service)
3. ✅ Test/production separation example

---

## Timeline Estimate

- **Phase 1 (Core Filtering):** 1-2 days
- **Phase 2 (Preset Profiles):** 1 day
- **Phase 3 (Documentation):** 0.5 days
- **Phase 4 (UI Improvements):** 2-3 days (optional)

**Total:** 2.5-3.5 days for essential features, 5-6 days with UI enhancements

---

## Contact & Context

**Project Context:** Building Moderator, a meta-orchestration system for AI code generation with phased "Gear" architecture (Gear 1, 2, 3, 4). Need to visualize each phase's architecture separately without noise from other phases.

**Current Workaround:** Post-processing emerge's JSON output with custom Python scripts to filter and generate clean DOT files.

**Desired End State:** Native emerge support for filtering, enabling clean visualizations directly from `emerge -c config.yaml` without post-processing.

---

**Prepared by:** AI Assistant analyzing Moderator codebase
**For:** Claude Code Web to fork and enhance emerge
**Priority:** High (needed for Gear 2 migration planning)
