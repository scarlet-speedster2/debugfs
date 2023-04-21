


from struct import pack, unpack, unpack_from
from time import time
from math import ceil
from ..error import FilesystemError


class _Inode(object):
  """Models an inode on the Ext2 fileystem. For internal use only."""


  @property
  def number(self):
    """Gets the inode number of this inode."""
    return self._num

  @property
  def isUsed(self):
    """Returns True if the inode is marked as used, False otherwise."""
    return self._used

  @property
  def timeCreated(self):
    """Gets the time this inode was created."""
    return self._timeCreated

  @property
  def flags(self):
    """Gets the flags bitmap for this inode."""
    return self._flags

  @property
  def blocks(self):
    """Gets the list of block ids used by the inode."""
    return self._blocks

  @property
  def numBlocks(self):
    """Gets the total number of blocks used by the inode."""
    return self._numDataBlocks
  
  @property
  def numDataBlocks(self):
    """Gets the number of blocks used for only data inside the inode."""
    return int(ceil(float(self._size) // self._superblock.blockSize))

  @property
  def mode(self):
    """Gets the mode bitmap."""
    return self._mode


  @property
  def uid(self):
    """Gets the uid of the inode's owner."""
    return self._uid

  @property
  def size(self):
    """Gets the size in bytes of the inode's file."""
    return self._size

  @property
  def timeAccessed(self):
    """Gets the time the inode was last accessed."""
    return self._timeAccessed
  @timeAccessed.setter
  def timeAccessed(self, value):
    """Sets the time the inode was last accessed."""
    self._timeAccessed = value
    self.__writeData(8, pack("<I", self._timeAccessed))

  @property
  def timeModified(self):
    """Gets the time the inode was last modified."""
    return self._timeModified
  @timeModified.setter
  def timeModified(self, value):
    """Sets the time the inode was last modified."""
    self._timeModified = value
    self.__writeData(16, pack("<I", self._timeModified))

  @property
  def timeDeleted(self):
    """Gets the time the inode was deleted."""
    return self._timeDeleted
  @timeDeleted.setter
  def timeDeleted(self, value):
    """Sets the time the inode was deleted."""
    self._timeDeleted = value
    self.__writeData(20, pack("<I", self._timeDeleted))

  @property
  def gid(self):
    """Gets the gid of the inode's owner."""
    return self._gid

  @property
  def numLinks(self):
    """Gets the number of hard links to the inode."""
    return self._numLinks
  @numLinks.setter
  def numLinks(self, value):
    """Sets the number of hard links to the inode."""
    self._numLinks = value
    self.__writeData(26, pack("<h", self._numLinks))

  def __init__(self, tableBid, inodeTableOffset, inodeBytes, isUsed, inodeNum, bgdtEntry, superblock, fs):
    """Constructs a new inode from the given byte array."""
    self._bgdtEntry = bgdtEntry
    self._tableBid = tableBid
    self._fs = fs
    self._superblock = superblock
    self._inodeTableOffset = inodeTableOffset

    if superblock.revisionMajor == 0:
      fields = unpack_from("<2Hi4IHh2I4x15I", inodeBytes)
    else:
      fields = unpack_from("<2H5IHh2I4x15I8xI", inodeBytes)

    osFields = []
    if superblock.creatorOS == "LINUX":
      osFields = unpack_from("<4x2H", inodeBytes, 116)
    elif superblock.creatorOS == "HURD":
      osFields = unpack_from("<2x3H", inodeBytes, 116)

    self._num = inodeNum
    self._used = isUsed
    self._mode = fields[0]
    self._uid = fields[1]
    self._size = fields[2]
    self._timeAccessed = fields[3]
    self._timeCreated = fields[4]
    self._timeModified = fields[5]
    self._timeDeleted = fields[6]
    self._gid = fields[7]
    self._numLinks = fields[8]
    self._numDataBlocks = fields[9] / (2 << self._superblock.logBlockSize)
    self._flags = fields[10]
    self._blocks = []
    for i in range(15):
      self._blocks.append(fields[11 + i])
    if superblock.revisionMajor > 0:
      self._size |= (fields[26] << 32)
    if superblock.creatorOS == "LINUX":
      self._uid |= (osFields[0] << 16)
      self._gid |= (osFields[1] << 16)
    elif superblock.creatorOS == "HURD":
      self._mode |= (osFields[0] << 16)
      self._uid |= (osFields[1] << 16)
      self._gid |= (osFields[2] << 16)

    self._numIdsPerBlock = self._superblock.blockSize / 4
    self._numDirectBlocks = 12
    self._numIndirectBlocks = self._numDirectBlocks + self._numIdsPerBlock
    self._numDoublyIndirectBlocks = self._numIndirectBlocks + self._numIdsPerBlock ** 2
    self._numTreblyIndirectBlocks = self._numDoublyIndirectBlocks + self._numIdsPerBlock ** 3

  @classmethod
  def read(cls, inodeNum, bgdt, superblock, fs):
    """Reads the inode with the specified inode number and returns the new object."""

    #bgroupNum = (inodeNum - 1) / superblock.numInodesPerGroup
    bgroupNum = (inodeNum - 1) // superblock.numInodesPerGroup
    bgroupIndex = (inodeNum - 1) % superblock.numInodesPerGroup
    bgdtEntry = bgdt.entries[bgroupNum]

    bitmapByteIndex = bgroupIndex // 8
    tableBid = bgdtEntry.inodeTableLocation + (bgroupIndex * superblock.inodeSize) // fs.blockSize
    inodeTableOffset = (bgroupIndex * superblock.inodeSize) % fs.blockSize
    
    bitmapByte = unpack("B", fs._readBlock(bgdtEntry.inodeBitmapLocation, bitmapByteIndex, 1))[0]
    inodeBytes = fs._readBlock(tableBid, inodeTableOffset, superblock.inodeSize)
    if len(inodeBytes) < superblock.inodeSize:
      raise FilesystemError("Invalid inode.")

    isUsed = (bitmapByte & (1 << (bgroupIndex % 8)) != 0)
    return cls(tableBid, inodeTableOffset, inodeBytes, isUsed, inodeNum, bgdtEntry, superblock, fs)

  def usedBlocks(self):
    """Generates a list of all block ids in use by the inode, including data
    and indirect blocks."""
    
    # get direct blocks
    for i in range(12):
      bid = self.blocks[i]
      if bid == 0:
        break
      yield bid

    # get indirect blocks
    if self.blocks[12] != 0:
      for bid in self.__getBidListAtBid(self.blocks[12]):
        if bid == 0:
          break
        yield bid
      yield self.blocks[12]

    # get doubly indirect blocks
    if self.blocks[13] != 0:
      for indirectBid in self.__getBidListAtBid(self.blocks[13]):
        if indirectBid == 0:
          break
        for bid in self.__getBidListAtBid(indirectBid):
          if bid == 0:
            break
          yield bid
        yield indirectBid
      yield self.blocks[13]

    # get trebly indirect blocks
    if self.blocks[14] != 0:
      for doublyIndirectBid in self.__getBidListAtBid(self.blocks[14]):
        if doublyIndirectBid == 0:
          break
        for indirectBid in self.__getBidListAtBid(doublyIndirectBid):
          if indirectBid == 0:
            break
          for bid in self.__getBidListAtBid(indirectBid):
            if bid == 0:
              break
            yield bid
          yield indirectBid
        yield doublyIndirectBid
      yield self.blocks[14]




  def lookupBlockId(self, index):
    """Looks up the block id corresponding to the block at the specified index,
    where the block index is the absolute block number within the data."""
    
    if index >= self._numDataBlocks:
      return 0
    
    try:
      if index < self._numDirectBlocks:
        return self.blocks[index]

      elif index < self._numIndirectBlocks:
        directList = self.__getBidListAtBid(self.blocks[12])
        return directList[index - self._numDirectBlocks]

      elif index < self._numDoublyIndirectBlocks:
        indirectList = self.__getBidListAtBid(self.blocks[13])
        index -= self._numIndirectBlocks # get index from start of doubly indirect list
        directList = self.__getBidListAtBid(indirectList[index / self._numIdsPerBlock])
        return directList[index % self._numIdsPerBlock]

      elif index < self._numTreblyIndirectBlocks:
        doublyIndirectList = self.__getBidListAtBid(self.blocks[14])
        index -= self._numDoublyIndirectBlocks # get index from start of trebly indirect list
        indirectList = self.__getBidListAtBid(doublyIndirectList[index / (self._numIdsPerBlock ** 2)])
        index %= (self._numIdsPerBlock ** 2) # get index from start of indirect list
        directList = self.__getBidListAtBid(indirectList[index / self._numIdsPerBlock])
        return directList[index % self._numIdsPerBlock]
      
      return 0
    except IndexError:
      return 0
  
  
  
  def assignStringToBlocks(self, path):
    """Assigns the specified string to the block data."""
    pathBytes = pack("<{0}s{1}x".format(len(path), 60 - len(path)), path)
    self.__writeData(40, pathBytes)
    self._blocks = list(unpack_from("<15I", pathBytes))


  def getStringFromBlocks(self):
    """Reads and returns block data as a string."""
    pathBytes = self._fs._readBlock(self._tableBid, self._inodeTableOffset + 40, self._size)
    return unpack_from("<{0}s".format(self._size), pathBytes)[0]




  def __getBidListAtBid(self, bid):
    """Reads and returns the list of block ids at the specified block id."""
    return list(unpack_from("<{0}I".format(self._numIdsPerBlock), self._fs._readBlock(bid)))


