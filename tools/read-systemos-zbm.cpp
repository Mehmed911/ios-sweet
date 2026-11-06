// SPDX-License-Identifier: GPL-2.0-or-later
// Read-only adapter to upstream apfs-fuse's APFS/LZBITMAP implementation.
#include <ApfsLib/ApfsContainer.h>
#include <ApfsLib/ApfsVolume.h>
#include <ApfsLib/ApfsDir.h>
#include <ApfsLib/Decmpfs.h>
#include <ApfsLib/Device.h>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <memory>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 4) { std::fprintf(stderr, "usage: read-systemos-zbm IMAGE COMPONENT NEW-OUTPUT\n"); return 2; }
    const char *filename = nullptr;
    uint64_t expected_inode = 0, expected_bytes = 0;
    bool runtime_module = false;
    if (!std::strcmp(argv[2], "42")) {
        filename = "dyld_shared_cache_arm64.42.dyldlinkedit"; expected_inode = 88; expected_bytes = 333955072;
    } else if (!std::strcmp(argv[2], "28")) {
        filename = "dyld_shared_cache_arm64.28.dyldlinkedit"; expected_inode = 73; expected_bytes = 19906560;
    } else if (!std::strcmp(argv[2], "symbols")) {
        filename = "dyld_shared_cache_arm64.symbols"; expected_inode = 90; expected_bytes = 591855616;
    } else if (!std::strcmp(argv[2], "objc-trampolines")) {
        filename = "libobjc-trampolines.dylib"; expected_inode = 3136; expected_bytes = 68080;
        runtime_module = true;
    } else { return 2; }
    std::unique_ptr<Device> device(Device::OpenDevice(argv[1]));
    if (!device) return 3;
    ApfsContainer container(device.get(), 0, device->GetSize());
    if (!container.Init()) return 4;
    std::unique_ptr<ApfsVolume> volume(container.GetVolume(0));
    if (!volume) return 5;
    ApfsDir directory(*volume);
    uint64_t inode = 2;
    const char *cache_parts[] = {"System", "Library", "Caches", "com.apple.dyld", filename};
    const char *runtime_parts[] = {"usr", "lib", filename};
    const char **parts = runtime_module ? runtime_parts : cache_parts;
    size_t part_count = runtime_module ? 3 : 5;
    for (size_t index = 0; index < part_count; ++index) {
        ApfsDir::DirRec entry;
        if (!directory.LookupName(entry, inode, parts[index])) return 6;
        inode = entry.file_id;
    }
    if (inode != expected_inode) return 7;
    std::vector<uint8_t> attr, decoded;
    if (!directory.GetAttribute(attr, inode, "com.apple.decmpfs") || attr.size() < sizeof(CompressionHeader)) return 8;
    const CompressionHeader *header = reinterpret_cast<const CompressionHeader *>(attr.data());
    if (header->algo != 14 || header->size != expected_bytes) return 9;
    if (!DecompressFile(directory, inode, decoded, attr) || decoded.size() != expected_bytes) return 10;
    int fd = open(argv[3], O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (fd < 0) return 11;
    size_t done = 0;
    while (done < decoded.size()) {
        ssize_t count = write(fd, decoded.data() + done, decoded.size() - done);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) { close(fd); return 12; }
        done += static_cast<size_t>(count);
    }
    if (fsync(fd) || close(fd)) return 13;
    std::printf("ZBM extraction PASS inode=%llu algorithm=14 bytes=%zu\n", static_cast<unsigned long long>(inode), done);
    return 0;
}
