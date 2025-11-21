# Repository Setup Clarification

## Where Does Claude Code Web Work?

### ✅ CC-Web Works In: **Your Emerge Fork**
- **Repository:** Your forked copy of https://github.com/glato/emerge
- **Location:** Separate repository (NOT the moderator repo)
- **Purpose:** Add filtering features to emerge itself

### ❌ CC-Web Does NOT Work In: Moderator Repository
- **Repository:** /home/thh3/personal/moderator
- **Purpose:** This is YOUR project that USES emerge
- **Status:** Already has the documentation package

---

## The Two Repositories

### Repository 1: Moderator (Your Project)
```
/home/thh3/personal/moderator/
├── src/                      # Your code
├── docs/                     # Your docs
├── emerge-output/            # ← Documentation package for CC-Web
│   ├── README_FOR_CLAUDE_WEB.md
│   ├── CLAUDE_WEB_INSTRUCTIONS.md
│   └── EMERGE_ENHANCEMENT_REQUIREMENTS.md
└── emerge-config.yaml        # Config that will use enhanced emerge
```

**Role:** This is where you WANT to use emerge for clean visualizations

### Repository 2: Emerge Fork (Tool Repository)
```
/path/to/your/emerge-fork/
├── emerge/                   # emerge source code
│   ├── analysis.py          # Files CC-Web will modify
│   ├── config.py            # Files CC-Web will modify
│   └── scanner.py           # Files CC-Web will modify
├── tests/                    # CC-Web will add tests here
├── examples/                 # CC-Web will add examples here
└── README.md                 # CC-Web will update this
```

**Role:** This is the TOOL that CC-Web will enhance

---

## Workflow

### What You Do:
1. ✅ Fork emerge on GitHub (already done)
2. ✅ Give CC-Web access to your emerge fork repository
3. ✅ Provide documentation from moderator/emerge-output/

### What CC-Web Does:
1. Works in **emerge fork repository** (NOT moderator)
2. Creates branch: `feature/advanced-filtering`
3. Modifies emerge source code to add filtering
4. Adds tests, documentation, examples
5. Commits and pushes to **emerge fork**

### What You Get:
1. Enhanced emerge in your fork with filtering features
2. You can then use it to analyze moderator project:
   ```bash
   # Install your enhanced emerge
   pip install git+https://github.com/YOUR_USERNAME/emerge.git@feature/advanced-filtering

   # Use it with moderator
   cd /home/thh3/personal/moderator
   emerge -c emerge-config-gear1-clean.yaml

   # Result: Clean 9-file visualization!
   ```

---

## How to Give CC-Web Access

### Option 1: Start CC-Web in Emerge Fork
When starting Claude Code Web session:
- **Repository URL:** `https://github.com/YOUR_USERNAME/emerge`
- **Provide files:** Upload the 3 documentation files from moderator/emerge-output/

### Option 2: Start CC-Web and Navigate
If CC-Web starts in moderator:
```bash
# CC-Web should clone your emerge fork
git clone https://github.com/YOUR_USERNAME/emerge.git
cd emerge

# Then follow instructions
```

---

## File Locations Summary

### Files CC-Web Needs (from moderator repo):
- `emerge-output/README_FOR_CLAUDE_WEB.md`
- `emerge-output/CLAUDE_WEB_INSTRUCTIONS.md`
- `emerge-output/EMERGE_ENHANCEMENT_REQUIREMENTS.md`

### Files CC-Web Will Create/Modify (in emerge fork):
- `emerge/analysis.py` (modified)
- `emerge/config.py` (modified)
- `emerge/scanner.py` (modified)
- `tests/test_filtering.py` (new)
- `FILTERING.md` (new)
- `examples/filtering/*.yaml` (new)
- `README.md` (modified)

---

## Quick Start for CC-Web

### When CC-Web Starts:

1. **You should be in:** `/path/to/emerge-fork/`
2. **Check:** `git remote -v` should show your emerge fork
3. **If wrong repo:**
   ```bash
   # Exit moderator, go to emerge fork
   cd /path/to/emerge-fork
   ```

4. **Then follow:** `README_FOR_CLAUDE_WEB.md` instructions

---

## Summary

**Think of it like this:**

- **Moderator = Your house** (where you want better tools)
- **Emerge = The toolbox** (what CC-Web will improve)
- **Documentation package = Instructions** (how to improve the toolbox)

CC-Web goes to the **toolbox factory** (emerge repo), improves the tool, then you bring that improved tool back to your **house** (moderator) to use it.

---

**Still Confused?**

The key point: **CC-Web modifies emerge (the tool), not moderator (your project)**.

You'll use the enhanced emerge LATER to analyze moderator.
