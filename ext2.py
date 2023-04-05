import os
import struct

class Ext2:
    def __init__(self, fs_path):
        # Open the file as binary
        self.fs_file = open(fs_path, "rb")

        # Read the superblock from the filesystem
        self.superblock = self.read_superblock()

        # Compute the block group descriptor table (bgdt) location
        self.bgdt_start = self.superblock.first_data_block + 1
        self.bgdt_size = self.superblock.num_block_groups * self.superblock.bgdt_entries_per_block
        self.bgdt_block_size = self.superblock.bgdt_entries_per_block * 32  # 32 bytes per bgdt entry
        self.bgdt_offset = self.bgdt_start * self.superblock.block_size

        # Read the block group descriptor table from the filesystem
        self.bgdt = self.read_bgdt()

        # Compute the location of the root inode
        root_inode_num = self.superblock.root_inode_num
        root_inode = self.get_inode(root_inode_num)
        self.root_dir = Ext2Directory(root_inode, "/", self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.fs_file.close()

    def read_superblock(self):
        # Seek to the start of the filesystem
        self.fs_file.seek(1024)

        # Read the superblock from the filesystem
        superblock_data = self.fs_file.read(1024)
        superblock = _Superblock.from_bytes(superblock_data)

        # Check the superblock magic number to ensure this is an Ext2 filesystem
        if superblock.magic != 0xEF53:
            raise FilesystemError("Invalid superblock magic number.")

        return superblock

    def read_bgdt(self):
        # Compute the number of blocks required to hold the bgdt
        bgdt_blocks = self.bgdt_size // self.superblock.block_size
        if self.bgdt_size % self.superblock.block_size != 0:
            bgdt_blocks += 1

        # Read the bgdt blocks from the filesystem
        bgdt_data = b""
        for i in range(bgdt_blocks):
            self.fs_file.seek(self.bgdt_offset + i * self.superblock.block_size)
            bgdt_data += self.fs_file.read(self.superblock.block_size)

        # Parse the bgdt entries
        bgdt_entries = []
        for i in range(self.superblock.num_block_groups):
            offset = i * self.superblock.bgdt_entries_per_block
            for j in range(self.superblock.bgdt_entries_per_block):
                entry_data = bgdt_data[offset + j*32:offset + (j+1)*32]
                entry = _BlockGroupDescriptor.from_bytes(entry_data)
                bgdt_entries.append(entry)

        return _BlockGroupDescriptorTable(bgdt_entries)
