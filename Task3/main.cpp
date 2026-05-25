#include "../Task2/hxlbmpfile.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

static const uint32_t kMaxCode = 65535;

struct EncodedFile {
    int width = 0;
    int height = 0;
    std::vector<RGBQUAD> palette;
    std::vector<uint16_t> codes;
};

static uint64_t MakeKey(uint32_t prefix, BYTE value) {
    return (static_cast<uint64_t>(prefix) << 8) | value;
}

static void WriteU16(std::ofstream& out, uint16_t value) {
    out.put(static_cast<char>(value & 0xff));
    out.put(static_cast<char>((value >> 8) & 0xff));
}

static void WriteU32(std::ofstream& out, uint32_t value) {
    out.put(static_cast<char>(value & 0xff));
    out.put(static_cast<char>((value >> 8) & 0xff));
    out.put(static_cast<char>((value >> 16) & 0xff));
    out.put(static_cast<char>((value >> 24) & 0xff));
}

static uint16_t ReadU16(std::ifstream& in) {
    uint16_t b0 = static_cast<unsigned char>(in.get());
    uint16_t b1 = static_cast<unsigned char>(in.get());
    if (!in) throw std::runtime_error("Unexpected end of file while reading uint16.");
    return static_cast<uint16_t>(b0 | (b1 << 8));
}

static uint32_t ReadU32(std::ifstream& in) {
    uint32_t b0 = static_cast<unsigned char>(in.get());
    uint32_t b1 = static_cast<unsigned char>(in.get());
    uint32_t b2 = static_cast<unsigned char>(in.get());
    uint32_t b3 = static_cast<unsigned char>(in.get());
    if (!in) throw std::runtime_error("Unexpected end of file while reading uint32.");
    return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24);
}

static std::vector<BYTE> GetImageBytes(HXLBMPFILE& bmp) {
    if (bmp.iYRGBnum != 1) {
        throw std::runtime_error("This experiment expects an 8-bit grayscale BMP.");
    }

    std::vector<BYTE> data;
    data.reserve(static_cast<size_t>(bmp.iImagew) * bmp.iImageh);
    for (int y = 0; y < bmp.iImageh; ++y) {
        BYTE* row = bmp.pDataAt(y);
        data.insert(data.end(), row, row + bmp.iImagew);
    }
    return data;
}

static void PutImageBytes(HXLBMPFILE& bmp, int width, int height,
                          const std::vector<RGBQUAD>& palette,
                          const std::vector<BYTE>& data) {
    if (data.size() != static_cast<size_t>(width) * height) {
        throw std::runtime_error("Decoded byte count does not match image size.");
    }

    bmp.iImagew = width;
    bmp.iImageh = height;
    bmp.iYRGBnum = 1;
    if (!bmp.IspImageDataOk()) {
        throw std::runtime_error("Failed to allocate decoded image.");
    }

    for (int i = 0; i < 256; ++i) {
        bmp.rgbPalette[i] = palette.empty() ? RGBQUAD{static_cast<BYTE>(i), static_cast<BYTE>(i), static_cast<BYTE>(i), 0}
                                           : palette[i];
    }

    size_t pos = 0;
    for (int y = 0; y < height; ++y) {
        BYTE* row = bmp.pDataAt(y);
        std::copy(data.begin() + pos, data.begin() + pos + width, row);
        pos += width;
    }
}

static double CalculateEntropy(const std::vector<BYTE>& data) {
    uint64_t hist[256] = {0};
    for (BYTE value : data) ++hist[value];

    double entropy = 0.0;
    const double total = static_cast<double>(data.size());
    for (uint64_t count : hist) {
        if (count == 0) continue;
        double p = static_cast<double>(count) / total;
        entropy -= p * std::log(p) / std::log(2.0);
    }
    return entropy;
}

