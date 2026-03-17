#!/usr/bin/env python3
"""
Workspace Cleanup Script with Safety Checks
Removes test files, debug scripts, and temporary documentation.
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime
import json

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

# Project root
PROJECT_ROOT = Path(__file__).parent

# Files and folders to delete
FILES_TO_DELETE = {
    "root_temp_docs": [
        "API_CLI_FIX_SUMMARY.md",
        "CACHING_DISABLED.md",
        "FINAL_YTD_COMPARISON.md",
        "UI_DASHBOARD_TEST_SUMMARY.md",
        "VERIFICATION_COMPLETE.md",
        "YTD_CLI_vs_UI_COMPARISON.md",
        "YTD_TEST_SUMMARY.md",
        "TASK_ETF_RS_BACKTEST.md",
    ],
    "root_test_scripts": [
        "refresh_all_data.py",
        "run_9sector_backtest.py",
        "run_leveraged_backtest.py",
        "save_9sector_results.py",
        "test_api_backtest.py",
        "test_ui_integration.py",
        "verify_setup.py",
    ],
    "api_test_files": [
        "api/test_api.py",
    ],
    "ui_temp_docs": [
        "ui/BACKTEST_FIX_SUMMARY.md",
        "ui/CLI_UI_BACKTEST_COMPARISON.md",
        "ui/CLI_UI_COMPARISON.md",
        "ui/DASHBOARD_FIX_SUMMARY.md",
        "ui/FINAL_DASHBOARD_STATUS.md",
        "ui/UI_FIX_SUMMARY.md",
    ],
    "ui_test_scripts": [
        "ui/capture_all_universes.cjs",
        "ui/complete_ui_validation.cjs",
        "ui/diagnose_signals_page.js",
        "ui/direct_api_test.html",
        "ui/final_validation.cjs",
        "ui/test_all_pages_final.js",
        "ui/test_all_pages.js",
        "ui/test_all_universes_dashboard.cjs",
        "ui/test_api_calls.js",
        "ui/test_backtest_page.cjs",
        "ui/test_backtest_results.js",
        "ui/test_dashboard_all_universes.js",
        "ui/test_dashboard_api.cjs",
        "ui/test_dashboard_comprehensive.js",
        "ui/test_dashboard_fixed.cjs",
        "ui/test_dashboard_quick.cjs",
        "ui/test_dashboard_quick.js",
        "ui/test_pages_quick.js",
        "ui/test_signals_all_universes.js",
        "ui/test_signals_fixed.cjs",
        "ui/test_simple.js",
        "ui/test_ui_final.js",
        "ui/test_ui_screens.js",
        "ui/view_screenshots.html",
    ],
    "ui_backup_files": [
        "ui/src/pages/Signals-broken.jsx.bak",
    ],
}

FOLDERS_TO_DELETE = {
    "ui_screenshots": "ui/screenshots",
    "ui_test_results": "ui/test-results",
}

# Optional: Data cache (regeneratable)
OPTIONAL_DELETE = {
    "price_cache": "data/price_data.csv",
}


def get_file_size(path):
    """Get human-readable file size."""
    try:
        size = os.path.getsize(path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except:
        return "N/A"


def get_folder_size(path):
    """Get total size of folder."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_folder_size(entry.path)
    except:
        pass

    for unit in ['B', 'KB', 'MB', 'GB']:
        if total < 1024.0:
            return f"{total:.1f} {unit}"
        total /= 1024.0
    return f"{total:.1f} TB"


