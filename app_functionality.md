 This app is used to scan a folder structure, finding all files and folders, and displaying them in a treemap.
 Folders should be displayed in a rectangle, with a size corresponding to its percentage of the total size. This is calculated in the function calculate_percentages.
 The folders and files are scanned using the function traverse_directory. The result is stored in a treemap of FileInfo objects.
 There is a function print_tree that displays the treemap in a text format.
 A folder has a coloured border, and no coloured background.
 The files in each containing folder have the same corresponding colour as its containing folder.

 We should use three colors for the borders, and three lighter colours for the files. So for folders we use Orange, Blue Brown, and for the files Light orange, Light Blue, Light Brown.
 Folders should alternate between the three colours. For example if a parent folder is red, its child folders should alternate between blue and green.

 The treemap should be interactive. When a file is clicked, the path of the file is displayed in the info label, plus the size of the file in MB or GB depending on it size.

 Folders have no colour. Folders cannot be clicked.
 Display the name of the file in the rectangle, if size permits.

 The colours are:
    for folders:
        ("#fe0f0f"),  # Red
        ("#0000FF"),  # Blue
        ("#22ff3e")   # Green
    for files:
        ("#ff7373"),  # Light red
        ("#CCE5FF"),  # Light blue
        ("#22ff3e")   # Light green

Directory Browser Panel:
- Display a directory tree view panel on the right side of the window
- Similar to Finder/Explorer style navigation
- Allow users to:
  - Expand/collapse folders by clicking arrows/icons
  - Select a folder to analyze by single-clicking
  - Show standard folder icons for visual familiarity
- Update the treemap visualization when a new folder is selected
- When the user clicks on a plus icon, the folder is expanded and the treemap and directory panel is updated to show the contents of the folder.
- When the user clicks on a minus icon, the folder is collapsed and the treemap is updated to show the parent folder.
- Maintain system-native look and feel for consistency
- The user can start a directory traversal scan from the selected folder by clicking the a scan button.

This would improve usability by:
- Providing familiar navigation patterns
- Giving visual context of folder hierarchy
- Enabling quick switching between different folders to analyze
- Removing the need for manual path entry

The app uses PySide6 for the UI.