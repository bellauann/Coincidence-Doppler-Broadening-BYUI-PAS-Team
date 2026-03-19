# evt2bin - Event File Binary Converter

A high-performance C++ utility that converts large text event data files to a compact binary format with intelligent sorting and compression.

## Overview

`evt2bin` is designed to efficiently handle massive event logs by converting them from text to a space-optimized binary format. It automatically chooses the best sorting strategy based on available memory and dataset size, making it suitable for processing gigabytes of event data.

---

## Download & Setup (Pre-compiled Binaries)

No compilation needed — just download the right binary for your platform from the [Releases page](https://github.com/bellauann/Coincidence-Doppler-Broadening-BYUI-PAS-Team/releases/) and follow the steps below.

| File | Platform |
|---|---|
| `evt2bin-linux-x64` | Linux (64-bit) |
| `evt2bin-macos-x64` | macOS — Intel (x86_64) |
| `evt2bin-macos-arm64` | macOS — Apple Silicon (M1/M2/M3) |
| `evt2bin-windows-x64.exe` | Windows (64-bit) |

---

### macOS (Intel & Apple Silicon)

**Step 1: Remove the quarantine flag**

macOS blocks binaries downloaded from the internet by default. Run this or it will refuse to open:
```bash
xattr -d com.apple.quarantine evt2bin-macos-arm64
```
*(Replace `arm64` with `x64` if you're on an Intel Mac)*

**Step 2: Make it executable**
```bash
chmod +x evt2bin-macos-arm64
```

**Step 3: Run it**
```bash
./evt2bin-macos-arm64 input.txt output.bin
```

**Optional — Add to PATH so you can run it from anywhere**
```bash
sudo mv evt2bin-macos-arm64 /usr/local/bin/evt2bin
```
Then from any folder:
```bash
evt2bin input.txt output.bin
```

---

### Windows

**Step 1: Download `evt2bin-windows-x64.exe`**

**Step 2: Run it**

Open Command Prompt or PowerShell, navigate to your download folder, and run:
```cmd
.\evt2bin-windows-x64.exe input.txt output.bin
```

> **SmartScreen popup:** If Windows says "Windows protected your PC", click **More info** then **Run anyway**. This happens because the binary isn't signed with a paid certificate — it is safe to run.

**Optional — Add to PATH so you can run it from anywhere**

1. Move `evt2bin-windows-x64.exe` to a permanent folder, e.g. `C:\Tools\`
2. Rename it to `evt2bin.exe` for shorter commands
3. Add that folder to your PATH:
   - Search **"environment variables"** in the Start menu
   - Click **"Edit the system environment variables"**
   - Click **"Environment Variables"**
   - Under "System variables" find **Path** and click **Edit**
   - Click **New** and type `C:\Tools\`
   - Click OK on all windows
4. Open a **new** Command Prompt window and run from anywhere:
```cmd
evt2bin input.txt output.bin
```

---

### Linux

**Step 1: Make it executable**
```bash
chmod +x evt2bin-linux-x64
```

**Step 2: Run it**
```bash
./evt2bin-linux-x64 input.txt output.bin
```

> **glibc error?** If you see `version 'GLIBC_2.3x' not found`, your distro is too old for the pre-compiled binary. See the [Building from Source](#building-from-source) section below.

**Optional — Add to PATH so you can run it from anywhere**
```bash
sudo mv evt2bin-linux-x64 /usr/local/bin/evt2bin
```
Then from any folder:
```bash
evt2bin input.txt output.bin
```

---

## Usage

```bash
evt2bin <input.txt> <output.bin> [options]
```

### Options

- `--delete-input` — Delete the input text file after successful conversion
- `--chunk-mb N` — Set memory limit per sort chunk in MB (default: auto-detect based on available RAM × 0.8, fallback 512 MB)

### Examples

```bash
# Basic conversion
evt2bin events.txt events.bin

# Convert and delete input file
evt2bin events.txt events.bin --delete-input

# Specify custom memory chunk size
evt2bin events.txt events.bin --chunk-mb 256
```

---

## Converting Binary Back to CSV

Use `bin2csv.py` to decompress and convert binary files back to CSV format:

```bash
python3 bin2csv.py events.bin events.csv
```

The CSV will have columns: `timestamp,channel,filter`

> **Note:** `bin2csv.py` requires only Python 3 — no compilation needed. It automatically handles column-oriented compressed format (EVTCOL v2) and legacy interleaved format (EVTBIN v1).

---

## Building from Source

If the pre-compiled binary doesn't work on your system, you can build from source.

### Prerequisites
The only thing you need is a C++ compiler and the zlib library (both come standard on macOS).

### Compile

```bash
make
```

The binary will be built into `bin/evt2bin` (or `bin/evt2bin.exe` on Windows).

## Platform Setup

### macOS
Nothing needed — zlib ships with Xcode tools. Just run `make`.

### Linux (Debian/Ubuntu)
```bash
sudo apt install g++ zlib1g-dev make
make
```

### Linux (Fedora/RHEL)
```bash
sudo dnf install gcc-c++ zlib-devel make
make
```

### Windows (Option 1: MSYS2/MinGW)

**Step 1: Download and install MSYS2**
1. Go to https://www.msys2.org/
2. Download the MSYS2 installer (msys2-x86_64-*.exe)
3. Run the installer and follow the setup wizard (default installation is fine)
4. After installation, launch **MSYS2 MinGW 64-bit** from the Windows Start menu (NOT "MSYS2 MSYS")
   - This opens a terminal-like window

**Step 2: Install build tools**
In the MSYS2 terminal, run:
```bash
pacman -S --needed mingw-w64-x86_64-gcc mingw-w64-x86_64-zlib make
```
When prompted, press `y` to confirm installation.

**Step 3: Build evt2bin**
Navigate to the project folder and build (in MSYS2 terminal):
```bash
cd /c/path/to/your/project/txt-to-binary
make
```
The compiled binary will be in `bin/evt2bin.exe`.

**Step 4: Run evt2bin**
Once built, you can run `evt2bin.exe` from:
- **MSYS2 terminal:** `./bin/evt2bin events.txt events.bin`
- **Windows Command Prompt/PowerShell:** `bin\evt2bin.exe events.txt events.bin`
- **Windows Explorer:** Double-click `evt2bin.exe` (drag event files onto it)

The build step **only** needs MSYS2, but the compiled binary runs anywhere on Windows.

---

### Windows (Option 2: WSL - Windows Subsystem for Linux)

WSL lets you run Linux directly on Windows. This is often simpler if you're comfortable with Linux.

**Step 1: Enable WSL**
1. Open PowerShell as Administrator
2. Run:
   ```powershell
   wsl --install --distribution Ubuntu
   ```
3. Restart your computer
4. After restart, open the Ubuntu app from the Start menu and wait for setup to complete

**Step 2: Install dependencies**
In the Ubuntu terminal:
```bash
sudo apt update
sudo apt install g++ zlib1g-dev make
```

**Step 3: Build evt2bin**
Navigate to the project and build:
```bash
cd /mnt/c/path/to/your/project/txt-to-binary
make
```

**Step 4: Use evt2bin**
```bash
./bin/evt2bin events.txt events.bin
```

---

### Windows (Option 3: Native MSVC)

If you have Visual Studio 2017 or later installed:

**Step 1: Install dependencies**
- zlib is available through vcpkg (Microsoft's package manager for C++)
- Or pre-compiled zlib binaries from https://github.com/madler/zlib/releases

**Step 2: Modify Makefile**
The current Makefile uses GCC syntax. You'll need to either:
- Use a GCC-compatible environment (Options 1 or 2 above are recommended)
- Or compile manually with MSVC (requires adjusting compiler flags)

**Recommendation:** Start with **Option 1 (MSYS2)** — it's the most straightforward and requires no additional software beyond the MSYS2 installer.

## Build Options

```bash
make              # Standard build (requires system zlib at runtime)
make static       # Self-contained binary (no dependencies on target machine)
make clean        # Remove compiled files and bin/ folder
make help         # Show all options
```

---

## Distributing a Pre-compiled Binary

### Option A: Use GitHub Actions for Automatic Builds (Recommended)

GitHub Actions automatically builds your code for Windows, macOS, and Linux whenever you create a release. Users just download the `.exe` (or binary for their platform) and run it.

**Setup (one-time):**

1. Ensure the `.github/workflows/build.yml` file is committed to your repository
2. Make sure your `Makefile` has the `static` target (it already does)
3. Commit and push to GitHub

**Creating a release:**

```bash
# Tag your code
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions will automatically:
1. Build `evt2bin` for Windows, macOS, and Linux
2. Create a GitHub release
3. Attach the compiled binaries as downloadable assets

Users can then download the binary from your GitHub "Releases" page without any compilation needed.

---

### Option B: Build Once Manually and Share

Build the binary once on a Windows machine (takes 2 minutes with MSYS2), then upload `bin/evt2bin.exe` to a GitHub release. Users download and run directly.

---

**For now:** You can use either approach. GitHub Actions (Option A) is more maintainable long-term, but if you just want something working quickly, build once on Windows and share the `.exe`.

---

## Input Format

The input text file must have the following structure:

1. **5 metadata header lines** (custom text, preserved in binary output)
2. **Event records** (one per line), each with 3 whitespace-separated columns:
   - Column 1: Timestamp (uint64)
   - Column 2: Channel number (uint16, max 16280)
   - Column 3: Filter value (0 = keep, non-zero = skip)

### Example Input

```
DETECTOR_ID=1
RUN_NUMBER=42
DATE=2024-01-15
TIME=10:30:00
VERSION=1.0
1000000 0 0
1000001 1 0
1000002 2 1
1000003 3 0
```

In this example, the third record (channel 2, filter=1) would be filtered out.

## Binary Format Specification

```
[8 bytes]     Magic: "EVTBIN\0\0"
[1 byte]      Version: 1
[1 byte]      Number of metadata lines: 5
For each metadata line:
  [2 bytes LE] Length of string
  [N bytes]    String data (no null terminator)
[8 bytes LE]   Number of events (uint64)
For each event:
  [1-9 bytes]  Varint-encoded timestamp delta (first = absolute)
  [2 bytes LE] Channel number (uint16)
```

### Varint Encoding

Timestamps use varint encoding to save space: 7 bits of data per byte, with MSB=1 indicating more bytes follow. This is particularly efficient for small deltas between consecutive events.

## Sorting Strategy

### Single-Pass In-Memory Sort (Default)
If all events fit within the configured memory chunk (default ~80% of available RAM), the program:
1. Reads all events into memory
2. Performs a single stable sort by timestamp
3. Writes the sorted binary output directly

**Memory usage:** ~10 bytes per event plus overhead

### Multi-Pass External Merge Sort
If the dataset exceeds available memory:

**Pass 1 (Read & Sort):**
- Reads events in chunks up to the memory limit
- Sorts each chunk by timestamp
- Writes sorted chunks as temporary binary run files

**Pass 2 (Merge):**
- Uses a k-way merge with a min-heap
- Maintains one buffered record per run file (~640 KB per run)
- Writes final varint-encoded output

**Peak RAM:** ~640 KB per run file + output buffer (typically much less than dataset size)

Temporary run files are automatically deleted after successful completion or on error.

## Performance

- **Event Density:** ~53 million events per 512 MB chunk
- **Output Size Reduction:** Typically 40-60% smaller than text input (depends on timestamp distribution)
- **Processing Speed:** I/O bound on most systems (typically 100K-500K events/second)

### Tips for Large Files

1. **Increase chunk size** if you have plenty of RAM:
   ```bash
   evt2bin large.txt large.bin --chunk-mb 2048
   ```

2. **Use SSDs** for temporary files when processing multi-gigabyte datasets

3. **Pre-filter data** in your data collection pipeline if possible

## Output Statistics

The program prints processing information:

```
Auto-detected available RAM: 8000 MB, using 6400 MB per chunk.
Chunk size: 6400 MB = 673 million events per run.
Pass 1: reading, filtering, writing sorted runs...
  Total: 50000000 events kept, 5000000 filtered (col3!=0), 100000 skipped (bad channel).
  Run files: 1
Pass 2: single run, streaming directly to output...
  50000000M written...
Done.
  Events written  : 50000000
  Rows filtered   : 5000000
  Rows skipped    : 100000
  Sort runs used  : 1
```

## Error Handling

- **Missing header lines**: Stops and reports number of lines found
- **I/O errors**: Prints error messages and cleans up temporary files
- **Invalid channels**: Skips records with channel > 16280
- **Memory issues**: Automatically falls back to external merge sort

All temporary files are cleaned up on both success and failure.

## Requirements

- **C++17** compatible compiler (GCC 7+, Clang 5+, MSVC 2017+)
- Platform detection for RAM query (Linux, Windows, macOS)
- Standard library: `<algorithm>`, `<queue>`, `<vector>`, `<string>`

## License

Specify your license here.

## Author

Developed for the BYUI PAS Team (Coincidence Doppler Broadening project)