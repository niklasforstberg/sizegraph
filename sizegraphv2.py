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
    def __init__(self, master, root_info: FileInfo, **kwargs):
        super().__init__(master, **kwargs)
        self.root_info = root_info
        self.border_colors = ['black', 'blue', 'brown']
        self.file_colors = ['#CCCCCC', '#CCE5FF', '#E5CCCC']  # Light versions of border colors
        self.border_width = 2
        self.min_size_for_label = 40
        self.tooltip = None
        
        self.bind('<Configure>', self._on_resize)
        self.bind('<Motion>', self._on_motion)
        self.bind('<Leave>', self._hide_tooltip)
        
    def _show_tooltip(self, x, y, text):
        self._hide_tooltip()
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        label = tk.Label(self.tooltip, text=text, bg='lightyellow', 
                        relief='solid', borderwidth=1)
        label.pack()
        
        # Position tooltip near cursor but ensure it's visible
        screen_x = self.winfo_rootx() + x + 10
        screen_y = self.winfo_rooty() + y + 10
        self.tooltip.wm_geometry(f"+{screen_x}+{screen_y}")
        
    def _hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            
    def _on_motion(self, event):
        item = self.find_closest(event.x, event.y)
        if item:
            tags = self.gettags(item)
            if tags and tags[0].startswith('path:'):
                path_info = tags[0].split(':', 1)[1]
                parent_info = tags[1].split(':', 1)[1] if len(tags) > 1 else ""
                tooltip_text = f"File: {path_info}\nIn: {parent_info}" if parent_info else f"Folder: {path_info}"
                self._show_tooltip(event.x, event.y, tooltip_text)
            else:
                self._hide_tooltip()
                
    def _on_resize(self, event):
        self.delete('all')
        self._draw_treemap(
            self.root_info, 
            self.border_width,
            self.border_width,
            event.width - 2 * self.border_width,
            event.height - 2 * self.border_width,
            0
        )
        
    def _draw_treemap(self, node: FileInfo, x: float, y: float, width: float, height: float, color_idx: int):
        if width < 1 or height < 1:  # Skip if too small
            return
            
        border_color = self.border_colors[color_idx]
        if node.is_dir:
            # Draw directory rectangle
            rect_id = self.create_rectangle(
                x, y, x + width, y + height,
                fill='white',
                outline=border_color,
                width=self.border_width,
                tags=(f'path:{node.path.name}',)
            )
            
            # Add directory label if space permits
            if width > self.min_size_for_label and height > self.min_size_for_label:
                label = f"{node.path.name}\n{node.percentage:.1f}%"
                self.create_text(
                    x + width/2,
                    y + height/2,
                    text=label,
                    anchor='center',
                    font=('Arial', 8)
                )
            
            # Process children
            x += self.border_width
            y += self.border_width
            width -= 2 * self.border_width
            height -= 2 * self.border_width
            
            # Separate files and directories
            dirs = [c for c in node.children if c.is_dir]
            files = [c for c in node.children if not c.is_dir]
            
            # Layout directories
            if dirs:
                if width > height:
                    x_offset = x
                    dir_width = width
                    if files:
                        dir_width = width * sum(d.percentage for d in dirs) / node.percentage
                    for child in dirs:
                        child_width = dir_width * (child.percentage / sum(d.percentage for d in dirs))
                        next_color = (color_idx + 1) % len(self.border_colors)
                        self._draw_treemap(child, x_offset, y, child_width, height, next_color)
                        x_offset += child_width
                    if files:
                        self._draw_files(files, x_offset, y, width - dir_width, height, color_idx, node.path.name)
                else:
                    y_offset = y
                    dir_height = height
                    if files:
                        dir_height = height * sum(d.percentage for d in dirs) / node.percentage
                    for child in dirs:
                        child_height = dir_height * (child.percentage / sum(d.percentage for d in dirs))
                        next_color = (color_idx + 1) % len(self.border_colors)
                        self._draw_treemap(child, x, y_offset, width, child_height, next_color)
                        y_offset += child_height
                    if files:
                        self._draw_files(files, x, y_offset, width, height - dir_height, color_idx, node.path.name)
            elif files:
                self._draw_files(files, x, y, width, height, color_idx, node.path.name)
                
    def _draw_files(self, files: List[FileInfo], x: float, y: float, width: float, height: float, color_idx: int, parent_name: str):
        if width < 1 or height < 1:  # Skip if too small
            return
            
        total_size = sum(f.percentage for f in files)
        if width > height:
            x_offset = x
            for file in files:
                file_width = width * (file.percentage / total_size)
                self._draw_file(file, x_offset, y, file_width, height, color_idx, parent_name)
                x_offset += file_width
        else:
            y_offset = y
            for file in files:
                file_height = height * (file.percentage / total_size)
                self._draw_file(file, x, y_offset, width, file_height, color_idx, parent_name)
                y_offset += file_height
                
    def _draw_file(self, file: FileInfo, x: float, y: float, width: float, height: float, color_idx: int, parent_name: str):
        if width < 1 or height < 1:  # Skip if too small
            return
            
        self.create_rectangle(
            x, y, x + width, y + height,
            fill=self.file_colors[color_idx],
            outline=self.border_colors[color_idx],
            width=1,
            tags=(f'path:{file.path.name}', f'parent:{parent_name}')
        )
        
        if width > self.min_size_for_label and height > self.min_size_for_label:
            label = f"{file.path.name}\n{file.percentage:.1f}%"
            self.create_text(
                x + width/2,
                y + height/2,
                text=label,
                anchor='center',
                font=('Arial', 8)
            )

def main():
    import sys
    
    # Use command line arg if provided, else use current directory
    target_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    
    print(f"\nScanning: {target_path}\n")
    root = traverse_directory(target_path)

    print(f"Root size: {root.size:,} bytes")
    
    print("Calculating percentages...")
    calculate_percentages(root)

    print("Creating GUI window...")
    # Create GUI window
    root_window = tk.Tk()
    root_window.title("Directory Size Treemap")
    root_window.geometry("800x800")

    canvas = TreemapCanvas(root_window, root, bg='white')
    canvas.pack(fill=tk.BOTH, expand=True)

    root_window.mainloop()

if __name__ == "__main__":
    main()
