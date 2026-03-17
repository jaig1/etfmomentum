# Workspace Cleanup Guide

## Overview
The `cleanup_workspace.py` script safely removes test files, debug scripts, and temporary documentation while keeping all core application files.

## Safety Features
✅ **Dry-run mode by default** - Preview before deleting
✅ **Automatic backup** - Creates timestamped backup before deletion
✅ **Restore capability** - Can undo deletion if needed
✅ **Confirmation prompts** - Requires explicit 'yes' to proceed
✅ **Detailed logging** - Shows exactly what's being deleted

---

## Quick Start

### 1. Preview What Will Be Deleted (Safe)
```bash
python cleanup_workspace.py --dry-run
```
This shows all files that would be deleted without actually deleting anything.

### 2. Delete Files with Backup (Recommended)
```bash
python cleanup_workspace.py --delete
```
- Creates automatic backup in `.cleanup_backup_TIMESTAMP/`
- Asks for confirmation before deleting
- You can restore files if needed

### 3. Delete Including Cache (Optional)
```bash
python cleanup_workspace.py --delete --include-cache
```
Also deletes `data/price_data.csv` (regeneratable from FMP API)

### 4. Delete Without Backup (Not Recommended)
```bash
python cleanup_workspace.py --delete --no-backup
```
⚠️ **WARNING:** This permanently deletes files without backup!

---

## What Gets Deleted

### ❌ Root Directory Files (15 files)
- `API_CLI_FIX_SUMMARY.md`
- `CACHING_DISABLED.md`
- `FINAL_YTD_COMPARISON.md`
- `UI_DASHBOARD_TEST_SUMMARY.md`
- `VERIFICATION_COMPLETE.md`
- `YTD_CLI_vs_UI_COMPARISON.md`
- `YTD_TEST_SUMMARY.md`
- `TASK_ETF_RS_BACKTEST.md`
- `refresh_all_data.py`
- `run_9sector_backtest.py`
- `run_leveraged_backtest.py`
- `save_9sector_results.py`
- `test_api_backtest.py`
- `test_ui_integration.py`
- `verify_setup.py`

### ❌ API Test Files (1 file)
- `api/test_api.py`

### ❌ UI Temporary Docs (6 files)
- `ui/BACKTEST_FIX_SUMMARY.md`
- `ui/CLI_UI_BACKTEST_COMPARISON.md`
- `ui/CLI_UI_COMPARISON.md`
- `ui/DASHBOARD_FIX_SUMMARY.md`
- `ui/FINAL_DASHBOARD_STATUS.md`
- `ui/UI_FIX_SUMMARY.md`

### ❌ UI Test Scripts (24 files)
All files matching `ui/test_*.js`, `ui/test_*.cjs`, and debug HTML files

### ❌ UI Backup Files (1 file)
- `ui/src/pages/Signals-broken.jsx.bak`

### ❌ UI Folders (2 folders)
- `ui/screenshots/` - 26 PNG files
- `ui/test-results/` - Test output folder

### ⚠️ Optional: Data Cache (with --include-cache)
- `data/price_data.csv` - Regeneratable from FMP API

---

## What Gets KEPT (Core Application)

### ✅ Core Python Package (etfmomentum/)
- All core modules: config, backtest, signal generation, etc.
- Research modules: optimizer, defensive strategies, etc.

### ✅ FastAPI Backend (api/)
- API routes, models, main application
- requirements.txt

### ✅ React UI (ui/)
- Source code (src/)
- Components and pages
- Build configuration (package.json, vite.config.js)
- Public assets

### ✅ Configuration & Data
- `.env` - API keys
- `pyproject.toml` - Project config
- `etflist/*.csv` - ETF universe definitions
- `output/` - Backtest results
- Startup scripts (start_api.sh, start_ui.sh)

---

## Restore Files from Backup

If you deleted files and want them back:

```bash
# List available backups
ls -la .cleanup_backup_*

# Restore from specific backup
python cleanup_workspace.py --restore .cleanup_backup_20260316_143000
```

