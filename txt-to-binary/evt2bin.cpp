/*
 * evt2bin - Convert text event files to compact binary format
 *
 * Binary format spec (EVTCOL v2):
 *   [8 bytes]    Magic: "EVTCOL\0\0"
 *   [1 byte]     Version: 2
 *   [1 byte]     Number of metadata lines (5)
 *   For each metadata line:
 *     [2 bytes LE] Length of string
 *     [N bytes]    String data (no null terminator)
 *   [8 bytes LE]  Number of events (uint64)
 *   [4 bytes LE]  Compressed timestamp column size in bytes
 *   [N bytes]     zlib-compressed varint-encoded timestamp deltas
 *                 (first delta = absolute timestamp, rest = delta from previous)
 *   [4 bytes LE]  Compressed channel column size in bytes
 *   [N bytes]     zlib-compressed uint16 LE channel values
 *
 * Column-oriented layout compresses each data type separately for better ratios.
 * Varint encoding: 7 bits per byte, MSB=1 means more bytes follow.
 *
 * Sorting strategy:
 *   If all events fit within the memory limit (--chunk-mb, default auto-detected
 *   or 512 MB), an in-memory stable sort is used.
 *   Otherwise, an external merge sort is used:
 *     Pass 1 - read chunks up to the memory limit, sort each, write as a
 *              temporary run file of fixed 10-byte raw records.
 *     Pass 2 - k-way merge all run files with a min-heap, collecting all
 *              sorted events into memory, then write compressed column output.
 *   Temp files are deleted on both success and failure.
 *
 * Usage:
 *   evt2bin <input.txt> <output.bin> [--delete-input] [--chunk-mb N]
 *
 * Compile:
 *   g++ -O2 -std=c++17 -o evt2bin evt2bin.cpp
 *   cl /O2 /std:c++17 /Fe:evt2bin.exe evt2bin.cpp
 */

#include <algorithm>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <queue>
#include <string>
#include <vector>
#include <zlib.h>

#if defined(_WIN32)
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#endif

// ---------------------------------------------------------------------------
// Platform: detect available RAM
// ---------------------------------------------------------------------------

static uint64_t detect_available_ram_mb() {
#if defined(__linux__)
    FILE* f = fopen("/proc/meminfo", "r");
    if (f) {
        char line[128];
        while (fgets(line, sizeof(line), f)) {
            uint64_t kb = 0;
            if (sscanf(line, "MemAvailable: %" SCNu64 " kB", &kb) == 1) {
                fclose(f);
                return kb / 1024;
            }
        }
        fclose(f);
    }
#elif defined(_WIN32)
    MEMORYSTATUSEX ms; ms.dwLength = sizeof(ms);
    if (GlobalMemoryStatusEx(&ms))
        return (uint64_t)(ms.ullAvailPhys / (1024 * 1024));
#elif defined(__APPLE__)
    // Best-effort: use sysctl vm.swapusage or just fall through to default
    FILE* p = popen("sysctl -n hw.memsize 2>/dev/null", "r");
    if (p) {
        uint64_t bytes = 0;
        if (fscanf(p, "%" SCNu64, &bytes) == 1) {
            pclose(p);
            return (bytes / 2) / (1024 * 1024); // use half of total as conservative estimate
        }
        pclose(p);
    }
#endif
    return 0; // unknown
}

// ---------------------------------------------------------------------------
// Varint helper
// ---------------------------------------------------------------------------

static int write_varint(uint8_t* buf, uint64_t value) {
    int n = 0;
    do {
        uint8_t byte = value & 0x7F;
        value >>= 7;
        if (value != 0) byte |= 0x80;
        buf[n++] = byte;
    } while (value != 0);
    return n;
}

// ---------------------------------------------------------------------------
// zlib compression helper
// ---------------------------------------------------------------------------

