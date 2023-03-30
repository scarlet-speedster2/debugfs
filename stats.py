import os

# Constants
SUPERBLOCK_OFFSET = 1024
SUPERBLOCK_SIZE = 1024
BLOCK_GROUP_OFFSET = 2048
BLOCK_GROUP_SIZE = 32

# Helper functions
def read_bytes(fd, offset, size):
    fd.seek(offset)
    return fd.read(size)

def read_int(fd, offset, size):
    data = read_bytes(fd, offset, size)
    return int.from_bytes(data, byteorder='little')

# Main function
def display_ext2_info():
    with open("/dev/sda3", "rb") as fd:
        output = ""
        # Read superblock information
        inodes_count = read_int(fd, SUPERBLOCK_OFFSET + 0, 4)
        blocks_count = read_int(fd, SUPERBLOCK_OFFSET + 4, 4)
        free_blocks_count = read_int(fd, SUPERBLOCK_OFFSET + 12, 4)
        free_inodes_count = read_int(fd, SUPERBLOCK_OFFSET + 16, 4)
        block_size = read_int(fd, SUPERBLOCK_OFFSET + 24, 4)
        fragment_size = read_int(fd, SUPERBLOCK_OFFSET + 28, 4)
        blocks_per_group = read_int(fd, SUPERBLOCK_OFFSET + 32, 4)
        inodes_per_group = read_int(fd, SUPERBLOCK_OFFSET + 40, 4)
        first_data_block = read_int(fd, SUPERBLOCK_OFFSET + 20, 4)
        magic_number = read_int(fd, SUPERBLOCK_OFFSET + 56, 2)

        # Check if the magic number is correct
        if magic_number != 0xEF53:
            print("Error: Invalid ext2 filesystem")
            return

        # Calculate block group information
        block_group_count = (blocks_count - first_data_block) // blocks_per_group + 1
        block_group_size = block_group_count * BLOCK_GROUP_SIZE
        block_group_offset = SUPERBLOCK_OFFSET + SUPERBLOCK_SIZE
        output += f"SUPERBLOCK_OFFSET: {SUPERBLOCK_OFFSET}\n"
        output += f"SUPERBLOCK_SIZE: {SUPERBLOCK_SIZE}\n"
        output += f"BLOCK_GROUP_OFFSET: {BLOCK_GROUP_OFFSET}\n"
        output += f"BLOCK_GROUP_SIZE: {BLOCK_GROUP_SIZE}\n"
        output += f"fd: {fd}\n"
        output += f"inodes_count: {inodes_count}\n"
        output += f"blocks_count: {blocks_count}\n"
        output += f"free_blocks_count: {free_blocks_count}\n"
        output += f"free_inodes_count: {free_inodes_count}\n"
        output += f"block_size: {block_size}\n"
        output += f"fragment_size: {fragment_size}\n"
        output += f"blocks_per_group: {blocks_per_group}\n"
        output += f"inodes_per_group: {inodes_per_group}\n"
        output += f"first_data_block: {first_data_block}\n"
        output += f"magic_number: {magic_number}\n"
        output += f"block_group_count: {block_group_count}\n"
        output += f"block_group_size: {block_group_size}\n"
        output += f"block_group_offset: {block_group_offset}\n"

        # Read block group information
        for i in range(block_group_count):
            group_offset = block_group_offset + i * BLOCK_GROUP_SIZE
            blocks_in_group = blocks_per_group if i < block_group_count - 1 else blocks_count % blocks_per_group
            free_blocks_in_group = read_int(fd, group_offset + 12, 2)
            free_inodes_in_group = read_int(fd, group_offset + 14, 2)
            output += "Block Group {}:\n".format(i)
            output += "\tBlocks: {}-{}\n".format(i * blocks_per_group + 1, i * blocks_per_group + blocks_in_group)
            output += "\tFree blocks: {}\n".format(free_blocks_in_group)
            output += "\tFree inodes: {}\n".format(free_inodes_in_group)

        # Print filesystem information
    output += f"Inode count: {inodes_count}\n"
    output += f"Block count: {blocks_count}\n"
    output += f"Free blocks: {free_blocks_count}\n"
    output += f"Free inodes: {free_inodes_count}\n"
    output += f"Block size: {block_size}\n"
    output += f"Fragment size: {fragment_size}\n"
    return output

# Call the main function