static std::vector<uint16_t> LzwEncode(const std::vector<BYTE>& data) {
    if (data.empty()) return {};

    std::unordered_map<uint64_t, uint16_t> dict;
    dict.reserve(70000);
    uint32_t nextCode = 256;

    uint32_t prefix = data[0];
    std::vector<uint16_t> codes;
    codes.reserve(data.size() / 2);

    for (size_t i = 1; i < data.size(); ++i) {
        BYTE value = data[i];
        uint64_t key = MakeKey(prefix, value);
        auto it = dict.find(key);
        if (it != dict.end()) {
            prefix = it->second;
        } else {
            codes.push_back(static_cast<uint16_t>(prefix));
            if (nextCode <= kMaxCode) {
                dict.emplace(key, static_cast<uint16_t>(nextCode++));
            }
            prefix = value;
        }
    }

    codes.push_back(static_cast<uint16_t>(prefix));
    return codes;
}

struct DecodeEntry {
    int prefix;
    BYTE value;
};

static std::vector<BYTE> ExpandCode(const std::vector<DecodeEntry>& dict, uint32_t code) {
    if (code >= dict.size()) {
        throw std::runtime_error("Invalid LZW code in compressed stream.");
    }

    std::vector<BYTE> reversed;
    while (code != static_cast<uint32_t>(-1)) {
        reversed.push_back(dict[code].value);
        code = static_cast<uint32_t>(dict[code].prefix);
    }
    std::reverse(reversed.begin(), reversed.end());
    return reversed;
}

static std::vector<BYTE> LzwDecode(const std::vector<uint16_t>& codes, size_t expectedSize) {
    if (codes.empty()) return {};

    std::vector<DecodeEntry> dict;
    dict.reserve(70000);
    for (int i = 0; i < 256; ++i) {
        dict.push_back({-1, static_cast<BYTE>(i)});
    }

    std::vector<BYTE> output;
    output.reserve(expectedSize);

    uint32_t prevCode = codes[0];
    std::vector<BYTE> prevSeq = ExpandCode(dict, prevCode);
    output.insert(output.end(), prevSeq.begin(), prevSeq.end());

    for (size_t i = 1; i < codes.size(); ++i) {
        uint32_t code = codes[i];
        std::vector<BYTE> seq;

        if (code < dict.size()) {
            seq = ExpandCode(dict, code);
        } else if (code == dict.size()) {
            seq = prevSeq;
            seq.push_back(prevSeq.front());
        } else {
            throw std::runtime_error("Invalid LZW code order in compressed stream.");
        }

        output.insert(output.end(), seq.begin(), seq.end());

        if (dict.size() <= kMaxCode) {
            dict.push_back({static_cast<int>(prevCode), seq.front()});
        }

        prevCode = code;
        prevSeq = std::move(seq);
    }

    if (output.size() != expectedSize) {
        throw std::runtime_error("Decoded size differs from the original image size.");
    }
    return output;
}

static void SaveCompressedFile(const std::string& path, const EncodedFile& file) {
    std::ofstream out(path, std::ios::binary);
    if (!out) throw std::runtime_error("Cannot create compressed file: " + path);

    out.write("LZW3", 4);
    WriteU32(out, 1);
    WriteU32(out, static_cast<uint32_t>(file.width));
    WriteU32(out, static_cast<uint32_t>(file.height));
    WriteU32(out, 1);
    WriteU32(out, static_cast<uint32_t>(file.width * file.height));
    WriteU32(out, static_cast<uint32_t>(file.codes.size()));

    for (int i = 0; i < 256; ++i) {
        RGBQUAD q = file.palette[i];
        out.put(static_cast<char>(q.rgbBlue));
        out.put(static_cast<char>(q.rgbGreen));
        out.put(static_cast<char>(q.rgbRed));
        out.put(static_cast<char>(q.rgbReserved));
    }

    for (uint16_t code : file.codes) {
        WriteU16(out, code);
    }
}

