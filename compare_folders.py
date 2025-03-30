#!/usr/bin/env python3
"""
Folder Comparison Tool

This script compares two or more folders by calculating checksums of all files recursively.
It displays a table showing which files match, mismatch, or are missing across folders.
"""

import os
import sys
import hashlib
import argparse
import time
from pathlib import Path
from typing import Dict, List, Tuple, Set
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored terminal output
init()

def calculate_checksum(file_path: Path) -> str:
    """Calculate MD5 checksum for a file."""
    hash_md5 = hashlib.md5()
    
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"{Fore.RED}Error calculating checksum for {file_path}: {e}{Style.RESET_ALL}")
        return "ERROR"

def scan_folder(folder_path: Path, show_progress: bool = True, filter_paths: Set[str] = None) -> Dict[str, Dict[str, str]]:
    """
    Recursively scan a folder and calculate checksums for all files.
    
    Args:
        folder_path: Path to the folder to scan
        show_progress: Whether to show progress indicators
        filter_paths: If provided, only calculate checksums for files in this set of relative paths
    
    Returns a dictionary mapping relative paths to a dict with original case path and checksum.
    """
    checksums = {}
    
    if not folder_path.exists():
        print(f"{Fore.RED}Error: Folder {folder_path} does not exist{Style.RESET_ALL}")
        return checksums
    
    # For primary folder (no filter_paths), count all files
    # For secondary folders, we'll only count files that match the filter
    if filter_paths is None:
        # First pass: count total files for progress reporting
        total_files = 0
        if show_progress:
            print(f"Counting files in {folder_path}...", end="", flush=True)
            for _, _, files in os.walk(folder_path):
                total_files += len(files)
            print(f" {total_files} files found.")
        
        # Second pass: calculate checksums with progress
        processed_files = 0
        last_percent = -1
        
        for root, _, files in os.walk(folder_path):
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                relative_path = str(file_path.relative_to(folder_path))
                
                # Show progress
                if show_progress and total_files > 0:
                    processed_files += 1
                    percent = int((processed_files / total_files) * 100)
                    
                    # Update progress only when percentage changes
                    if percent != last_percent:
                        last_percent = percent
                        progress_bar = f"[{'=' * (percent // 5)}>{' ' * (20 - (percent // 5))}]"
                        print(f"\rScanning {folder_path.name}: {progress_bar} {percent}% ({processed_files}/{total_files})", end="", flush=True)
                
                # Store both the original case path and the checksum
                # Use lowercase path as key for case-insensitive comparison
                lowercase_path = relative_path.lower()
                
                if lowercase_path not in checksums:
                    checksums[lowercase_path] = {'original_paths': [relative_path], 'checksums': []}
                else:
                    # If we already have this path with different case, add it to the list
                    checksums[lowercase_path]['original_paths'].append(relative_path)
                
                checksum = calculate_checksum(file_path)
                checksums[lowercase_path]['checksums'].append(checksum)
        
        if show_progress and total_files > 0:
            print()  # New line after progress bar
    else:
        # For secondary folders, only check files that exist in the primary folder
        # Convert filter_paths to lowercase for case-insensitive comparison
        lowercase_filter_paths = {path.lower() for path in filter_paths}
        
        if show_progress:
            print(f"Checking {len(lowercase_filter_paths)} files from primary folder in {folder_path}...")
        
        # Create a mapping of relative paths to actual file paths for quick lookup
        file_map = {}
        for root, _, files in os.walk(folder_path):
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                relative_path = str(file_path.relative_to(folder_path))
                lowercase_path = relative_path.lower()
                
                if lowercase_path not in file_map:
                    file_map[lowercase_path] = [file_path]
                else:
                    file_map[lowercase_path].append(file_path)
        
        # Only process files that are in the filter_paths
        total_files = len(lowercase_filter_paths)
        processed_files = 0
        last_percent = -1
        
        for lowercase_path in lowercase_filter_paths:
            processed_files += 1
            
            # Show progress
            if show_progress and total_files > 0:
                percent = int((processed_files / total_files) * 100)
                
                # Update progress only when percentage changes
                if percent != last_percent:
                    last_percent = percent
                    progress_bar = f"[{'=' * (percent // 5)}>{' ' * (20 - (percent // 5))}]"
                    print(f"\rChecking files in {folder_path.name}: {progress_bar} {percent}% ({processed_files}/{total_files})", end="", flush=True)
            
            # Check if the file exists in this folder (case-insensitive)
            if lowercase_path in file_map:
                checksums[lowercase_path] = {'original_paths': [], 'checksums': []}
                
                # Calculate checksums for all case variations of this file
                for file_path in file_map[lowercase_path]:
                    original_path = str(file_path.relative_to(folder_path))
                    checksums[lowercase_path]['original_paths'].append(original_path)
                    checksums[lowercase_path]['checksums'].append(calculate_checksum(file_path))
        
        if show_progress and total_files > 0:
            print()  # New line after progress bar
    
    return checksums

