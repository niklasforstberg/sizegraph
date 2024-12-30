from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import os
import sys
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                              QGraphicsScene, QVBoxLayout, QHBoxLayout, QWidget, 
                              QLabel, QTreeView, QPushButton, QFileSystemModel, 
                              QSizePolicy)
from PySide6.QtCore import Qt, QRectF, QDir
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPen
import psutil

@dataclass
class FileInfo:
    path: Path
    size: int = 0
    is_dir: bool = False
    children: List['FileInfo'] = field(default_factory=list)
    parent: Optional['FileInfo'] = field(default=None, repr=False)
    percentage: float = 0.0

def traverse_directory(path: Path, parent: Optional[FileInfo] = None, 
                      counter: list = None, 
                      progress_callback = None) -> FileInfo:
    # Initialize counter on first call
    if counter is None:
        counter = [0]
    
    counter[0] += 1
    if counter[0] % 5000 == 0: 
        print(f"Scanned {counter[0]} files") 
        process = psutil.Process()
        mem_usage = process.memory_info().rss / 1024 / 1024
        if progress_callback:
            progress_callback(counter[0], mem_usage)
    
    path_obj = Path(path)
    is_dir = os.path.isdir(path)
    
    try:
        size = os.stat(path).st_size if not is_dir else 0
    except (PermissionError, OSError):
        return FileInfo(path=path_obj, size=0, is_dir=is_dir, parent=parent)
    
    obj = FileInfo(path=path_obj, is_dir=is_dir, size=size, parent=parent)
    
    if is_dir:
        try:
            entries = list(os.scandir(path))
            obj.children = [None] * len(entries)
            obj.children = [traverse_directory(entry.path, parent=obj, counter=counter, progress_callback=progress_callback) for entry in entries]
            obj.size = sum(child.size for child in obj.children)
        except (PermissionError, OSError):
            pass
            
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
        # Avoid division by zero
        if total_size > 0:
            node.percentage = (node.size / total_size) * 100
        else:
            node.percentage = 0.0
            
        if node.is_dir:
            for child in node.children:
                _calc_percentage(child)
    
    # Add percentage field to FileInfo class first
    FileInfo.percentage = field(default=0.0)
    
    # Start calculation from root
    _calc_percentage(root)

class TreemapView(QGraphicsView):
    def __init__(self, root_info: FileInfo):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.root_info = root_info
        
        # Define colors for files and folder borders
        self.border_colors = [
            QColor("#fe0f0f"),  # Red
            QColor("#0000FF"),  # Blue
            QColor("#22ff3e")   # Green
        ]
        self.file_colors = [
            QColor("#ff7373"),  # Light red
            QColor("#CCE5FF"),  # Light blue
            QColor("#22ff3e")   # Light green
        ]
        
        # Create info label with fixed height and expanding width
        self.info_label = QLabel("")
        self.info_label.setMinimumWidth(self.window().width())
        self.info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.draw_treemap()
        
        # Enable viewport update on resize
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Fit scene in viewport
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.draw_treemap()
        
    def draw_treemap(self):
        self.scene.clear()
        rect = self.viewport().rect()
        self._draw_item(self.root_info, QRectF(0, 0, rect.width(), rect.height()), 0)
        self.setSceneRect(self.scene.itemsBoundingRect())
        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def _draw_item(self, item: FileInfo, rect: QRectF, depth: int) -> None:
        if rect.width() < 1 or rect.height() < 1:
            return

        # For root folder, start with first color
        if not item.parent:
            color_index = 0
        # For files, use parent's color
        elif not item.is_dir:
            color_index = self._get_folder_color_index(item.parent)
        # For folders, alternate between colors not used by parent
        else:
            parent_color = self._get_folder_color_index(item.parent)
            available_colors = [i for i in range(len(self.border_colors)) if i != parent_color]
            sibling_index = sum(1 for sibling in item.parent.children[:item.parent.children.index(item)] if sibling.is_dir)
            color_index = available_colors[sibling_index % len(available_colors)]

        if item.is_dir:
            # Draw directory with transparent background and colored border
            rect_item = self.scene.addRect(
                rect,
                QPen(self.border_colors[color_index]),
                QBrush(Qt.transparent)
            )
            self._layout_children(item, rect, depth + 1)
        else:
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            base_color = self.file_colors[color_index]
            darker = base_color.darker(150)
            lighter = base_color.lighter(150)
            
            gradient.setColorAt(0.5, lighter)
            gradient.setColorAt(0, base_color)
            gradient.setColorAt(1, darker)
            
            rect_item = self.scene.addRect(
                rect,
                QPen(Qt.transparent),
                QBrush(gradient)
            )
            
            rect_item.setAcceptHoverEvents(True)
            rect_item.setData(0, item)

    def _layout_children(self, dir_item: FileInfo, rect: QRectF, depth: int):
        if not dir_item.children:
            return
            
        x, y = rect.x(), rect.y()
        width, height = rect.width(), rect.height()
        
        # Use all children (both files and directories)
        total_size = sum(child.size for child in dir_item.children)
        
        if width > height:
            x_offset = x
            for child in dir_item.children:
                child_width = width * (child.size / total_size)
                self._draw_item(child, QRectF(x_offset, y, child_width, height), depth)
                x_offset += child_width
        else:
            y_offset = y
            for child in dir_item.children:
                child_height = height * (child.size / total_size)
                self._draw_item(child, QRectF(x, y_offset, width, child_height), depth)
                y_offset += child_height

    def mousePressEvent(self, event):
        item = self.scene.itemAt(self.mapToScene(event.position().toPoint()), self.transform())
        if item:
            file_info = item.data(0)
            if file_info:
                size_str = self._format_size(file_info.size)
                # Elide the path if it's too long
                path_str = str(file_info.path)
                if len(path_str) > 100:  # Adjust this value as needed
                    path_str = path_str[:50] + "..." + path_str[-47:]
                self.info_label.setText(f"{path_str} ({size_str})")
        super().mousePressEvent(event)

    def _format_size(self, size: int) -> str:
        if size >= 1_000_000_000:
            return f"{size/1_000_000_000:.2f} GB"
        return f"{size/1_000_000:.2f} MB"

    def _get_folder_color_index(self, folder: FileInfo) -> int:
        if not folder.parent:
            return 0
        parent_color = self._get_folder_color_index(folder.parent)
        available_colors = [i for i in range(len(self.border_colors)) if i != parent_color]
        sibling_index = sum(1 for sibling in folder.parent.children[:folder.parent.children.index(folder)] if sibling.is_dir)
        return available_colors[sibling_index % len(available_colors)]

