#!/usr/bin/env python

import sys

# Attempt to convert value to an int, return the int if possible,
# otherwise, just return value as is.
def tryIntConvert(value):
    try:
        return int(value)
    except ValueError:
        return value

def listConvert(str):
    return [tryIntConvert(a) for a in str.split(',')]

def initError(className, line):
    sys.stderr.write("Error initializing " + className + " line: " + line + "\n")

def getFileArg(args): # checks number of args and returns opened file
    usage_msg = "./lab3b CSV_FILE\n"
    if len(args) != 2:
        sys.stderr.write("Wrong number of arguments.\n")
        sys.stderr.write(usage_msg)
        exit(1)

    filename = args[1]
    try:
        return open(filename, "r")
    except IOError:
        sys.stderr.write("Error: could not open file '%s'\n" %filename)
        exit(1)

class Superblock:
    def __init__(self, line):
        self.name = "SUPERBLOCK"
        list = listConvert(line)
        if list[0] != self.name:
            initError(self.name, line)
            return
        self.numBlocks = list[1]
        self.numInodes = list[2]
        self.blockSize = list[3]
        self.nodeSize = list[4]
        self.blocksPerGroup = list[5]
        self.nodesPerGroup = list[6]
        self.firstInode = list[7]

class Group:
    def __init__(self, line):
        self.name = "GROUP"
        list = listConvert(line)
        if list[0] != self.name:
            initError(self.name, line)
            return
        self.groupNum = line[1]
        self.numBlocks = line[2]
        self.numInodes = line[3]
        self.numFreeBlocks = line[4]
        self.numFreeInodes = line[5]
        self.blockBitmapBlockNum = line[6]
        self.nodeBitmapBlockNum = line[7]
        self.firstInodeBlockNum = line[8]

class FreeBlock:
    def __init__(self, line):
        self.name = "BFREE"
        list = listConvert(line)
        if list[0] != self.name:
            initError(self.name, line)
            return
        self.numFreeBlock = list[1]

class FreeInode:
    def __init__(self, line):
        self.name = "IFREE"
        list = listConvert(line)
        if list[0] != self.name:
            initError(self.name, line)
            return
        self.numFreeInode = list[1]

class Inode:
    def __init__(self, line):
        self.name = "INODE"
        list = listConvert(line)
        if list[0] != self.name:
            initError(self.name, line)
            return
        self.inodeNum = list[1]
        self.fileType = list[2]
        self.mode = list[3]
        self.owner = list[4]
        self.group = list[5]
        self.linkCount = list[6]
        self.ctime = list[7]
        self.mtime = list[8]
        self.atime = list[9]
        self.fileSize = list[10]
        self.numBlocks = list[11]

class DirectoryEntry:
    def __init__(self, line):
        self.name = "DIRENT"
        list = listConvert(line)
        if list[0] != self.name:
            initError(self.name, line)
            return
        self.parentInodeNum = list[1]
        self.logicalByteOffset = list[2]
        self.inodeNum = list[3]
        self.entryLen = list[4]
        self.nameLen = list[5]
        self.name = list[6]

class IndirectBlock:
    def __init__(self, line):
        self.name = "INDIRECT"
        list = listConvert(line)
        if list[0] != self.name:
            initError(self.name, line)
            return
        self.inodeNum = list[1]
        self.indirectionLevel = list[2]
        self.logicalBlockOffset = list[3]
        self.indirBlockNum = list[4]
        self.refBlockNum = list[5]

class FileSystem:
    def __init__(self, csvFile):
        self.groups = []
        self.freeBlocks = []
        self.freeInodes = []
        self.inodes = []
        self.dirEntries = []
        self.indirectBlocks = []
        fsLines = [l.rstrip('\n') for l in csvFile]
        for line in fsLines:
            name = line.split(',')[0]
            if name == "SUPERBLOCK":
                self.superblock = Superblock(line)
            elif name == "GROUP":
                self.groups.append(Group(line))
            elif name == "BFREE":
                self.freeBlocks.append(FreeBlock(line))
            elif name == "IFREE":
                self.freeInodes.append(FreeInode(line))
            elif name == "INODE":
                self.inodes.append(Inode(line))
            elif name == "DIRENT":
                self.dirEntries.append(DirectoryEntry(line))
            elif name == "INDIRECT":
                self.indirectBlocks.append(IndirectBlock(line))
            else:
                sys.stderr.write("Unknown record name: " + name + "\n")

def main():
    csvfile = getFileArg(sys.argv)
    fs = FileSystem(csvfile)
    csvfile.close()
    exit(0)

if __name__ == "__main__":
    main()
