# File Size Visualizer

A Python application that creates a visual representation of file and directory sizes, similar to WinDirStat. The visualization uses a treemap layout where the size of each rectangle is proportional to the file size, enabling the user to easily see which files take up the most space. The visualization is not perfect, but it gets the job done.

## Features

- Visual representation of file and directory sizes using treemap layout
- Interactive: click on any file/directory to see detailed information
- Progress indicator during directory scanning
- Handles large directory structures

## Requirements

- Python 3.6+
- PySide6

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
    python sizegraphv2.py
    ```

This has only been tested on an old Mac. Your mileage may vary.