static std::vector<uint8_t> zlib_compress(const uint8_t* data, size_t len) {
    uLongf out_size = compressBound((uLong)len);
    std::vector<uint8_t> out(out_size);
    if (compress2(out.data(), &out_size, data, (uLong)len, Z_BEST_COMPRESSION) != Z_OK) {
        fprintf(stderr, "Error: zlib compression failed\n");
        return {};
    }
    out.resize((size_t)out_size);
    return out;
}

// ---------------------------------------------------------------------------
// Buffered writer (for final output)
// ---------------------------------------------------------------------------

static const size_t WRITE_BUF_SIZE = 8 * 1024 * 1024;

struct Writer {
    FILE* fp;
    std::vector<uint8_t> buf;
    size_t pos;

    explicit Writer(FILE* f) : fp(f), pos(0) { buf.resize(WRITE_BUF_SIZE); }

    void flush() {
        if (pos > 0) { fwrite(buf.data(), 1, pos, fp); pos = 0; }
    }

    void write(const void* data, size_t len) {
        const uint8_t* src = reinterpret_cast<const uint8_t*>(data);
        while (len > 0) {
            size_t space = buf.size() - pos;
            if (space == 0) { flush(); space = buf.size(); }
            size_t n = len < space ? len : space;
            memcpy(buf.data() + pos, src, n);
            pos += n; src += n; len -= n;
        }
    }

    void write_u8(uint8_t v)     { write(&v, 1); }
    void write_u16le(uint16_t v) { uint8_t b[2]={(uint8_t)(v&0xFF),(uint8_t)(v>>8)}; write(b,2); }
    void write_u64le(uint64_t v) { uint8_t b[8]; for(int i=0;i<8;i++){b[i]=v&0xFF;v>>=8;} write(b,8); }
    void write_varint(uint64_t v){ uint8_t b[9]; int n=::write_varint(b,v); write(b,n); }
    void write_str16(const std::string& s) {
        uint16_t len=(uint16_t)(s.size()>65535?65535:s.size());
        write_u16le(len); write(s.data(),len);
    }
};

// ---------------------------------------------------------------------------
// Buffered line reader
// ---------------------------------------------------------------------------

static const size_t READ_BUF_SIZE = 8 * 1024 * 1024;

struct Reader {
    FILE* fp;
    std::vector<char> buf;
    size_t buf_len, buf_pos;

    explicit Reader(FILE* f) : fp(f), buf_len(0), buf_pos(0) { buf.resize(READ_BUF_SIZE); }

    bool read_line(std::string& dst) {
        dst.clear();
        for (;;) {
            while (buf_pos < buf_len) {
                char c = buf[buf_pos++];
                if (c == '\n') return true;
                if (c != '\r') dst += c;
            }
            buf_len = fread(buf.data(), 1, READ_BUF_SIZE, fp);
            buf_pos = 0;
            if (buf_len == 0) return !dst.empty();
        }
    }
};

// ---------------------------------------------------------------------------
// Fast integer parsers
// ---------------------------------------------------------------------------

static inline const char* skip_ws(const char* p) {
    while (*p == ' ' || *p == '\t') p++;
    return p;
}

