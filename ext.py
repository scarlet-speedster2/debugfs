
import sys
import os
from time import sleep, perf_counter
from threading import Thread
from collections import deque
from ext2 import *







def printDirectory(directory, recursive, showAll, longList, showTypeCharacters, showInodeNums, useTimeAccess,
                   useTimeCreation):

    if not directory.fsType == "EXT2":
        raise FilesystemNotSupportedError()
    op = []
    q = deque([])
    q.append(directory)
    while len(q) > 0:
        d = q.popleft()
        files = []
        maxInodeLen = 0
        maxSizeLen = 0
        maxUidLen = 0
        maxGidLen = 0
        for f in d.files():
            # if not showAll and f.name.startswith("."):
            # continue
            # if f.isDir and f.name != "." and f.name != "..":
            if f.isDir:
                if recursive:
                    q.append(f)
            files.append(f)
            if longList:
                maxInodeLen = max(len(str(f.inodeNum)), maxInodeLen)
                maxSizeLen = max(len(str(f.size)), maxSizeLen)
                maxUidLen = max(len(str(f.uid)), maxUidLen)
                maxGidLen = max(len(str(f.gid)), maxGidLen)

        files = sorted(files, key=lambda f: f.name)

        if recursive:
            print("{0}:".format(d.absolutePath))

        for f in files:

            if not longList:
                name = f.name
                if showTypeCharacters:
                    if f.isDir:
                        name = "{0}/".format(name)
                    elif f.isSymlink:
                        name = "{0}@".format(name)
                    elif f.isRegular and f.isExecutable:
                        name = "{0}*".format(name)
                print(name)

            else:
                inodeStr = ""
                name = f.name
                if showTypeCharacters:
                    if f.isDir:
                        name = "{0}/".format(name)
                    elif f.isSymlink:
                        name = "{0}@".format(name)
                    elif f.isRegular and f.isExecutable:
                        name = "{0}*".format(name)

                if f.isSymlink:
                    name = "{0} -> {1}".format(name, f.getLinkedPath())

                if showInodeNums:
                    inodeStr = "{0} ".format(f.inodeNum).rjust(maxInodeLen + 1)

                numLinks = "{0}".format(f.numLinks).rjust(2)
                uid = "{0}".format(f.uid).rjust(maxUidLen)
                gid = "{0}".format(f.gid).rjust(maxGidLen)
                size = "{0}".format(f.size).rjust(maxSizeLen)
                if useTimeAccess:
                    time = f.timeAccessed.ljust(17)
                elif useTimeCreation:
                    time = f.timeCreated.ljust(17)
                else:
                    time = f.timeModified.ljust(17)
                #s = "{0}{1} {2} {3} {4} {5} {6} {7}".format(inodeStr, f.modeStr, numLinks, uid, gid, size, time, name).split()
                s = [str(name)[2:],inodeStr.strip(), f.modeStr, numLinks, uid, gid, size.strip(), time]
                op.append(s)


                # print(
                #     "{0}{1} {2} {3} {4} {5} {6} {7}".format(inodeStr, f.modeStr, numLinks, uid, gid, size, time, name))
        return op



def getFileObject(fs, directory, path, followSymlinks):
    """Looks up the file object specified by the given absolute path or the path relative to the specified directory."""
    try:
        if path == "/":
            fileObject = fs.rootDir
        # elif path.startswith("/"):
        elif path.startswith(b"/"):
            fileObject = fs.rootDir.getFileAt(path[1:], followSymlinks)
        else:
            fileObject = directory.getFileAt(path, followSymlinks)
    except FileNotFoundError:
        raise FilesystemError("{0} does not exist.".format(path))
    if fileObject.absolutePath == directory.absolutePath:
        fileObject = directory
    return fileObject


def parseNewPath(fs, directory, path):

    parentDir = directory
    if path.startswith(b"/"):
        path = path[1:]
        parentDir = fs.rootDir
        if parentDir.absolutePath == directory.absolutePath:
            parentDir = directory
    # if "/" in path:
    if b"/" in path:
        name = path[path.rindex("/") + 1:]
        parentDir = getFileObject(fs, directory, path[:path.rindex("/")], True)
    else:
        name = path
    return (parentDir, name)


def shell(fs,workingDir,inputline):

    def __parseInput(inputline):
        # print(type(inputline))

        parts = deque(inputline.split())
        cmd = parts.popleft()
        flags = []
        parameters = []

        while len(parts) > 0:
            part = parts.popleft()

            if part.startswith("-") and len(parameters) == 0:
                flags.extend(list(part[1:]))

            elif part.startswith("\"") or part.startswith("\'"):
                quoteChar = part[0]
                param = part[1:]
                nextPart = part
                while not nextPart.endswith(quoteChar) and len(parts) > 0:
                    nextPart = parts.popleft()
                    param = "{0} {1}".format(param, nextPart)


                parameters.append(bytes(param[:-1], encoding='utf-8'))

            elif part.endswith("\\"):
                param = ""
                nextPart = part
                while nextPart.endswith("\\") and len(parts) > 0:
                    param = "{0} {1}".format(param, nextPart[:-1])
                    nextPart = parts.popleft()
                param = "{0} {1}".format(param, nextPart)
                parameters.append(bytes(param.strip(), encoding='utf-8'))

            else:
                parameters.append(bytes(part, encoding='utf-8'))

        return (cmd, flags, parameters)

    while True:
        #inputline = input(": '{0}' >> ".format(workingDir.absolutePath)).rstrip()
        if len(inputline) == 0:
            continue

        try:
            parsed = __parseInput(inputline)
            cmd = parsed[0]
            flags = parsed[1]
            parameters = parsed[2]

            if cmd == "exit":
                break

            elif cmd == "pwd":
                return (workingDir.absolutePath)
                

            elif cmd == "ls":
                if len(parameters) == 0:
                    return printDirectory(workingDir, "R" in flags, "a" in flags, "l" in flags, "F" in flags,
                                   "i" in flags, "u" in flags, "U" in flags),workingDir
                elif len(parameters) == 1:
                    lsDir = getFileObject(fs, workingDir, parameters[0], True)
                    return printDirectory(lsDir, "R" in flags, "a" in flags, "l" in flags, "F" in flags,
                                   "i" in flags, "u" in flags, "U" in flags),workingDir


            elif cmd == "cd":

                cdDir = getFileObject(fs, workingDir, parameters[0], True)
                if not cdDir.isDir:
                    cdDir = getFileObject(fs,workingDir,'..',True)
                workingDir = cdDir
                return workingDir,workingDir
        except Exception as e:
            print(e)