def compare_folders(folder_paths: List[Path]) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    """
    Compare multiple folders by their file checksums.
    
    Returns:
        - A dictionary mapping files to their checksums and metadata
        - A dictionary mapping folder paths to their file checksums
    """
    # The first folder path is considered the primary folder
    primary_folder = folder_paths[0]
    
    folder_checksums = {}
    
    # Scan each folder and collect all file paths
    print(f"{Fore.CYAN}Starting folder comparison...{Style.RESET_ALL}")
    start_time = time.time()
    
    # First, scan the primary folder to get all files
    print(f"\n{Fore.CYAN}Processing Primary folder: {primary_folder}{Style.RESET_ALL}")
    primary_checksums = scan_folder(primary_folder)
    folder_checksums[str(primary_folder)] = primary_checksums
    
    # Get the set of file paths from the primary folder to use as a filter for other folders
    primary_files = set(primary_checksums.keys())
    
    # Then scan secondary and additional folders, but only check files that exist in the primary folder
    for i, folder_path in enumerate(folder_paths[1:], 1):
        folder_type = "Secondary" if i == 1 else "Additional"
        print(f"\n{Fore.CYAN}Processing {folder_type} folder: {folder_path}{Style.RESET_ALL}")
        
        # Use the full path as the key instead of just the folder name
        folder_checksums[str(folder_path)] = scan_folder(folder_path, filter_paths=primary_files)
    
    # Create a dictionary mapping files to their checksums and metadata (using primary folder checksums)
    file_checksums = {}
    for lowercase_path in primary_files:
        file_data = primary_checksums[lowercase_path]
        # Use the first original path as the display path
        display_path = file_data['original_paths'][0]
        # Use the first checksum as the reference checksum
        reference_checksum = file_data['checksums'][0]
        # Check if this is a multicase file (multiple files with same name but different case)
        is_multicase = len(file_data['original_paths']) > 1
        # Check if all checksums are the same for multicase files
        all_checksums_equal = all(checksum == reference_checksum for checksum in file_data['checksums'])
        
        file_checksums[lowercase_path] = {
            'display_path': display_path,
            'reference_checksum': reference_checksum,
            'is_multicase': is_multicase,
            'all_checksums_equal': all_checksums_equal
        }
    
    elapsed_time = time.time() - start_time
    print(f"\n{Fore.CYAN}Folder comparison completed in {elapsed_time:.2f} seconds.{Style.RESET_ALL}")
    
    return file_checksums, folder_checksums

def get_shortened_path(folder_path: str) -> str:
    """
    Create a shortened path representation that includes the first 10 characters 
    and the folder name, separated by "...".
    """
    path_obj = Path(folder_path)
    folder_name = path_obj.name
    
    if len(folder_path) <= 10 + len(folder_name) + 3:  # +3 for "..."
        return folder_path
    
    # Get the first 10 characters of the path
    start = folder_path[:10]
    
    return f"{start}...{folder_name}"

