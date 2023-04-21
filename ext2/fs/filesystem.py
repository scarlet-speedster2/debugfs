

import inspect
from uuid import uuid4
from os import path, remove
from collections import deque
from struct import pack, unpack
from time import time
from math import ceil
from ..file.directory import _openRootDirectory
from ..error import FilesystemError
from .superblock import _Superblock
from .bgdt import _BGDT
from .inode import _Inode
from .device import _DeviceFromFile


class InformationReport(object):
  """Structure used to return information about the filesystem."""
  pass


class Ext2Filesystem(object):
  """Models a filesystem image file formatted to Ext2."""
  
  
  @property
  def fsType(self):
    """Gets a string representing the filesystem type. Always EXT2."""
    return "EXT2"
  
  @property
  def revision(self):
    """Gets the filesystem revision string formatted as MAJOR.MINOR."""
    if not self.isValid:
      raise FilesystemError("Filesystem is not valid.")
    return "{0}.{1}".format(self._superblock.revisionMajor, self._superblock.revisionMinor)
  
  @property
  def totalSpace(self):
    """Gets the total filesystem size in bytes."""
    if not self.isValid:
      raise FilesystemError("Filesystem is not valid.")
    return self._superblock.blockSize * self._superblock.numBlocks
  
  @property
  def freeSpace(self):
    """Gets the number of free bytes."""
    if not self.isValid:
      raise FilesystemError("Filesystem is not valid.")
    return self._superblock.blockSize * self._superblock.numFreeBlocks
  
  @property
  def usedSpace(self):
    """Gets the number of used bytes."""
    if not self.isValid:
      raise FilesystemError("Filesystem is not valid.")
    return self.totalSpace - self.freeSpace

  @property
  def totalFileSpace(self):
    """Gets the total number of bytes available for files."""
    if not self.isValid:
      raise FilesystemError("Filesystem is not valid.")
    bgdtBlocks = int(ceil(float(self._superblock.numBlockGroups * 32) // self._superblock.blockSize))
    inodeTableBlocks = int(ceil(float(self._superblock.numInodesPerGroup * self._superblock.inodeSize) // self._superblock.blockSize))
    numFileBlocks = (self._superblock.numBlocks - self._superblock.firstDataBlockId - inodeTableBlocks * self._superblock.numBlockGroups
                     - 2 * self._superblock.numBlockGroups - (1 + bgdtBlocks) * (len(self._superblock.copyLocations) + 1))
    return numFileBlocks * self._superblock.blockSize
  
  @property
  def blockSize(self):
    """Gets the block size in bytes."""
    if not self.isValid:
      raise FilesystemError("Filesystem is not valid.")
    return self._superblock.blockSize
  
  @property
  def numBlockGroups(self):
    """Gets the number of block groups."""
    if not self.isValid:
      raise FilesystemError("Filesystem is not valid.")
    return len(self._bgdt.entries)
  
  @property
  def numInodes(self):
    """Gets the total number of inodes."""
    if not self.isValid:
      raise FilesystemError("Filesystem is not valid.")
    return self._superblock.numInodes
  
  @property
  def rootDir(self):
    """Gets the file object representing the root directory."""
    if not self.isValid:
      raise FilesystemError("Filesystem is not valid.")
    return _openRootDirectory(self)

  @property
  def isValid(self):
    """Gets whether the filesystem is valid and mounted."""
    return self._isValid



  
  
  
  
  @classmethod
  def fromImageFile(cls, imageFilename):
    """Creates a new Ext2 filesystem from the specified image file."""
    return cls(_DeviceFromFile(imageFilename))
  
  def __init__(self, device):
    """Constructs a new Ext2 filesystem from the specified device object."""
    self._device = device
    self._isValid = False
  
  def __del__(self):
    """Destructor that unmounts the filesystem if it has not been unmounted."""
    if self._device.isMounted:
      self.unmount()
  
  def __enter__ (self):
    """Mounts the filesystem and returns the root directory."""
    self.mount()
    return self.rootDir

  def __exit__ (self, t, value, tb):
    """Unmounts the filesystem and re-raises any exception that occurred."""
    self.unmount()

  def mount(self):
    """Mounts the Ext2 filesystem for reading and writing and reads the root directory. Raises an
    error if the root directory cannot be read."""
    self._device.mount()
    try:
      self._superblock = _Superblock.read(1024, self._device)
      self._bgdt = _BGDT.read(0, self._superblock, self._device)
      self._isValid = True
      _openRootDirectory(self)
    except:
      if self._device.isMounted:
        self._device.unmount()
      self._isValid = False
      # raise FilesystemError("Root directory could not be read.")
      raise

  def unmount(self):
    """Unmounts the Ext2 filesystem so that reading and writing may no longer occur, and closes
    access to the device."""
    if self._device.isMounted:
      self._device.unmount()
    self._isValid = False

  def scanBlockGroups(self):
    """Scans all block groups and returns an information report about them."""
    assert self.isValid, "Filesystem is not valid."
    
    report = InformationReport()

    report.spaceUsed = 0
    
    # count files and directories
    report.numRegFiles = 0
    report.numSymlinks = 0
    report.numDirs = 1 # initialize with root directory
    q = deque([])
    q.append(self.rootDir)
    while len(q) > 0:
      d = q.popleft()
      for f in d.files():
        if f.name == "." or f.name == "..":
          continue
        for b in f._inode.usedBlocks():
          report.spaceUsed += self._superblock.blockSize
        if f.isDir:
          report.numDirs += 1
          q.append(f)
        elif f.isRegular:
          report.numRegFiles += 1
        elif f.isSymlink:
          report.numSymlinks += 1
    
    # report block group information
    report.groupReports = []
    for i,entry in enumerate(self._bgdt.entries):
      groupReport = InformationReport()
      groupReport.numFreeBlocks = entry.numFreeBlocks
      groupReport.numFreeInodes = entry.numFreeInodes
      groupReport.inodeBitmapLocation = entry.inodeBitmapLocation
      groupReport.blockBitmapLocation = entry.blockBitmapLocation
      groupReport.inodeTableLocation = entry.inodeTableLocation
      groupReport.numInodesAsDirs = entry.numInodesAsDirs
      report.groupReports.append(groupReport)
    
    return report
  
  
  

  def __getUsedInodes(self):
    """Returns a list of all used inode numbers, excluding those reserved by the
    filesystem."""
    used = []
    bitmaps = []
    for bgdtEntry in self._bgdt.entries:
      bitmapStartPos = bgdtEntry.inodeBitmapLocation * self._superblock.blockSize
      bitmapSize = self._superblock.numInodesPerGroup / 8
      bitmapBytes = self._device.read(bitmapStartPos, bitmapSize)
      if len(bitmapBytes) < bitmapSize:
        raise FilesystemError("Invalid inode bitmap.")
      bitmaps.append(unpack("{0}B".format(bitmapSize), bitmapBytes))
    
    for groupNum,bitmap in enumerate(bitmaps):
      for byteIndex, byte in enumerate(bitmap):
        if byte != 0:
          for i in range(8):
            if (1 << i) & byte != 0:
              inum = (groupNum * self._superblock.numInodesPerGroup) + (byteIndex * 8) + i + 1
              if inum >= self._superblock.firstInode:
                used.append(inum)
    
    return used

  
  def __getUsedBlocks(self):
    """Returns a list off all block ids currently in use by the filesystem."""
    used = []
    bitmaps = []
    for bgdtEntry in self._bgdt.entries:
      bitmapStartPos = bgdtEntry.blockBitmapLocation * self._superblock.blockSize
      bitmapSize = self._superblock.numBlocksPerGroup / 8
      bitmapBytes = self._device.read(bitmapStartPos, bitmapSize)
      if len(bitmapBytes) < bitmapSize:
        raise FilesystemError("Invalid block bitmap.")
      bitmaps.append(unpack("{0}B".format(bitmapSize), bitmapBytes))
        
    for groupNum,bitmap in enumerate(bitmaps):
      for byteIndex, byte in enumerate(bitmap):
        if byte != 0:
          for i in range(8):
            if (1 << i) & byte != 0:
              bid = (groupNum * self._superblock.numBlocksPerGroup) + (byteIndex * 8) + i + self._superblock.firstDataBlockId
              used.append(bid)
    
    return used
    

  def _readBlock(self, bid, offset = 0, count = None):
    """Reads from the block specified by the given block id and returns a string of bytes."""
    if not count:
      count = self._superblock.blockSize
    block = self._device.read(bid * self._superblock.blockSize + offset, count)
    if len(block) < count:
      raise FilesystemError("Invalid block.")
    return block

  def _readInode(self, inodeNum):
    """Reads the specified inode number and returns the inode object."""
    return _Inode.read(inodeNum, self._bgdt, self._superblock, self)
  
  




