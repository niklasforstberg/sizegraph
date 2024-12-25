from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import os
import tkinter as tk
from tkinter import ttk
import math

@dataclass
class FileInfo:
    path: Path
    size: int = 0
    is_dir: bool = False
    children: List['FileInfo'] = field(default_factory=list)
    parent: Optional['FileInfo'] = field(default=None, repr=False)  # repr=False to avoid circular reference in prints
    percentage: float = 0.0  # New field for size percentage

def traverse_directory(path: Path, parent: Optional[FileInfo] = None) -> FileInfo:
    path_obj = Path(path)
    is_dir = path_obj.is_dir()
    
    obj = FileInfo(
        path=path_obj,
        is_dir=is_dir,
        size=path_obj.stat().st_size if not is_dir else 0,
        parent=parent
    )
    
    if is_dir:
        for entry in os.scandir(path):
            obj.children.append(traverse_directory(entry.path, parent=obj))
        obj.size = sum(child.size for child in obj.children)
            
    return obj

def print_tree(root: FileInfo, indent: str = "", is_last: bool = True, dirs_only: bool = False) -> None:
    # Skip files if dirs_only is True
    if dirs_only and not root.is_dir:
        return
        
    prefix = "└── " if is_last else "├── "
    size_str = f"[{root.size:,} bytes] ({root.percentage:.1f}%)"
    print(f"{indent}{prefix}{root.path.name} {size_str}")
    
    child_indent = indent + ("    " if is_last else "│   ")
    # Filter children if dirs_only
    children = [c for c in root.children if not dirs_only or c.is_dir]
    for i, child in enumerate(children):
        print_tree(child, child_indent, i == len(children) - 1, dirs_only)
 

def calculate_percentages(root: FileInfo) -> None:
    total_size = root.size  # Root size is the reference
    
    def _calc_percentage(node: FileInfo) -> None:
        # Calculate percentage of total size
        node.percentage = (node.size / total_size) * 100
        # Recurse for directories
        if node.is_dir:
            for child in node.children:
                _calc_percentage(child)
    
    # Add percentage field to FileInfo class first
    FileInfo.percentage = field(default=0.0)
    
    # Start calculation from root
    _calc_percentage(root)

class TreemapCanvas(tk.Canvas):
    def __init__(self, master, root_info: FileInfo, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.root_info = root_info
        self.bind('<Configure>', self.on_resize)

    def on_resize(self, event):
        self.delete('all')
        self.draw_treemap(self.root_info, 0, 0, event.width, event.height)

    def draw_treemap(self, node: FileInfo, x: int, y: int, width: int, height: int):
        if width < 1 or height < 1:
            return

        # Draw current rectangle
        self.create_rectangle(x, y, x + width, y + height, fill='#e0e0e0', outline='white')
        
        if not node.is_dir or not node.children:
            self.create_text(x + width/2, y + height/2, 
                           text=f"{node.path.name}\n{node.percentage:.1f}%",
                           anchor='center')
            return

        # Sort children by size (largest first)
        sorted_children = sorted(node.children, key=lambda x: x.size, reverse=True)
        
        # Calculate layout
        if width > height:
            current_x = x
            for child in sorted_children:
                child_width = int(width * (child.size / node.size))
                self.draw_treemap(child, current_x, y, child_width, height)
                current_x += child_width
        else:
            current_y = y
            for child in sorted_children:
                child_height = int(height * (child.size / node.size))
                self.draw_treemap(child, x, current_y, width, child_height)
                current_y += child_height

def main():
    import sys
    
    # Use command line arg if provided, else use current directory
    target_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    
    print(f"\nScanning: {target_path}\n")
    root = traverse_directory(target_path)
    print_tree(root)

    calculate_percentages(root)
    
    print("\nDirectories only:")
    print_tree(root, dirs_only=True)

    # Create GUI window
    root_window = tk.Tk()
    root_window.title("Directory Size Treemap")
    root_window.geometry("800x800")

    canvas = TreemapCanvas(root_window, root, bg='white')
    canvas.pack(fill=tk.BOTH, expand=True)

    root_window.mainloop()

if __name__ == "__main__":
    main()
