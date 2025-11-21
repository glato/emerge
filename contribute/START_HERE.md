# 🚀 START HERE - Claude Code Web Instructions

## Quick Summary

You have **forked emerge** and need **Claude Code Web** to add advanced filtering features to it.

---

## What's the Goal?

**Currently:** emerge analyzes 66 files → creates unusable hairball visualization

**Goal:** emerge filters to 9 core files → creates clean, focused visualization

**Solution:** Add filtering features to emerge (the tool itself)

---

## Repository Setup

### ✅ You Already Did This:
- Forked https://github.com/glato/emerge
- Created documentation package in moderator/emerge-output/

### ⚠️ Important: Two Separate Repositories

**Repository 1: Moderator** (your project)
- Location: `/home/thh3/personal/moderator/`
- Contains: Documentation for CC-Web
- **CC-Web does NOT modify this**

**Repository 2: Emerge Fork** (the tool)
- Location: Wherever you forked emerge to
- URL: `https://github.com/YOUR_USERNAME/emerge`
- **CC-Web WILL modify this**

---

## How to Use Claude Code Web

### Step 1: Start CC-Web in Your Emerge Fork

When starting a Claude Code Web session:
- **Repository:** Your emerge fork URL
- **Branch:** Will create `feature/advanced-filtering`

### Step 2: Provide Documentation

Upload these 3 files from moderator/emerge-output/:
1. `README_FOR_CLAUDE_WEB.md` ⭐ Start here
2. `CLAUDE_WEB_INSTRUCTIONS.md` 📖 Detailed steps
3. `EMERGE_ENHANCEMENT_REQUIREMENTS.md` 📋 Feature specs

### Step 3: Give Instructions

Tell CC-Web:

```
You're working in a fork of the emerge repository.

Read README_FOR_CLAUDE_WEB.md and follow the instructions to add
advanced file filtering capabilities to emerge.

The repository has already been forked. Start at Step 1 in
CLAUDE_WEB_INSTRUCTIONS.md (Setup Repository).

Goal: Add file_inclusions, fix file_exclusions, add metric_filters,
and add filter_profiles to enable clean visualizations.

Timeline: 2.5-3.5 days
```

---

## What CC-Web Will Do

### In Emerge Fork Repository:
1. Create branch: `feature/advanced-filtering`
2. Modify: `emerge/analysis.py`, `emerge/config.py`, etc.
3. Add: Tests, documentation, examples
4. Commit and push changes

### Deliverables:
- ✅ File filtering features implemented
- ✅ Tests (>80% coverage)
- ✅ Documentation updated
- ✅ Example configs created
- ✅ Ready for PR to upstream emerge

---

## After CC-Web Completes

### Test It:
```bash
# Install your enhanced emerge
pip install git+https://github.com/YOUR_USERNAME/emerge.git@feature/advanced-filtering

# Test with moderator project
cd /home/thh3/personal/moderator
emerge -c test-gear1-filter.yaml -v

# Should output: Scanned 9 files (not 66)
```

### Create PR:
1. Review CC-Web's changes
2. Use `PR_SUMMARY.md` (CC-Web will create this)
3. Submit PR to https://github.com/glato/emerge

---

## Files in This Package

### Primary Documents (Give to CC-Web):
- `README_FOR_CLAUDE_WEB.md` - Overview and quick start
- `CLAUDE_WEB_INSTRUCTIONS.md` - Step-by-step implementation
- `EMERGE_ENHANCEMENT_REQUIREMENTS.md` - Feature specifications

### Supporting Documents (Context):
- `SETUP_CLARIFICATION.md` - Explains two-repo setup
- `ARCHITECTURE_ANALYSIS.md` - Why we need this
- `START_HERE.md` - This file

---

## Common Questions

**Q: Should CC-Web work in moderator or emerge repo?**
A: **Emerge repo!** CC-Web modifies the tool (emerge), not your project (moderator).

**Q: Where do I get the emerge fork URL?**
A: Check your GitHub account. You should have forked https://github.com/glato/emerge

**Q: What if CC-Web starts in the wrong repo?**
A: Tell it to navigate to your emerge fork: `cd /path/to/emerge-fork`

**Q: How long will this take?**
A: 2.5-3.5 days for core features, 5-6 days with optional UI improvements

**Q: What happens after CC-Web finishes?**
A: You test the enhanced emerge, then create a PR to the original emerge repo

---

## Timeline

| Day | CC-Web Tasks |
|-----|--------------|
| 1 | Setup, understand code, implement file inclusions |
| 2 | Fix exclusions, add metric filters, write tests |
| 3 | Add filter profiles, documentation, examples |
| 3.5 | Validation, commit, push |

---

## Success Criteria

✅ This YAML config works in enhanced emerge:
```yaml
filter_profiles:
  - profile_name: "gear1-core"
    file_inclusions:
      exact_files:
        - "src/orchestrator.py"
        - "src/decomposer.py"
        # ... 7 more files

analyses:
  - analysis_name: gear1
    apply_filter_profile: "gear1-core"
    export:
      - d3
      - graphml
```

✅ Running emerge produces 9-file graph (not 66-file hairball)

✅ All tests pass, documentation complete

---

## 📞 Next Steps

1. **Open Claude Code Web** with your emerge fork repository
2. **Upload** the 3 documentation files
3. **Paste** the instruction prompt from Step 3 above
4. **Let CC-Web work** for 2.5-3.5 days
5. **Test** the enhanced emerge
6. **Submit PR** to upstream emerge

**Good luck! This will be a valuable contribution to the emerge project! 🎉**
