#!/usr/bin/env python3
"""
bin2csv.py - Convert evt2bin binary format back to CSV.
Supports both EVTCOL v2 (column-oriented + zlib) and legacy EVTBIN v1.
"""

import struct
import sys
import zlib


def read_varint_from_bytes(data, pos):
    """Read a varint from a bytes object at position pos. Returns (value, new_pos)."""
    value = 0
    shift = 0
    while True:
        b = data[pos]; pos += 1
        value |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            break
        shift += 7
    return value, pos


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


def read_metadata(f, num_headers):
    metadata = []
    for i in range(num_headers):
        str_len = struct.unpack('<H', f.read(2))[0]
        str_data = f.read(str_len).decode('utf-8', errors='replace')
        metadata.append(str_data)
        print(f"  Header {i}: {str_data}", file=sys.stderr)
    return metadata


def bin2csv(input_bin, output_csv):
    with open(input_bin, 'rb') as f:
        magic = f.read(8)

        # -------------------------------------------------------
        # EVTCOL v2: column-oriented + zlib compressed
        # -------------------------------------------------------
        if magic == b'EVTCOL\x00\x00':
            version    = struct.unpack('<B', f.read(1))[0]
            num_hdr    = struct.unpack('<B', f.read(1))[0]
            print(f"Format: EVTCOL v{version}, Headers: {num_hdr}", file=sys.stderr)
            metadata   = read_metadata(f, num_hdr)
            num_events = struct.unpack('<Q', f.read(8))[0]
            print(f"Events: {num_events}", file=sys.stderr)

            # Read and decompress timestamp column
            ts_csize      = struct.unpack('<I', f.read(4))[0]
            ts_compressed = f.read(ts_csize)
            ts_data       = zlib.decompress(ts_compressed)

            # Read and decompress channel column
            ch_csize      = struct.unpack('<I', f.read(4))[0]
            ch_compressed = f.read(ch_csize)
            ch_data       = zlib.decompress(ch_compressed)

            # Decode varint timestamp deltas
            timestamps = []
            pos, prev_ts = 0, 0
            for i in range(num_events):
                delta, pos = read_varint_from_bytes(ts_data, pos)
                prev_ts = delta if i == 0 else prev_ts + delta
                timestamps.append(prev_ts)

            # Decode uint16 LE channels
            channels = list(struct.unpack_from(f'<{num_events}H', ch_data))

            # Write CSV
            with open(output_csv, 'w') as out:
                for h in metadata:
                    out.write(f"# {h}\n")
                written = 0
                for ts, ch in zip(timestamps, channels):
                    out.write(f"{ts},{ch},0\n")
                    written += 1
                print(f"  Done! Wrote {written} events to {output_csv}", file=sys.stderr)

        # -------------------------------------------------------
        # Legacy EVTBIN v1: interleaved varint+uint16, no compression
        # -------------------------------------------------------
        elif magic == b'EVTBIN\x00\x00':
            version    = struct.unpack('<B', f.read(1))[0]
            num_hdr    = struct.unpack('<B', f.read(1))[0]
            print(f"Format: EVTBIN v{version} (legacy), Headers: {num_hdr}", file=sys.stderr)
            metadata   = read_metadata(f, num_hdr)
            num_events = struct.unpack('<Q', f.read(8))[0]
            print(f"Events: {num_events}", file=sys.stderr)

            with open(output_csv, 'w') as out:
                for h in metadata:
                    out.write(f"# {h}\n")
                prev_ts, written = 0, 0
                for i in range(num_events):
                    delta = read_varint(f)
                    if delta is None:
                        print(f"Error: Unexpected EOF at event {i}", file=sys.stderr)
                        return False
                    prev_ts = delta if i == 0 else prev_ts + delta
                    channel = struct.unpack('<H', f.read(2))[0]
                    if channel > 16280:
                        continue
                    out.write(f"{prev_ts},{channel},0\n")
                    written += 1
                print(f"  Done! Wrote {written} events to {output_csv}", file=sys.stderr)

        else:
            print(f"Error: Unrecognised magic bytes: {magic}", file=sys.stderr)
            return False

    return True


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.bin> <output.csv>", file=sys.stderr)
        sys.exit(1)

    if bin2csv(sys.argv[1], sys.argv[2]):
        sys.exit(0)
    else:
        sys.exit(1)

