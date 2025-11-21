# Instructions for Claude Code Web
**Project:** Fork and Enhance emerge (https://github.com/glato/emerge)

---

## Your Mission

Fork the emerge repository and add robust file filtering capabilities to enable clean, focused visualizations of large codebases.

**Context:** emerge is a great codebase analysis tool (MIT license, 965 GitHub stars), but it lacks good filtering for large projects. Currently, analyzing 66 files creates unusable visualizations. We need to filter to specific subsets (e.g., just 9 core files).

---

## Step-by-Step Instructions

### Step 1: Setup Repository (10 minutes)

**Note:** The repository has already been forked. You're working in an existing fork.

1. **Navigate to the repository root:**
   ```bash
   # The repository should already be checked out
   # If not, CC-Web will clone it automatically
   cd emerge
   ```

2. **Create feature branch:**
   ```bash
   git checkout -b feature/advanced-filtering
   ```

3. **Verify current state:**
   ```bash
   # Check you're in the right repo
   git remote -v
   # Should show the forked emerge repository

   # Check current branch
   git branch
   ```

4. **Install development environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   pip install pytest pytest-cov
   ```

5. **Run existing tests to verify setup:**
   ```bash
   pytest
   ```

   **Expected:** Tests should pass (confirms environment is working)

### Step 2: Understand Current Code (30 minutes)

**Key Files to Read:**

1. **emerge/config.py** or **emerge/configuration.py**
   - Look for YAML parsing
   - Find where `ignore_directories_containing` is processed
   - Understand the Configuration class structure

2. **emerge/analysis.py**
   - Look for file scanning logic
   - Find where files are filtered/excluded
   - Understand how file lists are built

3. **emerge/scanner.py** (if exists)
   - File system traversal
   - Pattern matching for file discovery

4. **Look at example YAML configs** in the repo
   - Understand current configuration schema
   - Find examples of file filtering (if any)

**What to Find:**
- ❓ Where does file exclusion happen? (before or after parsing?)
- ❓ Is there glob pattern matching already? (if so, why doesn't it work?)
- ❓ How is the YAML config validated?

### Step 3: Read the Requirements (10 minutes)

**Carefully read:** `EMERGE_ENHANCEMENT_REQUIREMENTS.md` (included in this directory)

**Focus on:**
- Section: "Current Limitations" (what's broken)
- Section: "Proposed Enhancements" (what to build)
- Section: "Test Cases" (how to validate)
- Section: "Success Criteria" (what's required vs optional)

### Step 4: Implement Phase 1 - Core Filtering (1-2 days)

#### 4A. Fix Existing Exclusion Logic

**Task:** Make `file_exclusions` actually work

1. **Find the bug** - Why do current exclusions not work?
   - Check glob pattern matching
   - Check if filters are applied too late
   - Check if there's a configuration parsing issue

2. **Fix it** with proper glob support:
   ```python
   # Should support:
   - "*/test_*.py"       # Glob pattern
   - "src/dashboard/*"   # Directory glob
   - "tests/"            # Exact directory
   ```

3. **Add validation:**
   - Warn if pattern matches 0 files
   - Error if all files are excluded

#### 4B. Add Inclusion Filters (NEW FEATURE)

**Add to YAML schema:**
```yaml
file_inclusions:
  exact_files:          # List of exact paths
    - "src/models.py"
  patterns:             # Glob patterns
    - "src/*_manager.py"
  directories:          # Include entire directories
    - "src/core/"
```

**Implementation:**
1. Update configuration parsing (config.py)
2. Implement filtering logic (analysis.py)
3. Add early-exit: if inclusions specified, ONLY scan those files
4. Validate: error if inclusions match 0 files

#### 4C. Add Metric Filters (NEW FEATURE)

**Add to YAML schema:**
```yaml
metric_filters:
  min_sloc: 50
  max_sloc: 500
  min_fan_out: 5
  max_fan_in: 20
```

**Implementation:**
1. Apply AFTER metrics calculation
2. Filter file results based on calculated metrics
3. Update dependency graph to remove filtered nodes

### Step 5: Add Tests (Throughout Development)

**For each feature, add tests:**

#### Test: Exact File Inclusion
```python
def test_exact_file_inclusion():
    config = {
        'file_inclusions': {
            'exact_files': ['src/models.py', 'src/orchestrator.py']
        }
    }
    result = run_analysis(config)
    assert len(result.files) == 2
    assert 'src/models.py' in result.files
    assert 'src/orchestrator.py' in result.files
```

#### Test: Pattern Inclusion
```python
def test_pattern_inclusion():
    config = {
        'file_inclusions': {
            'patterns': ['src/*_manager.py']
        }
    }
    result = run_analysis(config)
    # Should match state_manager.py, git_manager.py
    assert all('_manager.py' in f for f in result.files)
```

#### Test: Directory Exclusion
```python
def test_directory_exclusion():
    config = {
        'file_exclusions': {
            'directories': ['tests/', 'src/dashboard/']
        }
    }
    result = run_analysis(config)
    assert all('tests/' not in f for f in result.files)
    assert all('dashboard/' not in f for f in result.files)
```

#### Test: Metric Filter
```python
def test_metric_filter_min_fan_out():
    config = {
        'metric_filters': {
            'min_fan_out': 10
        }
    }
    result = run_analysis(config)
    for file in result.files:
        assert result.get_fan_out(file) >= 10
```

#### Test: Combined Filters
```python
def test_combined_filters():
    config = {
        'file_inclusions': {
            'directories': ['src/core/']
        },
        'file_exclusions': {
            'patterns': ['*_test.py']
        },
        'metric_filters': {
            'max_sloc': 300
        }
    }
    result = run_analysis(config)
    for file in result.files:
        assert file.startswith('src/core/')
        assert not file.endswith('_test.py')
        assert result.get_sloc(file) <= 300
```

**Coverage Target:** >80% on new filtering code

### Step 6: Implement Phase 2 - Filter Profiles (1 day)

**Add to YAML schema:**
```yaml
filter_profiles:
  - profile_name: "gear1-core"
    description: "Gear 1 core files only"
    file_inclusions:
      exact_files:
        - "src/orchestrator.py"
        - "src/models.py"
        # ... etc

analyses:
  - analysis_name: gear1-analysis
    source_directory: /path/to/src
    apply_filter_profile: "gear1-core"  # Reference profile
```

**Implementation:**
1. Parse `filter_profiles` section from YAML
2. Store profiles in Configuration object
3. When `apply_filter_profile` is specified, load that profile's filters
4. Apply filters as if they were specified inline

**Validation:**
- Error if referenced profile doesn't exist
- Error if profile_name is duplicated
- Warn if profile matches 0 files

### Step 7: Update Documentation (0.5 days)

1. **Update README.md:**
   - Add "Advanced Filtering" section
   - Show examples of file_inclusions, file_exclusions, metric_filters
   - Show filter profile example

2. **Create FILTERING.md** (new file):
   - Comprehensive filtering guide
   - All filter types with examples
   - Common use cases:
     - "Analyze only core modules"
     - "Exclude tests and generated code"
     - "Show only high-complexity files"
     - "Multi-phase architecture (Gear 1/2/3)"

3. **Update YAML schema docs:**
   - Document all new fields
   - Show valid values and patterns
   - Provide templates

### Step 8: Create Example Configs (0.5 days)

**Add to `examples/` directory:**

1. **examples/filtering/gear-based-architecture.yaml**
   - Example: Moderator project with Gear 1/2/3 filters
   - Multiple analyses in one config
   - Shows filter profiles

2. **examples/filtering/monorepo-filtering.yaml**
   - Example: Filter by microservice
   - Separate analysis per service

3. **examples/filtering/complexity-analysis.yaml**
   - Example: Metric-based filtering
   - High complexity vs low complexity

4. **examples/filtering/exclude-generated-code.yaml**
   - Example: Exclude build artifacts, tests, migrations

### Step 9: Validate Against Our Use Case

**Test with Moderator config:**

Create this config and verify it works:
```yaml
---
project_name: moderator
loglevel: info

filter_profiles:
  - profile_name: "gear1-core"
    description: "Gear 1 implementation files only"
    file_inclusions:
      exact_files:
        - "src/orchestrator.py"
        - "src/decomposer.py"
        - "src/executor.py"
        - "src/state_manager.py"
        - "src/git_manager.py"
        - "src/backend.py"
        - "src/models.py"
        - "src/logger.py"
        - "src/main.py"

analyses:
  - analysis_name: gear1-clean
    source_directory: /home/thh3/personal/moderator/src
    only_permit_languages:
      - py
    only_permit_file_extensions:
      - .py
    apply_filter_profile: "gear1-core"
    file_scan:
      - dependency_graph
      - fan_in_out
      - source_lines_of_code
    export:
      - directory: /tmp/emerge-test/
      - graphml
      - d3
```

**Run it:**
```bash
emerge -c moderator-test.yaml -v
```

**Verify:**
- ✅ Exactly 9 files scanned (not 66)
- ✅ Dependency graph shows only connections between those 9
- ✅ D3 visualization is clean and readable
- ✅ GraphML export contains only 9 nodes

### Step 10: Commit and Push Changes

1. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: Add advanced file filtering capabilities

   - Add file_inclusions (exact_files, patterns, directories)
   - Fix file_exclusions to properly support glob patterns
   - Add metric_filters (min/max sloc, fan_in, fan_out)
   - Add filter_profiles for reusable filter definitions
   - Add comprehensive tests (>80% coverage)
   - Update documentation with examples
   - Add example configs for common use cases

   Closes #XXX (if there's a relevant issue)"
   ```

2. **Push to the fork:**
   ```bash
   git push origin feature/advanced-filtering
   ```

3. **Verify the push:**
   - Check the repository on GitHub
   - Confirm the new branch exists
   - Verify commits are visible

### Step 11: Prepare Pull Request (For Owner to Submit)

**Note:** The repository owner will create the PR to the original emerge repo.

Create a PR summary file for the owner:

```bash
cat > PR_SUMMARY.md << 'EOF'
## Pull Request: Advanced File Filtering for Emerge

### Summary
Adds robust file filtering capabilities to enable clean, focused
visualizations of large codebases.

### Motivation
Current file exclusion doesn't work reliably, and there's no way to
include only specific files. This makes emerge unusable for large
projects where you want to visualize specific subsystems.

### Changes
- ✅ Fixed file_exclusions (proper glob pattern support)
- ✅ Added file_inclusions (exact_files, patterns, directories)
- ✅ Added metric_filters (min/max sloc, fan_in, fan_out)
- ✅ Added filter_profiles (reusable named filters)
- ✅ Added comprehensive tests (XX% coverage on new code)
- ✅ Updated documentation with examples
- ✅ Added example configurations

### Backward Compatibility
All existing configs work unchanged. New fields are optional.

### Testing
- Unit tests: XX new tests added
- Integration tests: 3 example projects tested
- Tested with Python 3.9, 3.10, 3.11

### Documentation
- README.md updated with filtering examples
- New FILTERING.md comprehensive guide
- Example configs in examples/filtering/

### Example Use Case
This enables analyzing the Moderator project (66 files) by filtering
to just 9 core Gear 1 files, producing clean visualizations instead
of unusable hairball diagrams.

### How to Create the PR
1. Go to: https://github.com/glato/emerge/compare
2. Select: base: `glato/emerge:dev` ← head: `YOUR_USERNAME/emerge:feature/advanced-filtering`
3. Click "Create Pull Request"
4. Paste this summary as the PR description
5. Add before/after screenshots if available
EOF
```

**The PR_SUMMARY.md file is ready for the repository owner to use when creating the pull request.**

---

## Checklist Before Submitting PR

- [ ] All tests pass (`pytest`)
- [ ] Coverage >80% on new code (`pytest --cov`)
- [ ] Linting passes (if emerge has linting)
- [ ] Documentation updated
- [ ] Example configs provided
- [ ] CHANGELOG.md updated (if exists)
- [ ] Backward compatible (existing configs work)
- [ ] Tested with real project (Moderator)

---

## Optional Enhancements (If Time Permits)

### UI Filter Controls (Phase 4)

If you want to go further, add filter controls to the D3 visualization:

**File:** `emerge/templates/d3_template.html`

**Add to HTML:**
```html
<div class="filter-controls">
  <label>Show:</label>
  <select id="filter-preset">
    <option value="all">All Files</option>
    <option value="high-complexity">High Complexity (fan-out > 10)</option>
    <option value="core">Core Only (SLOC > 100)</option>
  </select>

  <label>Min SLOC:</label>
  <input type="range" id="min-sloc" min="0" max="1000" value="0">
  <span id="min-sloc-value">0</span>

  <label>Max SLOC:</label>
  <input type="range" id="max-sloc" min="0" max="1000" value="1000">
  <span id="max-sloc-value">1000</span>
</div>
```

**Add JavaScript filtering:**
```javascript
function applyFilters() {
  const minSloc = parseInt(document.getElementById('min-sloc').value);
  const maxSloc = parseInt(document.getElementById('max-sloc').value);

  // Filter nodes
  const filteredNodes = nodes.filter(node => {
    return node.sloc >= minSloc && node.sloc <= maxSloc;
  });

  // Update visualization
  updateGraph(filteredNodes);
}
```

---

## Tips for Success

### 1. Read the Code First
Don't start coding immediately. Spend 30-60 minutes understanding:
- How configuration is parsed
- Where file scanning happens
- How filters are currently applied
- The testing framework structure

### 2. Start Small
Implement features incrementally:
1. Fix file_exclusions first (builds on existing code)
2. Add file_inclusions (similar pattern)
3. Add metric_filters (requires understanding metrics flow)
4. Add filter_profiles last (combines everything)

### 3. Test as You Go
Don't write all code then test. Write test → implement → verify → repeat.

### 4. Follow Existing Patterns
Look for similar features in the codebase and follow their patterns:
- Configuration parsing
- Error handling
- Logging
- Code style

### 5. Ask for Help if Stuck
If you can't figure out why exclusions don't work after 30 minutes:
- Check GitHub issues for similar problems
- Look at recent commits for filtering-related changes
- Run emerge in debug mode to see what's happening

---

## Expected Timeline

| Phase | Task | Time | Priority |
|-------|------|------|----------|
| 1 | Fork & setup | 15 min | Must |
| 2 | Understand code | 30-60 min | Must |
| 3 | Read requirements | 10 min | Must |
| 4 | Fix file_exclusions | 2-4 hours | Must |
| 5 | Add file_inclusions | 3-5 hours | Must |
| 6 | Add metric_filters | 2-3 hours | Must |
| 7 | Add tests | Throughout | Must |
| 8 | Add filter_profiles | 4-6 hours | Should |
| 9 | Documentation | 2-3 hours | Must |
| 10 | Example configs | 1-2 hours | Should |
| 11 | Validation with Moderator | 1 hour | Must |
| 12 | Create PR | 30 min | Must |
| **Total** | | **2.5-3.5 days** | |
| Optional | UI improvements | 2-3 days | Nice |

---

## Questions?

If you encounter issues:

1. **Configuration not parsing?**
   - Check YAML syntax
   - Look for schema validation code
   - Check for typos in field names

2. **Filters not applying?**
   - Add debug logging to see which files are being filtered
   - Check if filters run before or after parsing
   - Verify glob patterns are correct

3. **Tests failing?**
   - Check if you broke backward compatibility
   - Verify test fixtures exist
   - Run tests individually to isolate failures

4. **Unsure about design decision?**
   - Refer to "Questions for Implementation" section in requirements doc
   - Follow the recommendations provided
   - Prioritize backward compatibility

---

## Success Metrics

You'll know you succeeded when:

1. ✅ Moderator config with 9-file filter works perfectly
2. ✅ All tests pass with >80% coverage
3. ✅ D3 visualization is clean (9 nodes, not 66)
4. ✅ Documentation is clear and comprehensive
5. ✅ PR is accepted by emerge maintainers
6. ✅ Feature is released in next emerge version

**Good luck! This will be a valuable contribution to the emerge project and will help many users who struggle with large codebases.**

---

**Prepared:** 2024-11-20
**For:** Claude Code Web
**Project:** emerge filtering enhancement
**Context:** Moderator project needs clean Gear 1/2/3 visualization
