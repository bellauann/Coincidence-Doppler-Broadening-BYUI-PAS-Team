CXX      := g++
CXXFLAGS := -O2 -std=c++17
SRCS     := evt2bin.cpp
BIN_DIR  := bin
TARGET   := $(BIN_DIR)/evt2bin

# ---------------------------------------------------------------------------
# Detect OS
# ---------------------------------------------------------------------------
OS := $(shell uname -s 2>/dev/null || echo Windows)

ifeq ($(OS), Darwin)
    # macOS — zlib ships with Xcode tools
    LDFLAGS  := -lz
    $(info Platform: macOS)

else ifeq ($(OS), Linux)
    # Linux — requires zlib1g-dev (apt) or zlib-devel (dnf)
    LDFLAGS  := -lz
    $(info Platform: Linux)

else
    # Windows (MinGW/MSYS2)
    TARGET   := $(BIN_DIR)/evt2bin.exe
    LDFLAGS  := -lz
    $(info Platform: Windows (MinGW))
endif

# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------
.PHONY: all clean static help

all: $(TARGET)

$(BIN_DIR):
	mkdir -p $@

$(TARGET): $(BIN_DIR) $(SRCS)
	$(CXX) $(CXXFLAGS) -o $@ $(SRCS) $(LDFLAGS)
	@echo "Built: $@"

# Static build — embeds zlib so the binary runs without any dependencies
static: $(BIN_DIR) $(SRCS)
ifeq ($(OS), Darwin)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRCS) /usr/lib/libz.a
else ifeq ($(OS), Linux)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRCS) -lz -static-libstdc++ -static-libgcc
else
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRCS) -lz -static
endif
	@echo "Static build: $(TARGET) (no runtime dependencies)"

clean:
	rm -rf $(BIN_DIR) *.o *.bin.tmp.run.*

help:
	@echo "Usage:"
	@echo "  make          Build evt2bin into bin/ (requires system zlib)"
	@echo "  make static   Build self-contained binary into bin/ (no deps)"
	@echo "  make clean    Remove bin/ and compiled files"