def scan_files(dry_run=True):
    """Scan and display files to be deleted."""
    print_header("WORKSPACE CLEANUP SCAN")

    total_files = 0
    total_folders = 0
    existing_files = []
    existing_folders = []

    # Scan files
    for category, files in FILES_TO_DELETE.items():
        print(f"\n{Colors.BOLD}{Colors.BLUE}Category: {category}{Colors.END}")
        category_count = 0

        for file_path in files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                size = get_file_size(full_path)
                print(f"  {Colors.YELLOW}→{Colors.END} {file_path} ({size})")
                existing_files.append((category, full_path, file_path))
                category_count += 1
            else:
                if not dry_run:
                    print(f"  {Colors.CYAN}⊘{Colors.END} {file_path} (not found, skipping)")

        if category_count > 0:
            total_files += category_count
            print(f"  {Colors.GREEN}Subtotal: {category_count} files{Colors.END}")
        else:
            print(f"  {Colors.CYAN}No files to delete in this category{Colors.END}")

    # Scan folders
    print(f"\n{Colors.BOLD}{Colors.BLUE}Folders to Delete:{Colors.END}")
    for name, folder_path in FOLDERS_TO_DELETE.items():
        full_path = PROJECT_ROOT / folder_path
        if full_path.exists():
            size = get_folder_size(full_path)
            file_count = sum(1 for _ in full_path.rglob('*') if _.is_file())
            print(f"  {Colors.YELLOW}→{Colors.END} {folder_path}/ ({file_count} files, {size})")
            existing_folders.append((name, full_path, folder_path))
            total_folders += 1
        else:
            print(f"  {Colors.CYAN}⊘{Colors.END} {folder_path}/ (not found, skipping)")

    # Optional deletions
    print(f"\n{Colors.BOLD}{Colors.BLUE}Optional (Data Cache):{Colors.END}")
    optional_files = []
    for name, file_path in OPTIONAL_DELETE.items():
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            size = get_file_size(full_path)
            print(f"  {Colors.YELLOW}→{Colors.END} {file_path} ({size}) - regeneratable")
            optional_files.append((name, full_path, file_path))
        else:
            print(f"  {Colors.CYAN}⊘{Colors.END} {file_path} (not found)")

    # Summary
    print_header("SCAN SUMMARY")
    print(f"{Colors.BOLD}Files to delete:{Colors.END} {total_files}")
    print(f"{Colors.BOLD}Folders to delete:{Colors.END} {total_folders}")
    print(f"{Colors.BOLD}Optional files:{Colors.END} {len(optional_files)}")
    print(f"{Colors.BOLD}Total items:{Colors.END} {total_files + total_folders + len(optional_files)}")

    return existing_files, existing_folders, optional_files