static inline const char* parse_uint64(const char* p, uint64_t& out) {
    uint64_t v = 0;
    while (*p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
    out = v;
    return p;
}

// ---------------------------------------------------------------------------
// Raw event: 10-byte fixed record used in temporary run files
// Layout: [8 bytes LE uint64 timestamp][2 bytes LE uint16 channel]
// ---------------------------------------------------------------------------

#pragma pack(push, 1)
struct RawEvent {
    uint64_t ts;
    uint16_t channel;
};

#pragma pack(pop)
static_assert(sizeof(RawEvent) == 10, "RawEvent must be 10 bytes");

static void raw_write(FILE* f, const RawEvent& e) {
    uint8_t b[10];
    uint64_t ts = e.ts;
    for (int i = 0; i < 8; i++) { b[i] = ts & 0xFF; ts >>= 8; }
    b[8] = e.channel & 0xFF;
    b[9] = e.channel >> 8;
    fwrite(b, 1, 10, f);
}

static bool raw_read(FILE* f, RawEvent& e) {
    uint8_t b[10];
    if (fread(b, 1, 10, f) != 10) return false;
    e.ts = 0;
    for (int i = 7; i >= 0; i--) e.ts = (e.ts << 8) | b[i];
    e.channel = (uint16_t)(b[8] | (b[9] << 8));
    return true;
}

// ---------------------------------------------------------------------------
// Run file reader with read-ahead buffer (used during merge)
// ---------------------------------------------------------------------------

static const size_t RUN_READ_BUF_EVENTS = 65536; // 640 KB per run reader

struct RunReader {
    FILE*    fp;
    std::string path;
    std::vector<RawEvent> buf;
    size_t   buf_pos;
    size_t   buf_len;
    bool     exhausted;

    explicit RunReader(const std::string& p)
        : fp(nullptr), path(p), buf_pos(0), buf_len(0), exhausted(false)
    {
        buf.resize(RUN_READ_BUF_EVENTS);
        fp = fopen(p.c_str(), "rb");
    }

    ~RunReader() { close(); }

    bool open_ok() const { return fp != nullptr; }

    // Returns true if there is a valid current record
    bool fill() {
        if (buf_pos < buf_len) return true;  // serve buffered data first
        if (exhausted) return false;          // only bail after buffer is empty
        // Refill buffer
        buf_pos = 0;
        buf_len = 0;
        uint8_t raw[10];
        while (buf_len < buf.size()) {
            if (fread(raw, 1, 10, fp) != 10) { exhausted = true; break; }
            RawEvent& e = buf[buf_len++];
            e.ts = 0;
            for (int i = 7; i >= 0; i--) e.ts = (e.ts << 8) | raw[i];
            e.channel = (uint16_t)(raw[8] | (raw[9] << 8));
        }
        return buf_len > 0;
    }

    const RawEvent& current() const { return buf[buf_pos]; }

    void advance() { buf_pos++; }

    void close() {
        if (fp) { fclose(fp); fp = nullptr; }
    }

    void remove_file() {
        close();
        remove(path.c_str());
    }
};

// ---------------------------------------------------------------------------
// Heap entry for k-way merge
// ---------------------------------------------------------------------------

struct HeapEntry {
    uint64_t ts;
    uint16_t channel;
    int      run_idx;
    // Min-heap: smallest ts wins
    bool operator>(const HeapEntry& o) const { return ts > o.ts; }
};

// ---------------------------------------------------------------------------
// Write one sorted chunk to a temp run file.
// Returns the path, or "" on error.
// ---------------------------------------------------------------------------

static std::string write_run_file(
    const std::string& base_path,
    int run_idx,
    std::vector<RawEvent>& chunk)
{
    std::stable_sort(chunk.begin(), chunk.end(),
        [](const RawEvent& a, const RawEvent& b){ return a.ts < b.ts; });

    char path[4096];
    snprintf(path, sizeof(path), "%s.tmp.run.%06d", base_path.c_str(), run_idx);

    FILE* f = fopen(path, "wb");
    if (!f) { perror(path); return ""; }

    // Bulk write using a local buffer
    static const size_t BUF = 8 * 1024 * 1024;
    std::vector<uint8_t> wbuf(BUF);
    size_t wpos = 0;

    for (const RawEvent& e : chunk) {
        if (wpos + 10 > BUF) { fwrite(wbuf.data(), 1, wpos, f); wpos = 0; }
        uint64_t ts = e.ts;
        for (int i = 0; i < 8; i++) { wbuf[wpos++] = ts & 0xFF; ts >>= 8; }
        wbuf[wpos++] = e.channel & 0xFF;
        wbuf[wpos++] = e.channel >> 8;
    }
    if (wpos) fwrite(wbuf.data(), 1, wpos, f);
    fclose(f);
    return std::string(path);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

static void print_usage(const char* prog) {
    fprintf(stderr,
        "Usage: %s <input.txt> <output.bin> [options]\n"
        "\n"
        "Options:\n"
        "  --delete-input     Delete the input file after successful conversion.\n"
        "  --chunk-mb N       Memory limit per sort chunk in MB (default: auto-detect\n"
        "                     available RAM * 0.8, fallback 512 MB).\n"
        "\n"
        "Sorting:\n"
        "  If all events fit in the chunk, an in-memory sort is used.\n"
        "  Otherwise, external merge sort is used automatically:\n"
        "    - Sorted run files are written to the same directory as <output.bin>.\n"
        "    - Peak RAM during merge = ~640 KB per run file + output buffer.\n"
        "    - Temp files are cleaned up on both success and error.\n"
        "\n"
        "Event record: ~10 bytes.  512 MB chunk holds ~53M events.\n",
        prog);
}

int main(int argc, char* argv[]) {
    if (argc < 3) { print_usage(argv[0]); return 1; }

    const char* input_path  = argv[1];
    const char* output_path = argv[2];
    bool     delete_input = false;
    uint64_t chunk_mb     = 0; // 0 = auto-detect

    for (int i = 3; i < argc; i++) {
        if (strcmp(argv[i], "--delete-input") == 0) {
            delete_input = true;
        } else if (strcmp(argv[i], "--chunk-mb") == 0 && i + 1 < argc) {
            chunk_mb = (uint64_t)atoll(argv[++i]);
            if (chunk_mb < 16) { fprintf(stderr, "--chunk-mb must be at least 16.\n"); return 1; }
        } else {
            fprintf(stderr, "Unknown option: %s\n", argv[i]);
            return 1;
        }
    }

    // --- Determine chunk size ---
    if (chunk_mb == 0) {
        uint64_t avail = detect_available_ram_mb();
        if (avail > 0) {
            chunk_mb = (uint64_t)(avail * 0.8);
            fprintf(stderr, "Auto-detected available RAM: %" PRIu64 " MB, using %" PRIu64 " MB per chunk.\n",
                avail, chunk_mb);
        } else {
            chunk_mb = 512;
            fprintf(stderr, "Could not detect RAM, defaulting to %" PRIu64 " MB per chunk.\n", chunk_mb);
        }
    }

    const uint64_t chunk_events = (chunk_mb * 1024ULL * 1024ULL) / sizeof(RawEvent);
    fprintf(stderr, "Chunk size: %" PRIu64 " MB = %" PRIu64 " events per run.\n",
        chunk_mb, chunk_events);

    // --- Open input ---
    FILE* fin = fopen(input_path, "rb");
    if (!fin) { perror(input_path); return 1; }

    Reader reader(fin);

    // --- Read 5 metadata header lines ---
    static const int NUM_HEADERS = 5;
    std::string meta[NUM_HEADERS];
    for (int i = 0; i < NUM_HEADERS; i++) {
        if (!reader.read_line(meta[i])) {
            fprintf(stderr, "Error: expected %d header lines, got %d.\n", NUM_HEADERS, i);
            fclose(fin); return 1;
        }
    }

    // -------------------------------------------------------------------------
    // Pass 1 -- read, filter, and write sorted run files (or single in-mem sort)
    // -------------------------------------------------------------------------

    std::vector<std::string> run_paths;
    std::vector<RawEvent>    chunk;
    chunk.reserve((size_t)std::min(chunk_events, (uint64_t)4 * 1024 * 1024));

    uint64_t total_events   = 0;
    uint64_t filtered_count = 0;
    uint64_t skipped_count  = 0;
    std::string line;

    auto flush_chunk = [&]() -> bool {
        if (chunk.empty()) return true;
        std::string path = write_run_file(output_path, (int)run_paths.size(), chunk);
        if (path.empty()) return false;
        run_paths.push_back(path);
        fprintf(stderr, "  Run %d written: %" PRIu64 " events -> %s\n",
            (int)run_paths.size(), (uint64_t)chunk.size(), path.c_str());
        total_events += chunk.size();
        chunk.clear();
        return true;
    };

    fprintf(stderr, "Pass 1: reading, filtering, writing sorted runs...\n");

    while (reader.read_line(line)) {
        if (line.empty()) continue;
        const char* p = skip_ws(line.c_str());
        if (*p == '\0') continue;

        uint64_t ts, channel, filter_val;
        p = parse_uint64(p, ts);      p = skip_ws(p);
        if (*p == '-') { filtered_count++; continue; }  // negative channel
        p = parse_uint64(p, channel); p = skip_ws(p);
        if (*p == '-') { filtered_count++; continue; } // negative filter value
        p = parse_uint64(p, filter_val);

        if (filter_val != 0) { filtered_count++; continue; }
        if (channel < 0) { filtered_count++; continue; }
        if (channel > 16383) { skipped_count++;  continue; }

        chunk.push_back({ts, (uint16_t)channel});

        if ((uint64_t)chunk.size() >= chunk_events) {
            if (!flush_chunk()) {
                fclose(fin);
                for (auto& rp : run_paths) remove(rp.c_str());
                return 1;
            }
        }

        if ((total_events + chunk.size()) % 5000000 == 0) {
            fprintf(stderr, "\r  %" PRIu64 "M events read so far...",
                (total_events + chunk.size()) / 1000000);
            fflush(stderr);
        }
    }
    fclose(fin);
    if ((total_events + chunk.size()) >= 5000000) fprintf(stderr, "\n");

    // Flush final partial chunk
    if (!flush_chunk()) {
        for (auto& rp : run_paths) remove(rp.c_str());
        return 1;
    }

    fprintf(stderr,
        "  Total: %" PRIu64 " events kept, %" PRIu64 " filtered (col3!=0)"
        ", %" PRIu64 " skipped (bad channel).\n"
        "  Run files: %d\n",
        total_events, filtered_count, skipped_count, (int)run_paths.size());

    // -------------------------------------------------------------------------
    // Pass 2 -- k-way merge all run files, collecting into column buffers
    // -------------------------------------------------------------------------

    std::vector<uint64_t> out_ts;
    std::vector<uint16_t> out_ch;
    out_ts.reserve((size_t)total_events);
    out_ch.reserve((size_t)total_events);

    if (run_paths.size() == 1) {
        // Only one run: stream directly into column buffers
        fprintf(stderr, "Pass 2: collecting single run into column buffers...\n");
        RunReader rr(run_paths[0]);
        if (!rr.open_ok()) {
            fprintf(stderr, "Error: could not open run file.\n");
            for (auto& rp : run_paths) remove(rp.c_str());
            return 1;
        }
        while (rr.fill()) {
            const RawEvent& e = rr.current();
            out_ts.push_back(e.ts);
            out_ch.push_back(e.channel);
            rr.advance();
        }
        rr.remove_file();
    } else {
        // K-way merge with min-heap into column buffers
        fprintf(stderr, "Pass 2: merging %d runs into column buffers...\n", (int)run_paths.size());

        std::vector<RunReader*> readers;
        readers.reserve(run_paths.size());
        for (const auto& rp : run_paths) {
            RunReader* rr = new RunReader(rp);
            if (!rr->open_ok()) {
                fprintf(stderr, "Error: could not open run file %s\n", rp.c_str());
                for (auto r : readers) { r->remove_file(); delete r; }
                for (auto& p : run_paths) remove(p.c_str());
                return 1;
            }
            readers.push_back(rr);
        }

        std::priority_queue<HeapEntry,
                            std::vector<HeapEntry>,
                            std::greater<HeapEntry>> pq;

        for (int i = 0; i < (int)readers.size(); i++) {
            if (readers[i]->fill()) {
                const RawEvent& e = readers[i]->current();
                pq.push({e.ts, e.channel, i});
                readers[i]->advance();
            }
        }

        while (!pq.empty()) {
            HeapEntry top = pq.top(); pq.pop();
            out_ts.push_back(top.ts);
            out_ch.push_back(top.channel);

            RunReader* rr = readers[top.run_idx];
            if (rr->fill()) {
                const RawEvent& e = rr->current();
                pq.push({e.ts, e.channel, top.run_idx});
                rr->advance();
            }

            if (out_ts.size() % 5000000 == 0) {
                fprintf(stderr, "\r  %" PRIu64 "M merged...", (uint64_t)out_ts.size() / 1000000);
                fflush(stderr);
            }
        }
        if (out_ts.size() >= 5000000) fprintf(stderr, "\n");

        for (auto rr : readers) { rr->remove_file(); delete rr; }
    }

    fprintf(stderr, "Pass 3: encoding and compressing columns...\n");

    // --- Encode timestamp deltas into a byte buffer ---
    std::vector<uint8_t> ts_buf;
    ts_buf.reserve(out_ts.size() * 4);
    {
        uint64_t prev = 0;
        for (size_t i = 0; i < out_ts.size(); i++) {
            uint64_t delta = (i == 0) ? out_ts[i] : (out_ts[i] - prev);
            prev = out_ts[i];
            uint8_t b[9];
            int n = write_varint(b, delta);
            for (int j = 0; j < n; j++) ts_buf.push_back(b[j]);
        }
    }

    // --- Encode channels as packed uint16 LE ---
    std::vector<uint8_t> ch_buf(out_ch.size() * 2);
    for (size_t i = 0; i < out_ch.size(); i++) {
        ch_buf[i * 2]     = out_ch[i] & 0xFF;
        ch_buf[i * 2 + 1] = out_ch[i] >> 8;
    }

    // --- zlib compress both columns ---
    auto ts_compressed = zlib_compress(ts_buf.data(), ts_buf.size());
    auto ch_compressed = zlib_compress(ch_buf.data(), ch_buf.size());
    if (ts_compressed.empty() || ch_compressed.empty()) {
        return 1;
    }

    fprintf(stderr,
        "  Timestamp column: %zu bytes -> %zu bytes compressed\n"
        "  Channel column:   %zu bytes -> %zu bytes compressed\n",
        ts_buf.size(), ts_compressed.size(),
        ch_buf.size(), ch_compressed.size());

    // --- Write output file ---
    FILE* fout = fopen(output_path, "wb");
    if (!fout) {
        perror(output_path);
        return 1;
    }
    Writer writer(fout);

    const char MAGIC[8] = {'E','V','T','C','O','L','\0','\0'};
    writer.write(MAGIC, 8);
    writer.write_u8(2);   // version 2
    writer.write_u8((uint8_t)NUM_HEADERS);
    for (int i = 0; i < NUM_HEADERS; i++) writer.write_str16(meta[i]);
    writer.write_u64le(total_events);

    // Write compressed timestamp column
    uint32_t ts_csize = (uint32_t)ts_compressed.size();
    writer.write(&ts_csize, 4);
    writer.write(ts_compressed.data(), ts_compressed.size());

    // Write compressed channel column
    uint32_t ch_csize = (uint32_t)ch_compressed.size();
    writer.write(&ch_csize, 4);
    writer.write(ch_compressed.data(), ch_compressed.size());

    writer.flush();
    fclose(fout);

    // --- Summary ---
    fprintf(stderr,
        "Done.\n"
        "  Events written  : %" PRIu64 "\n"
        "  Rows filtered   : %" PRIu64 "\n"
        "  Rows skipped    : %" PRIu64 "\n"
        "  Sort runs used  : %d\n",
        total_events, filtered_count, skipped_count, (int)run_paths.size());

    // --- Optionally delete input ---
    if (delete_input) {
        if (remove(input_path) != 0) perror("Warning: could not delete input file");
        else fprintf(stderr, "  Input file deleted: %s\n", input_path);
    }

    return 0;
}
