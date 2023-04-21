
from ..error import FilesystemError
from .file import Ext2File


class Ext2RegularFile(Ext2File):
  """Represents a regular file on the Ext2 filesystem."""

  @property
  def isRegular(self):
    """Gets whether the file object is a regular file."""
    return True
  
  def __init__(self, dirEntry, inode, fs):
    """Constructs a new regular file object from the specified directory entry."""
    super(Ext2RegularFile, self).__init__(dirEntry, inode, fs)
    if (self._inode.mode & 0x8000) != 0x8000:
      raise FilesystemError("Inode does not point to a regular file.")


  def blocks(self):
    """Generates a list of data blocks in the file."""
    for i in range(self.numBlocks):
      blockId = self._inode.lookupBlockId(i)
      if blockId == 0:
        break
      block = self._fs._readBlock(blockId)
      if (i+1) * self._fs.blockSize > self.size:
        block = block[:(self.size % self._fs.blockSize)]
      yield block


      
    
