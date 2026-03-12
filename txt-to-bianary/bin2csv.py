#!/usr/bin/env python3
"""
bin2csv.py - Convert evt2bin binary format back to CSV
"""

import struct
import sys


def read_varint(f):
    """Read a varint-encoded uint64 from file."""
    value = 0
    shift = 0
    while True:
        byte = f.read(1)
        if not byte:
            return None
        b = byte[0]
        value |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            break
        shift += 7
    return value


def bin2csv(input_bin, output_csv):
    """Convert binary event file to CSV format."""
    
    with open(input_bin, 'rb') as f:
        # Read and verify magic
        magic = f.read(8)
        if magic != b'EVTBIN\x00\x00':
            print(f"Error: Invalid magic bytes: {magic}", file=sys.stderr)
            return False
        
        # Read version and header count
        version = struct.unpack('<B', f.read(1))[0]
        num_headers = struct.unpack('<B', f.read(1))[0]
        
        print(f"Version: {version}, Headers: {num_headers}", file=sys.stderr)
        
        # Read metadata lines
        metadata = []
        for i in range(num_headers):
            str_len = struct.unpack('<H', f.read(2))[0]
            str_data = f.read(str_len).decode('utf-8', errors='replace')
            metadata.append(str_data)
            print(f"  Header {i}: {str_data}", file=sys.stderr)
        
        # Read event count
        num_events = struct.unpack('<Q', f.read(8))[0]
        print(f"Events: {num_events}", file=sys.stderr)
        
        # Write CSV
        with open(output_csv, 'w') as out:
            # Write headers as comments (optional)
            for header in metadata:
                out.write(f"# {header}\n")
            
            # Read and decode events
            prev_ts = 0
            for i in range(num_events):
                delta = read_varint(f)
                if delta is None:
                    print(f"Error: Unexpected EOF at event {i}", file=sys.stderr)
                    return False
                
                # First event is absolute, rest are deltas
                if i == 0:
                    prev_ts = delta
                else:
                    prev_ts += delta
                
                # Read channel
                channel = struct.unpack('<H', f.read(2))[0]
                
                # Skip invalid channels (same limit as evt2bin.cpp)
                if channel > 16280:
                    continue
                
                # Write CSV row: timestamp,channel,filter (0 = kept)
                out.write(f"{prev_ts},{channel},0\n")
                
                if (i + 1) % 100000 == 0:
                    print(f"\r  {i+1}/{num_events} events...", end='', file=sys.stderr)
            
            print(f"\n  Done! Wrote {num_events} events to {output_csv}", file=sys.stderr)
    
    return True


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.bin> <output.csv>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if bin2csv(input_file, output_file):
        sys.exit(0)
    else:
        sys.exit(1)