def display_comparison_table(file_checksums: Dict[str, Dict], 
                            folder_checksums: Dict[str, Dict]) -> None:
    """Display a formatted table of file comparison results."""
    folder_paths = list(folder_checksums.keys())
    primary_folder = folder_paths[0]
    
    # Get shortened paths for display
    shortened_paths = [get_shortened_path(path) for path in folder_paths]
    
    # Calculate column widths
    filename_width = max(len("Filename"), max([len(file_data['display_path']) for file_data in file_checksums.values()], default=10))
    checksum_width = max(len("Checksum"), 32)  # MD5 is 32 characters
    folder_width = max([len(name) for name in shortened_paths], default=10)
    
    # Print table header
    print(f"{'Filename':<{filename_width}} | {'Checksum':<{checksum_width}} | ", end="")
    print(" | ".join(f"{name:<{folder_width}}" for name in shortened_paths))
    print("-" * (filename_width + checksum_width + sum([folder_width + 3 for _ in folder_paths]) + 3))
    
    # Sort files for consistent output
    sorted_files = sorted(file_checksums.keys())
    
    # Initialize counters for summary
    total_files = len(sorted_files)
    total_ok = 0
    total_mismatch = 0
    total_missing = 0
    total_multicase_ok = 0
    total_multicase_mismatch = 0
    
    # Print table rows
    for lowercase_path in sorted_files:
        file_data = file_checksums[lowercase_path]
        display_path = file_data['display_path']
        reference_checksum = file_data['reference_checksum']
        is_multicase = file_data['is_multicase']
        all_checksums_equal = file_data['all_checksums_equal']
        
        print(f"{display_path:<{filename_width}} | {reference_checksum:<{checksum_width}} | ", end="")
        
        # Print status for each folder
        statuses = []
        
        # First folder (primary) is always OK or MULTICASE
        if is_multicase:
            if all_checksums_equal:
                status = f"{Fore.GREEN}MULTICASE{Style.RESET_ALL}"
                total_multicase_ok += 1
            else:
                status = f"{Fore.YELLOW}MULTICASE{Style.RESET_ALL}"
                total_multicase_mismatch += 1
        else:
            status = f"{Fore.GREEN}OK{Style.RESET_ALL}"
            total_ok += 1
            
        statuses.append(f"{status}".ljust(folder_width + len(Fore.RED) + len(Style.RESET_ALL)))
        
        # Check status for other folders
        for folder_path in folder_paths[1:]:
            folder_files = folder_checksums[folder_path]
            
            if lowercase_path not in folder_files:
                status = f"{Fore.RED}MISSING{Style.RESET_ALL}"
                total_missing += 1
            else:
                secondary_file_data = folder_files[lowercase_path]
                is_secondary_multicase = len(secondary_file_data['original_paths']) > 1
                all_secondary_checksums_equal = all(checksum == secondary_file_data['checksums'][0] 
                                                  for checksum in secondary_file_data['checksums'])
                
                # Check if any of the checksums in the secondary folder match the reference checksum
                any_checksum_matches = any(checksum == reference_checksum 
                                         for checksum in secondary_file_data['checksums'])
                
                if is_secondary_multicase:
                    if any_checksum_matches and all_secondary_checksums_equal:
                        status = f"{Fore.GREEN}MULTICASE{Style.RESET_ALL}"
                        total_multicase_ok += 1
                    else:
                        status = f"{Fore.YELLOW}MULTICASE{Style.RESET_ALL}"
                        total_multicase_mismatch += 1
                else:
                    if any_checksum_matches:
                        status = f"{Fore.GREEN}OK{Style.RESET_ALL}"
                        total_ok += 1
                    else:
                        status = f"{Fore.YELLOW}MISMATCH{Style.RESET_ALL}"
                        total_mismatch += 1
            
            statuses.append(f"{status}".ljust(folder_width + len(Fore.RED) + len(Style.RESET_ALL)))
        
        print(" | ".join(statuses))
    
    # Print summary
    print("\nSummary:")
    print(f"Total files checked: {total_files}")
    print(f"Files equal ({Fore.GREEN}OK{Style.RESET_ALL}): {total_ok}")
    print(f"Files with multiple case variations, all equal ({Fore.GREEN}MULTICASE{Style.RESET_ALL}): {total_multicase_ok}")
    print(f"Files with multiple case variations, not all equal ({Fore.YELLOW}MULTICASE{Style.RESET_ALL}): {total_multicase_mismatch}")
    print(f"Files not equal ({Fore.YELLOW}MISMATCH{Style.RESET_ALL}): {total_mismatch}")
    print(f"Files missing ({Fore.RED}MISSING{Style.RESET_ALL}): {total_missing}")

def main():
    parser = argparse.ArgumentParser(description="Compare files across multiple folders using checksums.")
    parser.add_argument("primary_folder", help="Primary folder path to compare against")
    parser.add_argument("secondary_folder", help="Secondary folder path to compare with the primary folder")
    parser.add_argument("additional_folders", nargs="*", help="Additional folder paths to compare (optional)")
    args = parser.parse_args()
    
    # Combine all folder paths
    folder_paths = [Path(args.primary_folder), Path(args.secondary_folder)]
    if args.additional_folders:
        folder_paths.extend([Path(folder) for folder in args.additional_folders])
    
    print(f"Comparing {len(folder_paths)} folders:")
    print(f"  - Primary: {folder_paths[0]}")
    for i, path in enumerate(folder_paths[1:], 1):
        if i == 1:
            print(f"  - Secondary: {path}")
        else:
            print(f"  - Additional: {path}")
    print()
    
    file_checksums, folder_checksums = compare_folders(folder_paths)
    
    if not file_checksums:
        print("No files found for comparison.")
        return
    
    display_comparison_table(file_checksums, folder_checksums)

if __name__ == "__main__":
    main()
