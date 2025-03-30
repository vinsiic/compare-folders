# Folder Comparison Tool

This Python script compares two or more folders by calculating checksums of all files recursively. It displays a table showing which files match, mismatch, or are missing across folders.

## Features

- Compare two or more folders recursively
- Calculate MD5 checksums for all files
- Case-insensitive file comparison with special handling for files with same name but different case
- Primary folder-based comparison (only checks files that exist in the primary folder)
- Visual progress indicators during scanning and checksum calculation
- Performance timing information
- Display results in a color-coded table with unique folder identifiers
- Comprehensive summary statistics
- Status indicators:
  - Green "OK" for matching files
  - Green "MULTICASE" for files with multiple case variations where all checksums match
  - Yellow "MISMATCH" for files with different checksums
  - Yellow "MULTICASE" for files with multiple case variations where checksums differ
  - Red "MISSING" for files not present in a folder

## Requirements

- Python 3.6+
- colorama package

## Installation

1. Clone this repository or download the script
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python compare_folders.py primary_folder secondary_folder [additional_folders ...]
```

Where:
- `primary_folder`: The main reference folder (mandatory)
- `secondary_folder`: The folder to compare against the primary folder (mandatory)
- `additional_folders`: Optional additional folders to include in the comparison

### Example

```bash
python compare_folders.py ./original ./backup ./another_copy
```

## Output

The script will display:

1. Progress indicators during scanning:
   - File counting phase
   - Checksum calculation with progress bar
   - Timing information

2. A comparison table with the following columns:
   - Filename: The relative path of the file
   - Checksum: The MD5 checksum of the file
   - Status for each folder: 
     - OK (green): Files match exactly
     - MULTICASE (green): Multiple files with same name but different case, all with matching checksums
     - MULTICASE (yellow): Multiple files with same name but different case, with different checksums
     - MISMATCH (yellow): Files with different checksums
     - MISSING (red): Files not present in a folder

3. Summary statistics:
   - Total files checked
   - Number of files that match exactly (OK)
   - Number of files with multiple case variations where all checksums match
   - Number of files with multiple case variations where checksums differ
   - Number of files that don't match (MISMATCH)
   - Number of files that are missing (MISSING)
