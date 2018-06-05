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
        linelist = listConvert(line)
        if linelist[0] != self.name:
            initError(self.name, line)
            return
        self.numBlocks = linelist[1]
        self.numInodes = linelist[2]
        self.blockSize = linelist[3]
        self.nodeSize = linelist[4]
        self.blocksPerGroup = linelist[5]
        self.nodesPerGroup = linelist[6]
        self.firstInode = linelist[7]

class Group:
    def __init__(self, line):
        self.name = "GROUP"
        linelist = listConvert(line)
        if linelist[0] != self.name:
            initError(self.name, line)
            return
        self.groupNum = linelist[1]
        self.numBlocks = linelist[2]
        self.numInodes = linelist[3]
        self.numFreeBlocks = linelist[4]
        self.numFreeInodes = linelist[5]
        self.blockBitmapBlockNum = linelist[6]
        self.nodeBitmapBlockNum = linelist[7]
        self.firstInodeBlockNum = linelist[8]

class FreeBlock:
    def __init__(self, line):
        self.name = "BFREE"
        linelist = listConvert(line)
        if linelist[0] != self.name:
            initError(self.name, line)
            return
        self.numFreeBlock = linelist[1]

class FreeInode:
    def __init__(self, line):
        self.name = "IFREE"
        linelist = listConvert(line)
        if linelist[0] != self.name:
            initError(self.name, line)
            return
        self.numFreeInode = linelist[1]

class Inode:
    def __init__(self, line):
        self.name = "INODE"
        linelist = listConvert(line)
        if linelist[0] != self.name:
            initError(self.name, line)
            return
        self.inodeNum = linelist[1]
        self.fileType = linelist[2]
        self.mode = linelist[3]
        self.owner = linelist[4]
        self.group = linelist[5]
        self.linkCount = linelist[6]
        self.ctime = linelist[7]
        self.mtime = linelist[8]
        self.atime = linelist[9]
        self.fileSize = linelist[10]
        self.numBlocks = linelist[11]
        self.blockPointers = linelist[12:]

class DirectoryEntry:
    def __init__(self, line):
        self.name = "DIRENT"
        linelist = listConvert(line)
        if linelist[0] != self.name:
            initError(self.name, line)
            return
        self.parentInodeNum = linelist[1]
        self.logicalByteOffset = linelist[2]
        self.inodeNum = linelist[3]
        self.entryLen = linelist[4]
        self.nameLen = linelist[5]
        self.name = linelist[6]

class IndirectBlock:
    def __init__(self, line):
        self.name = "INDIRECT"
        linelist = listConvert(line)
        if linelist[0] != self.name:
            initError(self.name, line)
            return
        self.inodeNum = linelist[1]
        self.indirectionLevel = linelist[2]
        self.logicalBlockOffset = linelist[3]
        self.indirBlockNum = linelist[4]
        self.refBlockNum = linelist[5]

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

def inodeAudit(fs):
    inodes = {}
    allocList = {}
    freeList = {}

    for ai in fs.inodes:
        allocList[ai.inodeNum] = True

    for fi in fs.freeInodes:
        freeList[fi.numFreeInode] = True

    for i in range(1, fs.superblock.numInodes):
        if i in allocList:
            inodes[i] = True
        else:
            inodes[i] = False

    for inodeNum in allocList:
        if inodeNum in freeList:
            sys.stdout.write("ALLOCATED INODE " + str(inodeNum) + " ON FREELIST\n")

    for inodeNum in inodes:
        if (inodes[inodeNum] == False and inodeNum not in freeList):
            sys.stdout.write("UNALLOCATED INODE " + str(inodeNum) + " NOT ON FREELIST\n")

class BlockObject:
    def __init__(self, blockNum, inoNum, indirection):
        self.blockNum = blockNum
        self.inodeNum = inoNum
        self.indirection = indirection

def printInvalidOrReservedBlock(INorRE, blockno, idx, inonum): # 0 for invalid, 1 for reserved
    offset = 0
    if INorRE == 0:
        sys.stdout.write("INVALID ")
    else:
        sys.stdout.write("RESERVED ")
    if idx == 12:  #TODO: how to get logical offset
        sys.stdout.write("INDIRECT ")
    elif idx == 13:
        sys.stdout.write("DOUBLE ")
    elif idx == 14:
        sys.stdout.write("TRIPLE ")
    sys.stdout.write("BLOCK %d IN INODE %d AT OFFSET %d\n" % (blockno, inonum, offset) )

def blockAudit(fs):
    allBlocks = dict((b, []) for b in range(1,fs.superblock.numBlocks+1) )

    for frb in fs.freeBlocks:
        allBlocks[frb.numFreeBlock] = None # set free blocks to None

    for ino in fs.inodes:
        for (idx, bp) in enumerate(ino.blockPointers):
            indirection = idx - 11 # indirection: 1 for indirect, 2 for double, 3 for triple
            if bp in allBlocks:
                if allBlocks[bp] == None:
                    sys.stdout.write("ALLOCATED %d ON FREELIST\n" % bp)
                    allBlocks[bp] = []

            if bp < 0 or bp > fs.superblock.numBlocks:
                printInvalidOrReservedBlock(0, bp, idx, ino.inodeNum)
            elif bp == fs.groups[0].blockBitmapBlockNum or bp == fs.groups[0].nodeBitmapBlockNum or (bp != 0 and bp < int(fs.groups[0].firstInodeBlockNum)):
                printInvalidOrReservedBlock(1, bp, idx, ino.inodeNum)
            elif bp != 0:
                allBlocks.setdefault(bp,[]).append(BlockObject(bp, ino.inodeNum, indirection))

   # for b in range(1,fs.superblock.numBlocks+1):
   #     if allBlocks[b] 





def main():
    csvfile = getFileArg(sys.argv)

    fs = FileSystem(csvfile)
    inodeAudit(fs)

    blockAudit(fs)

    csvfile.close()
    exit(0)

if __name__ == "__main__":
    main()
