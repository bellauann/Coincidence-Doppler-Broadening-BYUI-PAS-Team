# evt2bin - Event File Binary Converter

A high-performance C++ utility that converts large text event data files to a compact binary format with intelligent sorting and compression.

## Overview

`evt2bin` is designed to efficiently handle massive event logs by converting them from text to a space-optimized binary format. It automatically chooses the best sorting strategy based on available memory and dataset size, making it suitable for processing gigabytes of event data.

## Features

- **Efficient Conversion**: Converts text event records to compact binary format with varint-encoded timestamps
- **Smart Memory Management**: Automatically detects available RAM and uses optimal chunk sizes
- **Hybrid Sorting Algorithm**:
  - **In-memory sort** for datasets that fit in memory
  - **External merge sort** with temporary run files for large datasets
- **Data Validation**: Filters invalid records and validates channel numbers
- **Buffered I/O**: 8 MB read/write buffers for high-speed processing
- **Progress Reporting**: Real-time statistics on processing status
- **Cross-platform**: Works on Linux, Windows, and macOS

## Compilation

```bash
# Linux/macOS (GCC)
g++ -O2 -std=c++17 -o evt2bin evt2bin.cpp

# Windows (MSVC)
cl /O2 /std:c++17 /Fe:evt2bin.exe evt2bin.cpp
```

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
