# File Size Visualizer

Simple GUI tool that visualizes file sizes in a directory as horizontal bars. Helps identify large files and space usage patterns.

## Features
- Scans all files recursively from a given directory
- Shows files as horizontal bars proportional to their size
- Click any bar to see detailed file info (path and size)
- Sorts files by size (largest first)

## Requirements
- Python 3.x
- tkinter (included with Python, but needs separate install on Homebrew Python)

## Installation

### If using Homebrew Python: 
bash
brew install python-tk@3.12 # Replace 3.12 with your Python version


### If using Python.org Python:
No additional installation needed - tkinter is included.

## Usage
1. Clone this repo
2. Edit `root_path` in `sizegraph.py` to your target directory (defaults to current directory)
3. Run:
python sizegraph.py

This has only been tested on an old Mac. Your mileage may vary.