class DirectoryBrowser(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        # Add scan button at the top
        self.scan_button = QPushButton("Scan Selected Folder")
        layout.addWidget(self.scan_button)
        
        # Create tree view
        self.tree_view = QTreeView()
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        
        # Set model filters
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(QDir.rootPath()))
        
        # Hide all columns except the name column
        for i in range(1, self.model.columnCount()):
            self.tree_view.hideColumn(i)
            
        layout.addWidget(self.tree_view)

class MainWindow(QMainWindow):
    def __init__(self, root_info: FileInfo):
        super().__init__()
        self.setWindowTitle("Directory Size Treemap")
        
        # Create main central widget with vertical layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)  # Add small margins
        
        # Add info label at the top, stretching full width
        self.treemap_view = TreemapView(root_info)
        main_layout.addWidget(self.treemap_view.info_label)
        
        # Create horizontal container for treemap and directory browser
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)  # Remove internal margins
        
        # Add treemap (without its info label)
        content_layout.addWidget(self.treemap_view, stretch=2)
        
        # Add directory browser
        self.dir_browser = DirectoryBrowser()
        self.dir_browser.scan_button.clicked.connect(self.on_scan_clicked)
        self.dir_browser.tree_view.clicked.connect(self.on_directory_selected)
        content_layout.addWidget(self.dir_browser, stretch=1)
        
        # Add the content widget to main layout
        main_layout.addWidget(content_widget)
        
        self.setCentralWidget(central_widget)

        # Get screen size and set window to maximum
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)

        # Add status bar
        self.status_bar = self.statusBar()
        self.size_label = QLabel()
        self.count_label = QLabel()
        self.progress_label = QLabel()
        self.status_bar.addWidget(self.size_label)
        self.status_bar.addWidget(self.count_label)
        self.status_bar.addWidget(self.progress_label)
        self.update_status_info(root_info)

    def update_status_info(self, root: FileInfo):
        # Calculate total files and folders
        file_count = 0
        folder_count = 0
        
        def count_items(node: FileInfo):
            nonlocal file_count, folder_count
            if node.is_dir:
                folder_count += 1
                for child in node.children:
                    count_items(child)
            else:
                file_count += 1
        
        count_items(root)
        
        # Format size
        total_size = self._format_size(root.size)
        self.size_label.setText(f"Total Size: {total_size}")
        self.count_label.setText(f"Files: {file_count:,} | Folders: {folder_count:,}")

    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def scan_selected_directory(self):
        index = self.dir_browser.tree_view.currentIndex()
        if index.isValid():
            print("Starting scan...")  # Debug
            
            def progress_callback(files_scanned: int, memory_mb: float):
                print(f"Progress callback: {files_scanned} files")  # Debug
                self.progress_label.setText(
                    f"Scanning... Files: {files_scanned:,} | Memory: {memory_mb:.1f} MB"
                )
                self.status_bar.update()
                QApplication.processEvents()
            
            path = Path(self.dir_browser.model.filePath(index))
            root = traverse_directory(path, counter=[0], progress_callback=progress_callback)
            print("Scan complete")  # Debug
            calculate_percentages(root)
            self.treemap_view.root_info = root
            self.treemap_view.draw_treemap()
            self.update_status_info(root)
            self.progress_label.clear()
            self.status_bar.update()  # Update one final time

    def on_directory_selected(self, index):
        self.dir_browser.scan_button.setEnabled(index.isValid())

    def on_scan_clicked(self):
        # Clear info label before starting scan
        self.treemap_view.info_label.setText("")
        self.scan_selected_directory()

def main():
    app = QApplication(sys.argv)
    # Create window with empty root (or minimal placeholder)
    window = MainWindow(FileInfo(path=Path.home()))
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