static EncodedFile LoadCompressedFile(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("Cannot open compressed file: " + path);

    char magic[4];
    in.read(magic, 4);
    if (std::string(magic, 4) != "LZW3") {
        throw std::runtime_error("Compressed file magic is not LZW3.");
    }

    uint32_t version = ReadU32(in);
    if (version != 1) throw std::runtime_error("Unsupported compressed file version.");

    EncodedFile file;
    file.width = static_cast<int>(ReadU32(in));
    file.height = static_cast<int>(ReadU32(in));
    uint32_t channels = ReadU32(in);
    uint32_t pixelCount = ReadU32(in);
    uint32_t codeCount = ReadU32(in);
    if (channels != 1 || pixelCount != static_cast<uint32_t>(file.width * file.height)) {
        throw std::runtime_error("Compressed file metadata is invalid.");
    }

    file.palette.resize(256);
    for (int i = 0; i < 256; ++i) {
        file.palette[i].rgbBlue = static_cast<BYTE>(in.get());
        file.palette[i].rgbGreen = static_cast<BYTE>(in.get());
        file.palette[i].rgbRed = static_cast<BYTE>(in.get());
        file.palette[i].rgbReserved = static_cast<BYTE>(in.get());
        if (!in) throw std::runtime_error("Unexpected end of file while reading palette.");
    }

    file.codes.reserve(codeCount);
    for (uint32_t i = 0; i < codeCount; ++i) {
        file.codes.push_back(ReadU16(in));
    }
    return file;
}

static bool SameImage(const HXLBMPFILE& a, const std::vector<BYTE>& aData,
                      const HXLBMPFILE& b, const std::vector<BYTE>& bData) {
    return a.iImagew == b.iImagew && a.iImageh == b.iImageh &&
           a.iYRGBnum == b.iYRGBnum && aData == bData;
}

int main(int argc, char* argv[]) {
    const std::string inputBmp = argc > 1 ? argv[1] : "b8gray.bmp";
    const std::string compressedPath = argc > 2 ? argv[2] : "C.dat";
    const std::string decodedBmp = argc > 3 ? argv[3] : "Id.bmp";

    try {
        HXLBMPFILE src;
        if (!src.LoadBMPFile(const_cast<char*>(inputBmp.c_str()))) {
            throw std::runtime_error("Failed to load input BMP: " + inputBmp);
        }

        std::vector<BYTE> srcData = GetImageBytes(src);
        double entropy = CalculateEntropy(srcData);

        EncodedFile encoded;
        encoded.width = src.iImagew;
        encoded.height = src.iImageh;
        encoded.palette.assign(src.rgbPalette, src.rgbPalette + 256);
        encoded.codes = LzwEncode(srcData);
        SaveCompressedFile(compressedPath, encoded);

        EncodedFile loaded = LoadCompressedFile(compressedPath);
        std::vector<BYTE> decodedData = LzwDecode(
            loaded.codes,
            static_cast<size_t>(loaded.width) * loaded.height);

        HXLBMPFILE dst;
        PutImageBytes(dst, loaded.width, loaded.height, loaded.palette, decodedData);
        if (!dst.SaveBMPFile(const_cast<char*>(decodedBmp.c_str()))) {
            throw std::runtime_error("Failed to save decoded BMP: " + decodedBmp);
        }

        std::ifstream compressed(compressedPath, std::ios::binary | std::ios::ate);
        double fileBpp = static_cast<double>(compressed.tellg()) * 8.0 / srcData.size();
        double codeBpp = static_cast<double>(encoded.codes.size()) * 16.0 / srcData.size();
        bool identical = SameImage(src, srcData, dst, decodedData);

        std::ofstream result("result.txt");
        std::ostream* outs[] = {&std::cout, &result};
        for (std::ostream* os : outs) {
            *os << std::fixed << std::setprecision(6);
            *os << "LZW image coding experiment\n";
            *os << "Input image: " << inputBmp << "\n";
            *os << "Compressed file: " << compressedPath << "\n";
            *os << "Decoded image: " << decodedBmp << "\n";
            *os << "Image size: " << src.iImagew << " x " << src.iImageh << "\n";
            *os << "Original pixels: " << srcData.size() << "\n";
            *os << "LZW code count: " << encoded.codes.size() << "\n";
            *os << "Encoded bpp (codes only): " << codeBpp << "\n";
            *os << "Encoded bpp (C.dat file): " << fileBpp << "\n";
            *os << "Original entropy: " << entropy << " bit/pixel\n";
            *os << "Is == Id: " << (identical ? "YES" : "NO") << "\n";
        }

        return identical ? 0 : 2;
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << "\n";
        return 1;
    }
}
