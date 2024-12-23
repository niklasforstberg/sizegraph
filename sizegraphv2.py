from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import os

@dataclass
class FileInfo:
    path: Path
    size: int = 0
    is_dir: bool = False
    children: List['FileInfo'] = field(default_factory=list)
    parent: Optional['FileInfo'] = field(default=None, repr=False)  # repr=False to avoid circular reference in prints

def traverse_directory(path: Path, parent: Optional[FileInfo] = None) -> FileInfo:
    path_obj = Path(path)
    is_dir = path_obj.is_dir()
    
    info = FileInfo(
        path=path_obj,
        is_dir=is_dir,
        size=path_obj.stat().st_size if not is_dir else 0,
        parent=parent
    )
    
    if is_dir:
        for entry in os.scandir(path):
            info.children.append(traverse_directory(entry.path, parent=info))
        info.size = sum(child.size for child in info.children)
            
    return info

def print_tree(root: FileInfo, indent: str = "", is_last: bool = True, dirs_only: bool = False) -> None:
    # Skip files if dirs_only is True
    if dirs_only and not root.is_dir:
        return
        
    prefix = "└── " if is_last else "├── "
    size_str = f"[{root.size:,} bytes]"
    print(f"{indent}{prefix}{root.path.name} {size_str}")
    
    child_indent = indent + ("    " if is_last else "│   ")
    # Filter children if dirs_only
    children = [c for c in root.children if not dirs_only or c.is_dir]
    for i, child in enumerate(children):
        print_tree(child, child_indent, i == len(children) - 1, dirs_only)

def main():
    import sys
    
    # Use command line arg if provided, else use current directory
    target_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    
    print(f"\nScanning: {target_path}\n")
    root = traverse_directory(target_path)
    print_tree(root)

    print("\nDirectories only:")
    print_tree(root, dirs_only=True)

if __name__ == "__main__":
    main()
