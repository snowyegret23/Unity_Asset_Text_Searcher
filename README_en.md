[한국어](README.md) | **English**

# Unity Asset Text Searcher

A tool for searching text in Unity game asset files and DLL files.

## Features

- **Unity Asset Search**: Search text in TextAsset, MonoBehaviour, etc.
- **DLL Search**: Search string literals in .NET DLL files (using Mono.Cecil)
- **Auto Unity Version Detection**: Automatically extract Unity version from globalgamemanagers file
- **Multiple Output Formats**: TXT summary + CSV detailed results

## Installation

### Download Release
Download the latest version from the [Releases](../../releases) page.

### Run Directly (Python)
```bash
pip install UnityPy pythonnet
python Unity_searcher.py
```

## Usage

### Basic Usage
1. Copy `Unity_Searcher.exe` to the game's root folder or `_Data` folder
2. Copy `Mono.Cecil.dll` to the same location (required for DLL search)
3. Run and enter the text to search

### Command Line Options
```
Unity_searcher.py [-h] [-v UNITY_VERSION] [-s SEARCH] [-d DIRECTORY] [--no-dll]

Options:
  -h, --help            Show help message
  -v, --unity-version   Specify Unity version (e.g., -v "2022.3.15f1")
  -s, --search          Text to search (prompts if not specified)
  -d, --directory       Search directory (default: current directory, game root or _Data folder)
  --no-dll              Skip DLL searching
```

### Examples
```bash
# Basic execution (interactive)
Unity_Searcher.exe

# Specify search text and directory
Unity_Searcher.exe -s "Hello World" -d "C:\Games\MyGame\MyGame_Data"

# Manually specify Unity version
Unity_Searcher.exe -v "2021.3.0f1" -s "search term"

# Exclude DLL search
Unity_Searcher.exe -s "text" --no-dll
```

## Output Files

The following files are generated after search completion:

| File | Description |
|------|-------------|
| `output_[search_term].txt` | Search result summary (TXT) |
| `output_assets_[search_term].csv` | Asset search results (CSV) |
| `output_dll_[search_term].csv` | DLL search results (CSV) |

### CSV Format

**Asset Results (output_assets_*.csv)**
| Column | Description |
|--------|-------------|
| file_path | File path |
| assets_name | Asset name |
| path_id | Path ID |
| type_name | Object type |
| obj_name | Object name |

**DLL Results (output_dll_*.csv)**
| Column | Description |
|--------|-------------|
| file_path | File path |
| class_name | Class name |
| method_name | Method name |
| text | Found text |

## Requirements

### Executable (exe)
- Windows 10/11
- `Mono.Cecil.dll` (required for DLL search feature)

### Python Direct Execution
- Python 3.8+
- UnityPy
- pythonnet (for Mono.Cecil)

## Notes

- If Unity version auto-detection fails, manually specify it with the `-v` option
- DLL search feature is disabled if `Mono.Cecil.dll` is not found
- Searching large games may take some time

## License

MIT License

## Credits

- Made by **Snowyegret**
- [UnityPy](https://github.com/K0lb3/UnityPy) - Unity asset parsing
- [Mono.Cecil](https://github.com/jbevain/cecil) - .NET DLL analysis
