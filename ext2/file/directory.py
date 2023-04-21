

import re
from struct import pack, unpack_from
from time import time
from ..error import *
from .file import Ext2File

from .regularfile import Ext2RegularFile


def _openRootDirectory(fs):
  """Opens and returns the root directory of the specified filesystem."""
  return Ext2Directory._openEntry(None, fs)


class _EntryList(object):
  """Represents a doubly-liked directory list in the Ext2 filesystem. For internal use only."""
  
  def __init__(self, containingDir):
    """Constructs a new directory entry list for the specified directory."""
    self._containingDir = containingDir
    self._entries = []
    prevEntry = None
    for i in range(containingDir.numBlocks):
      blockId = containingDir._inode.lookupBlockId(i)
      if blockId == 0:
        break
      blockBytes = containingDir._fs._readBlock(blockId)
      offset = 0
      while offset < containingDir._fs.blockSize:
        entry = _Entry(i, blockId, offset, prevEntry, blockBytes[offset:], containingDir)
        if entry.inodeNum == 0:
          break
        prevEntry = entry
        offset += entry.size
        self._entries.append(entry)
  
  
  def __iter__(self):
    """Gets the iterator to this list."""
    self._itIndex = 0
    return self
  
  
  def __next__(self):
    """Gets the next entry in the linked list."""
    if self._itIndex == len(self._entries):
      raise StopIteration
    entry = self._entries[self._itIndex]
    self._itIndex += 1
    return entry
  


class _Entry(object):
  """Represents a directory entry in a linked entry list on the Ext2 filesystem. For internal use only."""

  @property
  def size(self):
    """Gets the size of this entry in bytes."""
    return self._size

  @property
  def containingDir(self):
    """Gets the directory object that contains this entry."""
    return self._containingDir
  
  @property
  def name(self):
    """Gets the name of the file represented by this entry."""
    return self._name

  @property
  def inodeNum(self):
    """Gets the inode number of the file represented by this entry."""
    return self._inodeNum
  @inodeNum.setter
  def inodeNum(self, value):
    """Sets the inode number of the file represented by this entry."""
    self._inodeNum = value
    self.__writeData(0, pack("<I", self._inodeNum))

  @property
  def prevEntry(self):
    """Gets the previous entry in the list."""
    return self._prevEntry
  @prevEntry.setter
  def prevEntry(self, value):
    """Sets the previous entry in the list."""
    self._prevEntry = value
  
  @property
  def nextEntry(self):
    """Gets the next entry in the list."""
    return self._nextEntry
  @nextEntry.setter
  def nextEntry(self, value):
    """Sets the next entry in the list."""
    if value is None:
      if self.size + self._offset + 4 <= self._containingDir._fs.blockSize:
        self.__writeData(self.size, pack("<I", 0))
    else:
      if value._bindex == self._bindex:
        newSize = value._offset - self._offset
        if not newSize > 0:
          raise FilesystemError("Next entry not after previous entry.")
      else:
        newSize = self._containingDir._fs.blockSize - self._offset + value._offset
      self.__writeData(4, pack("<H", newSize))
    self._nextEntry = value

  
  def __init__(self, blockIndex, blockId, blockOffset, prevEntry, byteString, containingDir):
    """Contructs a new entry in the linked list."""
    
    if containingDir._fs._superblock.revisionMajor == 0:
      fields = unpack_from("<IHH", byteString)
      self._fileType = 0
    else:
      fields = unpack_from("<IHBB", byteString)
      self._fileType = fields[3]
    
    self._name = unpack_from("<{0}s".format(fields[2]), byteString, 8)[0]
    self._inodeNum = fields[0]
    self._size = fields[1]
    self._bindex = blockIndex
    self._bid = blockId
    self._offset = blockOffset
    self._containingDir = containingDir
    self._nextEntry = None
    self._prevEntry = prevEntry
    if not (self._inodeNum == 0 or self._prevEntry is None):
      self._prevEntry._nextEntry = self
  


    




class Ext2Directory(Ext2File):
  """Represents a directory on the Ext2 filesystem."""

  @property
  def isDir(self):
    """Gets whether the file object is a directory."""
    return True


  def __init__(self, dirEntry, inode, fs):
    """Constructs a new directory object from the specified directory entry."""
    super(Ext2Directory, self).__init__(dirEntry, inode, fs)
    if (self._inode.mode & 0x4000) != 0x4000:
      raise FilesystemError("Inode does not point to a directory.")
    self._entryList = _EntryList(self)



  @classmethod
  def _openEntry(cls, dirEntry, fs):
    """Opens and returns the file object described by the specified directory entry."""
    if dirEntry:
      assert dirEntry.inodeNum != 0
      inode = fs._readInode(dirEntry.inodeNum)
    else:
      inode = fs._readInode(2)
    
    if (inode.mode & 0x4000) == 0x4000:
      return Ext2Directory(dirEntry, inode, fs)
    if (inode.mode & 0xA000) == 0xA000:
      return Ext2Symlink(dirEntry, inode, fs)
    if (inode.mode & 0x8000) == 0x8000:
      return Ext2RegularFile(dirEntry, inode, fs)

    return Ext2File(dirEntry, inode, fs)



  def files(self):
    """Generates a list of files in the directory."""
    for entry in self._entryList:
      yield Ext2Directory._openEntry(entry, self._fs)



  def getFileAt(self, relativePath, followSymlinks = False):
    """Looks up and returns the file specified by the relative path from this directory. Raises a
    FileNotFoundError if the file cannot be found."""
    
    #pathParts = re.compile("/+").split(relativePath)
    pathParts = re.compile(b"/+").split(relativePath)
    if len(pathParts) > 1 and pathParts[0] == "":
      del pathParts[0]
    if len(pathParts) > 1 and pathParts[-1] == "":
      del pathParts[-1]
    if len(pathParts) == 0:
      raise FileNotFoundError()
    if len(pathParts[0]) == 0:
      return self
    
    curFile = self
    for curPart in pathParts:
      if curFile.isDir:
        found = False
        for entry in curFile._entryList:
          if entry.name == curPart:
            curFile = Ext2Directory._openEntry(entry, self._fs)
            while curFile.isSymlink and followSymlinks:
              linkedPath = curFile.getLinkedPath()
              if linkedPath.startswith(b"/"):
                curFile = self._fs.rootDir.getFileAt(linkedPath[1:])
              else:
                curFile = curFile.parentDir.getFileAt(linkedPath)
            found = True
            break
        if not found:
          raise FileNotFoundError()
    
    if curFile.absolutePath == self.absolutePath:
      return self
    
    return curFile