Or manually restore:
```bash
# Find your backup folder
ls -d .cleanup_backup_*

# Restore all files
cp -r .cleanup_backup_TIMESTAMP/* .
```

---

## Example Usage

### Scenario 1: First-time cleanup
```bash
# Step 1: Preview
python cleanup_workspace.py --dry-run

# Step 2: Review the list, then delete with backup
python cleanup_workspace.py --delete

# Step 3: Verify everything works
uv run python -m etfmomentum signal --universe sp500
cd ui && npm run dev

# Step 4: If all good, delete backup
rm -rf .cleanup_backup_*
```

### Scenario 2: Aggressive cleanup (including cache)
```bash
# Delete everything including price cache
python cleanup_workspace.py --delete --include-cache

# Cache will regenerate on next run
uv run python -m etfmomentum backtest --universe sp500 --refresh
```

### Scenario 3: Oops, I need those files back!
```bash
# Restore from backup
python cleanup_workspace.py --restore .cleanup_backup_20260316_143000
```

---

## Command Reference

```
Usage: python cleanup_workspace.py [OPTIONS]

Options:
  --dry-run         Preview files without deleting (default)
  --delete          Actually delete files (requires confirmation)
  --no-backup       Skip creating backup (not recommended)
  --include-cache   Also delete data/price_data.csv
  --restore DIR     Restore files from backup directory
  -h, --help        Show help message
```

---

## Expected Output

### Dry-run Output
```
======================================================================
                     WORKSPACE CLEANUP SCAN
======================================================================

Category: root_temp_docs
  → API_CLI_FIX_SUMMARY.md (8.1 KB)
  → CACHING_DISABLED.md (3.4 KB)
  ...
  Subtotal: 8 files

Category: ui_test_scripts
  → ui/test_all_pages.js (4.4 KB)
  ...
  Subtotal: 24 files

Folders to Delete:
  → ui/screenshots/ (26 files, 2.3 MB)
  → ui/test-results/ (5 files, 45.2 KB)

======================================================================
                          SCAN SUMMARY
======================================================================
Files to delete: 54
Folders to delete: 2
Total items: 56
```

### Delete Output
```
======================================================================
                       CREATING BACKUP
======================================================================
ℹ Backup directory: .cleanup_backup_20260316_143000
  ✓ Backed up: API_CLI_FIX_SUMMARY.md
  ...
✓ Backup created successfully: .cleanup_backup_20260316_143000

======================================================================
                       DELETING FILES
======================================================================
  ✓ Deleted: API_CLI_FIX_SUMMARY.md
  ...
✓ Successfully deleted: 56 items
```

---

## Post-Cleanup Verification

After cleanup, verify everything still works:

```bash
# Test CLI
uv run python -m etfmomentum signal --universe sp500 --detailed --refresh

# Test API
cd /Users/jaig/etfmomentum
./start_api.sh &
curl http://localhost:8000/health

# Test UI
cd ui
npm run dev
# Visit http://localhost:5173
```

---

## FAQ

**Q: Is this safe?**
A: Yes! Default mode creates automatic backups and requires confirmation.

**Q: Can I undo the deletion?**
A: Yes! Use `--restore` with your backup folder name.

**Q: What if I accidentally delete the wrong files?**
A: The backup contains everything. Use the restore command to get files back.

**Q: Should I delete the cache?**
A: Optional. It regenerates automatically but adds a few minutes to next backtest.

**Q: Can I delete the backup folder after cleanup?**
A: Yes, after verifying everything works: `rm -rf .cleanup_backup_*`

**Q: What if I want to keep some test scripts?**
A: Edit `cleanup_workspace.py` and remove them from the `FILES_TO_DELETE` dictionary.

---

## Cleanup Checklist

- [ ] Run dry-run mode to preview
- [ ] Review list of files to be deleted
- [ ] Run delete mode with backup (recommended)
- [ ] Verify CLI still works
- [ ] Verify API still works
- [ ] Verify UI still works
- [ ] (Optional) Delete backup folder
- [ ] Commit cleaned workspace to git

---

**Ready to clean up?** Start with: `python cleanup_workspace.py --dry-run`
