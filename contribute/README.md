# Advanced File Filtering Contribution

## 📍 You Are Here

This directory contains complete documentation for adding advanced file filtering capabilities to emerge.

**Repository:** `/home/thh3/personal/emerge` (local clone of your fork)
**Branch:** Create `feature/advanced-filtering` (instructions will guide you)
**Timeline:** 2.5-3.5 days implementation

---

## 🚀 Quick Start

### For Claude Code Web:

1. **Start in this directory:**
   ```bash
   cd /home/thh3/personal/emerge
   ```

2. **Read the documentation:**
   - Start with: `contribute/START_HERE.md`
   - Then follow: `contribute/CLAUDE_WEB_INSTRUCTIONS.md`

3. **Create feature branch:**
   ```bash
   git checkout -b feature/advanced-filtering
   ```

4. **Begin implementation** following the 11-step guide

---

## 📚 Documentation Files

### Navigation & Overview
- **INDEX.md** - Directory of all files
- **START_HERE.md** ⭐ - Quick overview and setup

### Implementation Guides
- **CLAUDE_WEB_INSTRUCTIONS.md** 📋 - Complete 11-step implementation guide
- **EMERGE_ENHANCEMENT_REQUIREMENTS.md** 📝 - Detailed feature specifications
- **README_FOR_CLAUDE_WEB.md** - Quick start summary

### Context & Support
- **SETUP_CLARIFICATION.md** - Repository setup explanation
- **ARCHITECTURE_ANALYSIS.md** - Why this is needed

### Reference Files
- **gear1_core.dot** - Example of desired filtered output
- **visualize_gear1_core.py** - Example post-processing script

---

## 🎯 What You're Building

Add these features to emerge:

### 1. File Inclusions (NEW)
```yaml
file_inclusions:
  exact_files:
    - "src/models.py"
  patterns:
    - "src/*_manager.py"
  directories:
    - "src/core/"
```

### 2. Fixed File Exclusions
```yaml
file_exclusions:
  directories:
    - "tests/"
  patterns:
    - "test_*.py"
```

### 3. Metric Filters (NEW)
```yaml
metric_filters:
  min_sloc: 50
  max_sloc: 500
  min_fan_out: 5
```

### 4. Filter Profiles (NEW)
```yaml
filter_profiles:
  - profile_name: "gear1-core"
    file_inclusions:
      exact_files:
        - "src/orchestrator.py"
        # ... more files

analyses:
  - analysis_name: gear1
    apply_filter_profile: "gear1-core"
```

---

## 📋 Reading Order

1. **START_HERE.md** (5 min) - Understand the goal
2. **CLAUDE_WEB_INSTRUCTIONS.md** (20 min) - Complete implementation guide
3. **EMERGE_ENHANCEMENT_REQUIREMENTS.md** (15 min) - Feature details
4. Reference other files as needed

---

## ✅ Success Criteria

You'll know you succeeded when:

1. ✅ Tests pass with >80% coverage on new code
2. ✅ This config works:
   ```yaml
   filter_profiles:
     - profile_name: "test"
       file_inclusions:
         exact_files:
           - "emerge/analysis.py"
           - "emerge/config.py"

   analyses:
     - analysis_name: test
       source_directory: ./emerge
       apply_filter_profile: "test"
   ```
3. ✅ Running emerge produces exactly 2 files in output (not all files)
4. ✅ Documentation is complete
5. ✅ Examples are provided

---

## 🔧 Implementation Timeline

| Day | Tasks |
|-----|-------|
| 1 | Setup, understand code, implement file_inclusions |
| 2 | Fix file_exclusions, add metric_filters, tests |
| 3 | Add filter_profiles, documentation, examples |
| 3.5 | Validation, commit, push |

---

## 📂 Repository Structure

```
/home/thh3/personal/emerge/
├── contribute/              ← You are here
│   ├── README.md           ← This file
│   ├── START_HERE.md
│   ├── CLAUDE_WEB_INSTRUCTIONS.md
│   └── ...
├── emerge/                  ← Source code to modify
│   ├── analysis.py         ← Will modify
│   ├── config.py           ← Will modify
│   └── scanner.py          ← May modify
├── tests/                   ← Will add tests here
├── examples/                ← Will add examples here
└── README.md                ← Will update this

```

---

## 🎓 Key Implementation Files

### Files You'll Modify:
- `emerge/analysis.py` - Add filtering logic
- `emerge/config.py` or `emerge/configuration.py` - Parse YAML filters
- `emerge/scanner.py` - Apply filters during file scan

### Files You'll Create:
- `tests/test_filtering.py` - Comprehensive filter tests
- `FILTERING.md` - New filtering documentation
- `examples/filtering/*.yaml` - Example configurations
- `PR_SUMMARY.md` - Pull request template

### Files You'll Update:
- `README.md` - Add filtering examples
- `CHANGELOG.md` - Document new features (if exists)

---

## 🧪 Testing

Run tests frequently during development:

```bash
# All tests
pytest

# With coverage
pytest --cov=emerge tests/

# Specific test file
pytest tests/test_filtering.py -v

# Fast tests only
pytest -m "not slow"
```

**Coverage Goal:** >80% on new filtering code

---

## 💡 Tips

1. **Read the code first** (30-60 min) before implementing
2. **Start small** - Fix exclusions before adding inclusions
3. **Test as you go** - Don't write all code then test
4. **Follow existing patterns** - Match the codebase style
5. **Ask questions** - Use the documentation when stuck

---

## 📦 After Implementation

### 1. Commit Changes
```bash
git add .
git commit -m "feat: Add advanced file filtering capabilities"
```

### 2. Push to Fork
```bash
git push origin feature/advanced-filtering
```

### 3. Verify on GitHub
- Check branch exists
- Review commits
- Confirm all files present

### 4. Notify Owner
The repository owner will:
- Review your changes
- Test with Moderator project
- Create PR to upstream emerge using `PR_SUMMARY.md`

---

## 🆘 Help

### If Stuck:
1. Check the specific documentation file for that topic
2. Look at existing emerge code for similar patterns
3. Review the requirements document for clarification
4. Check GitHub issues on original emerge repo

### If Tests Fail:
1. Run individual test to isolate: `pytest tests/test_filtering.py::test_name -v`
2. Check if you broke backward compatibility
3. Verify fixtures and test data exist
4. Review error messages carefully

---

## 📞 Summary

**Goal:** Add filtering so emerge can show 9 files instead of 66

**Approach:** Modify emerge source code to support include/exclude filters

**Timeline:** 2.5-3.5 days

**Start:** Read `START_HERE.md`, then follow `CLAUDE_WEB_INSTRUCTIONS.md`

**Success:** Tests pass, features work, documentation complete

---

**Ready? Start with `START_HERE.md` and let's enhance emerge! 🚀**