def create_backup(files, folders):
    """Create a backup archive before deletion."""
    print_header("CREATING BACKUP")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = PROJECT_ROOT / f".cleanup_backup_{timestamp}"

    try:
        backup_dir.mkdir(exist_ok=True)
        print_info(f"Backup directory: {backup_dir}")

        # Backup files
        for category, full_path, rel_path in files:
            backup_path = backup_dir / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(full_path, backup_path)
            print(f"  {Colors.GREEN}✓{Colors.END} Backed up: {rel_path}")

        # Backup folders
        for name, full_path, rel_path in folders:
            backup_path = backup_dir / rel_path
            shutil.copytree(full_path, backup_path, dirs_exist_ok=True)
            file_count = sum(1 for _ in backup_path.rglob('*') if _.is_file())
            print(f"  {Colors.GREEN}✓{Colors.END} Backed up: {rel_path}/ ({file_count} files)")

        # Save metadata
        metadata = {
            "timestamp": timestamp,
            "files": [rel_path for _, _, rel_path in files],
            "folders": [rel_path for _, _, rel_path in folders],
        }
        with open(backup_dir / "backup_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        print_success(f"Backup created successfully: {backup_dir.name}")
        return backup_dir

    except Exception as e:
        print_error(f"Backup failed: {e}")
        return None


def delete_files(files, folders, backup_dir):
    """Delete files and folders."""
    print_header("DELETING FILES")

    deleted_count = 0
    failed_count = 0

    # Delete files
    print(f"\n{Colors.BOLD}Deleting individual files...{Colors.END}")
    for category, full_path, rel_path in files:
        try:
            os.remove(full_path)
            print(f"  {Colors.GREEN}✓{Colors.END} Deleted: {rel_path}")
            deleted_count += 1
        except Exception as e:
            print_error(f"Failed to delete {rel_path}: {e}")
            failed_count += 1

    # Delete folders
    print(f"\n{Colors.BOLD}Deleting folders...{Colors.END}")
    for name, full_path, rel_path in folders:
        try:
            shutil.rmtree(full_path)
            print(f"  {Colors.GREEN}✓{Colors.END} Deleted: {rel_path}/")
            deleted_count += 1
        except Exception as e:
            print_error(f"Failed to delete {rel_path}: {e}")
            failed_count += 1

    print_header("DELETION SUMMARY")
    print_success(f"Successfully deleted: {deleted_count} items")
    if failed_count > 0:
        print_error(f"Failed to delete: {failed_count} items")

    if backup_dir:
        print_info(f"Backup available at: {backup_dir}")
        print_info(f"To restore: mv {backup_dir}/* .")

    return deleted_count, failed_count


def restore_from_backup(backup_dir):
    """Restore files from backup."""
    if not backup_dir or not backup_dir.exists():
        print_error("Backup directory not found!")
        return False

    print_header("RESTORING FROM BACKUP")

    try:
        # Read metadata
        with open(backup_dir / "backup_metadata.json", "r") as f:
            metadata = json.load(f)

        # Restore files
        for rel_path in metadata["files"]:
            src = backup_dir / rel_path
            dst = PROJECT_ROOT / rel_path
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                print_success(f"Restored: {rel_path}")

        # Restore folders
        for rel_path in metadata["folders"]:
            src = backup_dir / rel_path
            dst = PROJECT_ROOT / rel_path
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)
                print_success(f"Restored: {rel_path}/")

        print_success("Restore completed successfully!")
        return True

    except Exception as e:
        print_error(f"Restore failed: {e}")
        return False


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up test files and temporary documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview files without deleting (default mode)",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete files (requires confirmation)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup (not recommended)",
    )
    parser.add_argument(
        "--restore",
        type=str,
        metavar="BACKUP_DIR",
        help="Restore files from backup directory",
    )
    parser.add_argument(
        "--include-cache",
        action="store_true",
        help="Also delete data cache (price_data.csv)",
    )

    args = parser.parse_args()

    # Restore mode
    if args.restore:
        backup_dir = Path(args.restore)
        restore_from_backup(backup_dir)
        return

    # Scan files
    files, folders, optional_files = scan_files(dry_run=not args.delete)

    if not files and not folders:
        print_success("No files to clean up. Workspace is already clean!")
        return

    # Dry-run mode (default)
    if not args.delete:
        print_header("DRY-RUN MODE")
        print_warning("This is a preview. No files were deleted.")
        print_info("To actually delete files, run with --delete flag:")
        print(f"  {Colors.CYAN}python cleanup_workspace.py --delete{Colors.END}")
        if optional_files:
            print_info("To also delete cache, add --include-cache flag")
        return

    # Delete mode - require confirmation
    print_header("DELETE MODE")
    print_warning("You are about to permanently delete these files!")

    # Include optional files if requested
    if args.include_cache and optional_files:
        print_info("Cache deletion is enabled")
        files.extend(optional_files)

    response = input(f"\n{Colors.BOLD}Continue with deletion? (type 'yes' to confirm): {Colors.END}")
    if response.lower() != 'yes':
        print_warning("Deletion cancelled by user")
        return

    # Create backup unless explicitly disabled
    backup_dir = None
    if not args.no_backup:
        backup_dir = create_backup(files, folders)
        if not backup_dir:
            print_error("Backup failed. Aborting deletion for safety.")
            return
    else:
        print_warning("Backup disabled - proceeding without backup!")
        response = input(f"{Colors.RED}Are you SURE? (type 'yes'): {Colors.END}")
        if response.lower() != 'yes':
            print_warning("Deletion cancelled")
            return

    # Perform deletion
    deleted, failed = delete_files(files, folders, backup_dir)

    if failed == 0:
        print_success("Cleanup completed successfully! ✨")
        if backup_dir:
            print_info(f"You can safely delete backup after verifying: rm -rf {backup_dir}")


if __name__ == "__main__":
    main()
