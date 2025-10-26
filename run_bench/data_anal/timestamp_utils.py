#!/usr/bin/env python3
"""
Utility functions for handling timestamped result directories
"""

import os
import re
from pathlib import Path


def is_valid_timestamp_dir(dirname):
    """
    Check if directory name matches YYYYMMDDHHMM format

    Args:
        dirname: Directory name to check

    Returns:
        True if matches timestamp format, False otherwise
    """
    # Check if matches YYYYMMDDHHMM format (12 digits)
    return bool(re.match(r'^\d{12}$', dirname))


def get_all_timestamp_dirs(case_path):
    """
    Get all timestamp directories for a case, sorted chronologically

    Args:
        case_path: Path to case directory (e.g., results/bc-urand/autonuma_tiering/cpu0.firsttouch0_2/cxl_232G)

    Returns:
        List of full paths to timestamp directories, sorted oldest to newest
    """
    if not os.path.exists(case_path):
        return []

    timestamp_dirs = []

    try:
        for item in os.listdir(case_path):
            item_path = os.path.join(case_path, item)
            if os.path.isdir(item_path) and is_valid_timestamp_dir(item):
                timestamp_dirs.append(item_path)
    except Exception as e:
        print(f"Error reading directory {case_path}: {e}")
        return []

    # Sort by timestamp (directory name)
    timestamp_dirs.sort(key=lambda x: os.path.basename(x))

    return timestamp_dirs


def get_latest_timestamp_dir(case_path):
    """
    Get the latest timestamp directory for a case

    Args:
        case_path: Path to case directory

    Returns:
        Full path to latest timestamp directory, or None if none found
    """
    timestamp_dirs = get_all_timestamp_dirs(case_path)

    if not timestamp_dirs:
        return None

    # Return the last one (most recent) since list is sorted
    return timestamp_dirs[-1]


def get_timestamp_from_path(timestamp_dir_path):
    """
    Extract timestamp string from timestamp directory path

    Args:
        timestamp_dir_path: Full path to timestamp directory

    Returns:
        Timestamp string (YYYYMMDDHHMM) or None if invalid
    """
    dirname = os.path.basename(timestamp_dir_path)
    if is_valid_timestamp_dir(dirname):
        return dirname
    return None


def has_timestamp_subdirs(case_path):
    """
    Check if a case directory has timestamp subdirectories

    Args:
        case_path: Path to case directory

    Returns:
        True if has at least one timestamp subdirectory, False otherwise
    """
    timestamp_dirs = get_all_timestamp_dirs(case_path)
    return len(timestamp_dirs) > 0


def is_old_structure(case_path):
    """
    Check if a case directory uses old structure (files directly in case dir, not in timestamp subdirs)

    Args:
        case_path: Path to case directory

    Returns:
        True if old structure detected (has output.log directly), False if new structure
    """
    if not os.path.exists(case_path):
        return False

    # Check if output.log exists directly in case_path (old structure)
    output_log = os.path.join(case_path, "output.log")
    return os.path.exists(output_log)
