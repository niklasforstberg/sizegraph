from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import os
import sys
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                              QGraphicsScene, QVBoxLayout, QWidget, QLabel)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPen

@dataclass
class FileInfo:
    path: Path
    size: int = 0
    is_dir: bool = False
    children: List['FileInfo'] = field(default_factory=list)
    parent: Optional['FileInfo'] = field(default=None, repr=False)
    percentage: float = 0.0

def traverse_directory(path: Path, parent: Optional[FileInfo] = None, counter: list = None) -> FileInfo:
    # Initialize counter on first call
    if counter is None:
        counter = [0]
    
    counter[0] += 1
    if counter[0] % 10000 == 0:
        print(f"Files scanned: {counter[0]:,}", flush=True)
    
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
            obj.children = [traverse_directory(entry.path, parent=obj, counter=counter) for entry in entries]
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
        
        self.info_label = QLabel("Click a file to see details")
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
        # For direct children of root, alternate between remaining colors
        elif not item.parent.parent:
            color_index = 1 + (item.parent.children.index(item) % 2)
        # For all other folders, use parent's color
        else:
            parent_index = item.parent.children.index(item)
            color_index = (parent_index % len(self.border_colors))
        
        if item.is_dir:
            # Draw directory with transparent background and colored border
            rect_item = self.scene.addRect(
                rect,
                QPen(self.border_colors[color_index]),
                QBrush(Qt.transparent)
            )
            
            if rect.width() > 40 and rect.height() > 20:
                text = self.scene.addText(
                    f"{item.path.name}\n{item.percentage:.1f}%"
                )
                text.setDefaultTextColor(Qt.black)
                text.setPos(
                    rect.x() + (rect.width() - text.boundingRect().width()) / 2,
                    rect.y() + (rect.height() - text.boundingRect().height()) / 2
                )
            
            self._layout_children(item, rect, depth + 1)
        else:
            # Files should use their parent folder's color
            if item.parent:
                # Get parent's color index using same logic as above
                if not item.parent.parent:
                    color_index = 0  # Parent is root
                elif not item.parent.parent.parent:
                    color_index = 1 + (item.parent.parent.children.index(item.parent) % 2)
                else:
                    parent_index = item.parent.parent.children.index(item.parent)
                    color_index = (parent_index % len(self.border_colors))
            
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            base_color = self.file_colors[color_index]
            darker = base_color.darker(150)
            lighter = base_color.lighter(150)
            
            gradient.setColorAt(0, lighter)
            gradient.setColorAt(0.5, base_color)
            gradient.setColorAt(1, darker)
            
            rect_item = self.scene.addRect(
                rect,
                QPen(Qt.transparent),
                QBrush(gradient)
            )
            
            rect_item.setAcceptHoverEvents(True)
            rect_item.setData(0, item)
            
            if rect.width() > 40 and rect.height() > 20:
                text = self.scene.addText(
                    f"{item.path.name}\n{item.percentage:.1f}%"
                )
                text.setDefaultTextColor(Qt.black)
                text.setPos(
                    rect.x() + (rect.width() - text.boundingRect().width()) / 2,
                    rect.y() + (rect.height() - text.boundingRect().height()) / 2
                )

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
        item = self.scene.itemAt(self.mapToScene(event.pos()), self.transform())
        if item:
            file_info = item.data(0)
            if file_info:
                size_str = self._format_size(file_info.size)
                self.info_label.setText(f"{file_info.path} ({size_str})")
        super().mousePressEvent(event)

    def _format_size(self, size: int) -> str:
        if size >= 1_000_000_000:
            return f"{size/1_000_000_000:.2f} GB"
        return f"{size/1_000_000:.2f} MB"

class MainWindow(QMainWindow):
    def __init__(self, root_info: FileInfo):
        super().__init__()
        self.setWindowTitle("Directory Size Treemap")
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.treemap_view = TreemapView(root_info)
        
        layout.addWidget(self.treemap_view.info_label)
        layout.addWidget(self.treemap_view)
        
        self.setCentralWidget(central_widget)
        self.resize(800, 800)

def main():
    import time
    start_time = time.time()

    target_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    absolute_path = target_path.resolve().absolute()
    print(f"\nScanning: {absolute_path}\n")
    root = traverse_directory(absolute_path)
    print(f"Root size: {root.size:,} bytes")
    
    print("Calculating percentages...")
    calculate_percentages(root)

    print_tree(root, dirs_only=True)
    
    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.2f} seconds")
    
    print("Creating GUI window...")
    app = QApplication(sys.argv)
    window = MainWindow(root)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
