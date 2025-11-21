# Package for Claude Code Web
**Mission:** Fork and enhance emerge with advanced filtering

---

## What's in This Package

### 📋 1. EMERGE_ENHANCEMENT_REQUIREMENTS.md
**What:** Detailed feature requirements and specifications
**Read this for:**
- Current limitations (what's broken)
- Proposed features (what to build)
- Test cases (how to validate)
- Success criteria (what's required)
- Example configs (what we want to write)

### 📖 2. CLAUDE_WEB_INSTRUCTIONS.md
**What:** Step-by-step implementation guide
**Read this for:**
- Fork and setup instructions
- Implementation phases (what order to build)
- Test requirements (>80% coverage)
- Documentation requirements
- PR submission checklist

### 📊 3. ARCHITECTURE_ANALYSIS.md
**What:** Analysis of our codebase (context for why we need this)
**Read this for:**
- Understanding our use case (Moderator project)
- Why current emerge output is unusable (66-file hairball)
- What clean output looks like (9-file Gear 1 core)

### 🎨 4. Existing Emerge Output (for reference)
- `emerge-file_result_dependency_graph-data.json` - Raw data from emerge
- `emerge-file_result_dependency_graph.graphml` - GraphML with all 123 nodes
- `gear1_core.dot` - Our manual filtering (what we want automated)
- `html/emerge.html` - Cluttered D3 visualization (what we want to fix)

---

## Quick Start for Claude Web

### Step 1: Read the Instructions
Start here: **CLAUDE_WEB_INSTRUCTIONS.md**

Follow steps 1-12 in order.

### Step 2: Read the Requirements
Then read: **EMERGE_ENHANCEMENT_REQUIREMENTS.md**

Pay special attention to:
- "Proposed Enhancements" section
- "Test Cases" section
- "Example: Our Use Case" at the end

### Step 3: Start Working in the Fork

**Note:** The repository has already been forked. You're working in an existing fork.

```bash
# Navigate to the repository (CC-Web should already have it)
cd emerge

# Create feature branch
git checkout -b feature/advanced-filtering

# Install development environment
python -m venv venv
source venv/bin/activate
pip install -e .
pip install pytest pytest-cov

# Verify setup
pytest
```

---

## What You're Building

### Core Features (Must Have)

#### 1. File Inclusions (NEW)
```yaml
file_inclusions:
  exact_files:
    - "src/models.py"
  patterns:
    - "src/*_manager.py"
  directories:
    - "src/core/"
```

#### 2. Fixed File Exclusions (FIX EXISTING)
```yaml
file_exclusions:
  directories:
    - "tests/"
  patterns:
    - "test_*.py"
  exact_files:
    - "src/__init__.py"
```

#### 3. Metric Filters (NEW)
```yaml
metric_filters:
  min_sloc: 50
  max_sloc: 500
  min_fan_out: 5
  max_fan_in: 20
```

#### 4. Filter Profiles (NEW)
```yaml
filter_profiles:
  - profile_name: "gear1-core"
    file_inclusions:
      exact_files:
        - "src/orchestrator.py"
        - "src/models.py"
        # ...

analyses:
  - analysis_name: gear1
    apply_filter_profile: "gear1-core"
```

---

## Success Criteria

You're done when:

✅ **This config works:**
```yaml
---
project_name: moderator
filter_profiles:
  - profile_name: "gear1-core"
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
    apply_filter_profile: "gear1-core"
    export:
      - directory: /tmp/emerge-test/
      - d3
      - graphml
```

✅ **Running emerge produces:**
- Exactly 9 files scanned (not 66)
- Clean D3 visualization (9 nodes, readable)
- GraphML with only 9 nodes + their dependencies

✅ **Tests pass:**
- All existing tests still pass (backward compatible)
- New tests for filtering (>80% coverage)

✅ **Documentation complete:**
- README updated with filtering examples
- New FILTERING.md guide created
- Example configs in examples/filtering/

---

## Timeline

- **Phase 1 (Core Filtering):** 1-2 days
- **Phase 2 (Filter Profiles):** 1 day
- **Phase 3 (Documentation):** 0.5 days

**Total:** 2.5-3.5 days

---

## Questions?

Refer to:
- **CLAUDE_WEB_INSTRUCTIONS.md** - Step-by-step guide
- **EMERGE_ENHANCEMENT_REQUIREMENTS.md** - Feature specifications
- **emerge repo:** https://github.com/glato/emerge

---

## After You're Done

1. Create pull request to glato/emerge
2. Share PR link with us
3. We'll test with Moderator project
4. Help get it merged into emerge

---

**This will be a valuable contribution to emerge and help many users with large codebases!**

Good luck! 🚀
