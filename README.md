# File Size Visualizer

A Python application that creates a visual representation of file and directory sizes, similar to WinDirStat. The visualization uses a treemap layout where the size of each rectangle is proportional to the file size, and the color indicates the file type.

## Features

- Visual representation of file and directory sizes using treemap layout
- Color coding by file type
- Interactive: click on any file/directory to see detailed information
- Progress indicator during directory scanning
- Handles large directory structures
- Shows file names for larger items

## File Type Colors

- 🔴 Red: Image files (.jpg, .jpeg, .png, .gif)
- 🔵 Blue: Documents (.pdf, .doc, .docx, .txt, .md)
- 🟢 Green: Code files (.py, .js, .html, .css)
- 🟡 Yellow: Archives (.zip, .rar, .gz, .7z, .tar)
- 🟣 Purple: Media files (.mp3, .mp4, .avi, .mov)
- �cyan Cyan: System files (.exe, .dll, .sys)
- ⚫ Gray: Directories and unknown file types

## Requirements

- Python 3.6+
- tkinter (usually comes with Python)

## Installation

1. Clone this repository:
    ```
    git clone https://github.com/yourusername/sizegraph.git
    cd sizegraph

    ```
2. (Optional) Create and activate a virtual environment:
    ```
    python -m venv venv
    source venv/bin/activate # On Windows: venv\Scripts\activate
    ```
3. Install the required packages:
    ```
    pip install -r requirements.txt
    ```
4. Run the application:
    ```
    python sizegraph.py
    ```

This has only been tested on an old Mac. Your mileage may vary.