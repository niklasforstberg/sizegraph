import tkinter as tk
from tkinter import ttk
from pathlib import Path
import os
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class FileInfo:
    # Data structure to hold file/directory information
    path: Path      # Full path to the file/directory
    size: int       # Size in bytes
    is_dir: bool    # True if directory, False if file
    children: List['FileInfo']  # List of contained files/dirs (empty for files)

class SizeGraph(tk.Tk):
    def __init__(self, root_path: str):
        # Main window initialization
        super().__init__()
        
        self.title("File Size Graph")
        self.geometry("800x600")
        
        # Add protocol handler for window close button
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.files: Dict[str, FileInfo] = {}
        self.scanning = True
        
        self.canvas = tk.Canvas(self, width=780, height=540, bg='white')
        self.canvas.pack(padx=10, pady=(10,5))
        
        self.info_label = tk.Label(
            self, 
            text="This will probably take a while...", 
            wraplength=780,
            justify=tk.LEFT,
            anchor='w',
            padx=10,
            pady=5,
            font=('TkDefaultFont', 12)
        )
        self.info_label.pack(fill=tk.X, expand=True)
        
        # Schedule the scan to start after the window is shown
        self.after(100, lambda: self.start_scan(root_path))
        
        # Add these new instance variables
        self.total_files_scanned = 0
        self.total_size_scanned = 0
    
    def start_scan(self, root_path: str):
        """Initialize scanning process"""
        print(f"\nStarting scan of: {root_path}")
        
        # Create and configure progress window
        self.progress_window = tk.Toplevel(self)
        self.progress_window.title("Scanning Files...")
        self.progress_window.geometry("300x150")  # Reduced from 200 to 150
        self.progress_window.transient(self)
        
        # Center progress window
        self.progress_window.geometry("+%d+%d" % (
            self.winfo_screenwidth()//2 - 150,
            self.winfo_screenheight()//2 - 75))  # Adjusted center point
        
        # Main scanning label
        tk.Label(self.progress_window, text="Scanning files...", pady=10).pack()
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_window, 
            mode='indeterminate',
            length=200
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar.start(10)
        
        # Add file count and total size labels
        self.files_label = tk.Label(self.progress_window, text="Files scanned: 0")
        self.files_label.pack(pady=5)
        
        self.size_label = tk.Label(self.progress_window, text="Total size: 0 MB")
        self.size_label.pack(pady=5)
        
        print("Progress window created, starting scan...")
        
        # Initialize scan queue with root path
        self.total_files_scanned = 0
        self.total_size_scanned = 0
        self.scan_queue = [(Path(root_path), None)]
        self.process_scan_queue()
    
    def process_scan_queue(self):
        """Process files in chunks to keep UI responsive"""
        if not self.scanning or not self.scan_queue:
            print("\nScan queue empty or scanning stopped, finishing up...")
            # Calculate final sizes for all directories
            def recalculate_dir_size(item: FileInfo) -> int:
                if not item.is_dir:
                    return item.size
                total = sum(recalculate_dir_size(child) for child in item.children)
                item.size = total
                return total
            
            if hasattr(self, 'root_item'):
                self.root_item.size = recalculate_dir_size(self.root_item)
            self.finish_scan()
            return
        
        current_path, parent = self.scan_queue.pop(0)
        children = []
        
        try:
            for item in current_path.iterdir():
                try:
                    if item.is_file():
                        size = item.stat().st_size
                        self.total_size_scanned += size
                        children.append(FileInfo(item, size, False, []))
                        self.total_files_scanned += 1
                        
                        if self.total_files_scanned % 100 == 0:
                            self.files_label.config(text=f"Files scanned: {self.total_files_scanned:,}")
                            self.size_label.config(text=f"Total size: {self.total_size_scanned/1024/1024:.1f} MB")
                            self.progress_window.update()
                    elif item.is_dir():
                        self.scan_queue.append((item, children))
                except (OSError, PermissionError) as e:
                    print(f"Error accessing {item}: {e}")
        except (OSError, PermissionError) as e:
            print(f"Error accessing directory {current_path}: {e}")
        
        if parent is not None:
            file_info = FileInfo(current_path, 0, True, children)  # Size will be calculated at the end
            parent.append(file_info)
        else:
            self.root_item = FileInfo(current_path, 0, True, children)  # Size will be calculated at the end
        
        self.after(1, self.process_scan_queue)
    
    def finish_scan(self):
        """Clean up after scanning is complete"""
        print("\nScanning complete!")
        if hasattr(self, 'progress_window'):
            print("Closing progress window...")
            self.progress_window.destroy()
        self.info_label.config(text="")  # Clear the text after scan completes
        print("Starting to draw graph...")
        self.draw_graph()
    
    def on_closing(self):
        """Handle window close button click"""
        self.scanning = False
        self.quit()
        self.destroy()
    
    def draw_graph(self) -> None:
        """Draw the treemap visualization"""
        
        # Color mapping for different file types
        extension_colors = {
            # Colors grouped by file category
            '.jpg': '#e24a4a',  # Red for images
            '.jpeg': '#e24a4a',
            '.png': '#e24a4a',
            '.gif': '#e24a4a',
            
            # Documents
            '.pdf': '#4a90e2',
            '.doc': '#4a90e2',
            '.docx': '#4a90e2',
            '.txt': '#4a90e2',
            '.md': '#4a90e2',
            
            # Code
            '.py': '#4ae24a',
            '.js': '#4ae24a',
            '.html': '#4ae24a',
            '.css': '#4ae24a',
            
            # Archives
            '.zip': '#e2e24a',
            '.rar': '#e2e24a',
            '.gz': '#e2e24a',
        }
        
        # Clear previous drawing
        self.canvas.delete("all")
        
        def get_color(item: FileInfo) -> str:
            if item.is_dir:
                return '#666666'
            return extension_colors.get(item.path.suffix.lower(), '#808080')
        
        def draw_rectangle(x, y, width, height, item: FileInfo):
            if width < 2 or height < 2:
                return
            
            color = get_color(item)
            
            rect_id = self.canvas.create_rectangle(
                x, y, x + width, y + height,
                fill=color, outline='white', width=1
            )
            
            if width > 50 and height > 20:
                self.canvas.create_text(
                    x + 5, y + height/2,
                    text=item.path.name,
                    anchor='w',
                    fill='white',
                    font=('TkDefaultFont', 8)
                )
            
            self.canvas.tag_bind(rect_id, '<Button-1>', 
                               lambda e, f=item: self.show_file_info(f))
        
        def worst_ratio(row, width, height, total_size):
            """Calculate the worst aspect ratio for a row of rectangles
            Used in the squarified treemap algorithm to optimize rectangle shapes"""
            if not row or total_size == 0:
                return float('inf')
            
            row_sum = sum(item.size for item in row)
            if row_sum == 0:
                return float('inf')
            
            row_width = width * row_sum / total_size
            row_height = height
            max_ratio = 0
            
            for item in row:
                if item.size == 0:
                    continue
                
                item_width = row_width * item.size / row_sum
                if item_width == 0:
                    continue
                
                ratio = max(item_width / row_height, row_height / item_width)
                max_ratio = max(max_ratio, ratio)
            
            return max_ratio if max_ratio > 0 else float('inf')
        
        def layout_row(items, x, y, width, height, total_size):
            """Layout a single row of rectangles in the treemap
            Handles grouping of small items and recursive layout of directories"""
            if not items or total_size == 0:
                return y
            
            row_sum = sum(item.size for item in items)
            if row_sum == 0:
                return y
            
            row_height = height * row_sum / total_size
            xpos = x
            
            # Group very small items
            small_items_size = 0
            visible_items = []
            
            for item in items:
                item_width = width * item.size / row_sum
                if item_width < 1:  # Too small to display individually
                    small_items_size += item.size
                else:
                    visible_items.append(item)
            
            # If we have small items, create a combined rectangle
            if small_items_size > 0:
                combined_width = width * small_items_size / row_sum
                if combined_width >= 1:
                    draw_rectangle(xpos, y, combined_width, row_height, 
                                 FileInfo(Path("Small Files"), small_items_size, False, []))
                    xpos += combined_width
            
            # Draw remaining items
            for item in visible_items:
                item_width = width * item.size / row_sum
                if item.is_dir and item.children:
                    draw_rectangle(xpos, y, item_width, row_height, item)
                    layout_treemap(item.children, xpos, y, item_width, row_height)
                else:
                    draw_rectangle(xpos, y, item_width, row_height, item)
                xpos += item_width
            
            return y + row_height
        
        def layout_treemap(items, x, y, width, height):
            """Main treemap layout algorithm using the squarified treemap approach
            Tries to maintain aspect ratios close to 1 for better visualization"""
            if not items:
                return
            
            total_size = sum(item.size for item in items)
            if total_size == 0:
                return
            
            row = []
            best_ratio = float('inf')
            i = 0
            
            while i < len(items):
                row.append(items[i])
                ratio = worst_ratio(row, width, height, total_size)
                
                if ratio > best_ratio:
                    row.pop()
                    y = layout_row(row, x, y, width, height, total_size)
                    row = [items[i]]
                    best_ratio = float('inf')
                else:
                    best_ratio = ratio
                i += 1
            
            if row:
                y = layout_row(row, x, y, width, height, total_size)
        
        # Start layout with sorted children (largest first)
        if self.root_item.children:
            layout_treemap(
                sorted(self.root_item.children, key=lambda x: x.size, reverse=True),
                10, 10, 760, 520
            )
        
        print("Draw graph finished")
    
    def show_file_info(self, file_info: FileInfo) -> None:
        size_mb = file_info.size / (1024 * 1024)
        # Calculate percentage relative to root item
        percentage = (file_info.size / self.root_item.size * 100) if self.root_item.size > 0 else 0
        
        path_str = str(file_info.path)
        if len(path_str) > 100:
            path_parts = file_info.path.parts
            path_str = f".../{'/'.join(path_parts[-3:])}"
        
        info_text = f"Path: {path_str}\nSize: {size_mb:.2f} MB ({percentage:.1f}%)"
        self.info_label.config(text=info_text)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    from tkinter import filedialog
    
    # Open folder selection dialog
    root_path = filedialog.askdirectory(
        title='Select Folder to Analyze',
        initialdir='.'  # Start in current directory
    )
    
    if root_path:  # Only create app if user selected a folder
        app = SizeGraph(root_path)
        app.mainloop()
    else:
        print("No folder selected. Exiting.")
