# AppData Migration Tool

![Windows](https://img.shields.io/badge/Platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.7%2B-green)

## Features

✅ Automated AppData directory migration
✅ Automatic file lock handling
✅ Symbolic links for backward compatibility
✅ Automatic administrator privilege escalation
✅ Supports Local/LocalLow/Roaming directories

## Requirements
- Windows 10/11

## Quick Start
1. download the latest release executable from the right side
2. double-click to run

## Requirements For Building
- Python 3.7+
- Poetry 1.2+

## Run from Source
```powershell
# Clone repository
git clone https://github.com/huwei901108/AppDataMove.git

# Install dependencies
cd AppDataMove
poetry install

# Run application
./run.bat
```

## Build Standalone Executable

```powershell
./build.bat
# Built executable will be in dist directory
```

## Usage Instructions

1. Program will prompt for target AppData path
2. Path format validation:
   - Must match `C:\Users\<Username>\AppData\<Local|LocalLow|Roaming>\<subdirectory>`
3. After confirmation:
   - Automatically close file-locking processes
   - Migrate data to D: drive
   - Create symbolic links for compatibility

⚠️ Important:
- Requires administrator privileges
- Close related applications before migration
- Recommend backup important data first

## Technical Implementation

- Windows API for privilege detection
- Sysinternals tools integration for file handling
- Reliable file operations with shutil
- System compatibility via symbolic links

## License

[MIT License](LICENSE)