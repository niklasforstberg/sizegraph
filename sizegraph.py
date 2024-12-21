import tkinter as tk
from tkinter import ttk
from pathlib import Path
import os
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class FileInfo:
    path: Path
    size: int
    percentage: float
    is_dir: bool
    children: List['FileInfo']

class SizeGraph(tk.Tk):
    def __init__(self, root_path: str):
        super().__init__()
        
        self.title("File Size Graph")
        self.geometry("800x600")
        
        # Add protocol handler for window close button
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.files: Dict[str, FileInfo] = {}
        self.scanning = True  # Add flag to track scanning state
        
        self.canvas = tk.Canvas(self, width=780, height=540, bg='white')
        self.canvas.pack(padx=10, pady=(10,5))
        
        self.info_label = tk.Label(
            self, 
            text="Click any rectangle to see file info", 
            wraplength=780,
            justify=tk.LEFT,
            anchor='w',
            padx=10,
            pady=5,
            font=('TkDefaultFont', 12)
        )
        self.info_label.pack(fill=tk.X, expand=True)
        
        # Create and show progress window
        self.progress_window = tk.Toplevel()
        self.progress_window.title("Scanning Files...")
        self.progress_window.geometry("300x150")
        self.progress_window.transient(self)  # Make it float on top of main window
        
        # Center progress window
        self.progress_window.geometry("+%d+%d" % (
            self.winfo_screenwidth()/2 - 150,
            self.winfo_screenheight()/2 - 75))
        
        tk.Label(self.progress_window, text="Scanning files...", pady=10).pack()
        self.progress_var = tk.StringVar(value="Found: 0 files")
        tk.Label(self.progress_window, textvariable=self.progress_var, pady=10).pack()
        
        self.progress_bar = ttk.Progressbar(
            self.progress_window, 
            mode='indeterminate',
            length=200
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()
        
        # Update the UI
        self.progress_window.update()
        
        # Start scanning directly
        self._scan_and_draw(root_path)
    
    def on_closing(self):
        """Handle window close button click"""
        self.scanning = False  # Signal scanning thread to stop
        self.quit()
        self.destroy()
    
    def _scan_and_draw(self, root_path: str):
        """Scan directory and draw graph"""
        file_count = [0]
        
        def update_progress():
            if hasattr(self, 'progress_var'):
                self.progress_var.set(f"Found: {file_count[0]} files")
                self.progress_window.update()
        
        def scan_with_progress(path: Path) -> FileInfo:
            total_size = 0
            children = []
            
            try:
                for item in path.iterdir():
                    try:
                        if item.is_file():
                            size = item.stat().st_size
                            total_size += size
                            children.append(FileInfo(item, size, 0, False, []))
                            file_count[0] += 1
                            if file_count[0] % 100 == 0:
                                update_progress()
                        elif item.is_dir():
                            dir_info = scan_with_progress(item)
                            if dir_info.size > 0:
                                total_size += dir_info.size
                                children.append(dir_info)
                    except (OSError, PermissionError) as e:
                        print(f"Error accessing {item}: {e}")
                        continue
            except (OSError, PermissionError) as e:
                print(f"Error accessing directory {path}: {e}")
                return FileInfo(path, 0, 0, True, [])
            
            children.sort(key=lambda x: x.size, reverse=True)
            
            if total_size > 0:
                for child in children:
                    child.percentage = (child.size / total_size) * 100
                
            return FileInfo(path, total_size, 100, True, children)
        
        # Scan directory
        self.root_item = scan_with_progress(Path(root_path))
        
        # Clean up progress window
        self.progress_window.destroy()
        
        # Draw the graph
        self.draw_graph()
    
    def draw_graph(self) -> None:
        print("Draw graph started")
        
        # Define colors for different file types
        extension_colors = {
            # Images
            '.jpg': '#e24a4a',
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
            if not items or total_size == 0:
                return y
            
            row_sum = sum(item.size for item in items)
            if row_sum == 0:
                return y
            
            row_height = height * row_sum / total_size
            xpos = x
            
            for item in items:
                if item.size == 0:
                    continue
                
                item_width = width * item.size / row_sum
                if item_width < 1:  # Skip too small items
                    continue
                
                if item.is_dir and item.children:
                    draw_rectangle(xpos, y, item_width, row_height, item)
                    layout_treemap(item.children, xpos, y, item_width, row_height)
                else:
                    draw_rectangle(xpos, y, item_width, row_height, item)
                xpos += item_width
            
            return y + row_height
        
        def layout_treemap(items, x, y, width, height):
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
        
        # Start the treemap layout with root's children
        if self.root_item.children:
            layout_treemap(
                sorted(self.root_item.children, key=lambda x: x.size, reverse=True),
                10, 10, 760, 520
            )
        
        print("Draw graph finished")
    
    def show_file_info(self, file_info: FileInfo) -> None:
        size_mb = file_info.size / (1024 * 1024)
        
        # Truncate path if too long
        path_str = str(file_info.path)
        if len(path_str) > 100:
            path_parts = file_info.path.parts
            path_str = f".../{'/'.join(path_parts[-3:])}"  # Show only last 3 parts
        
        info_text = f"Path: {path_str}\nSize: {size_mb:.2f} MB ({file_info.percentage:.1f}%)"
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
