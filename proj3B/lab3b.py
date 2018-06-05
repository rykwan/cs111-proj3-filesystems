#!/usr/bin/env python

import sys

# Attempt to convert value to an int, return the int if possible,
# otherwise, just return value as is.
def tryIntConvert(value):
    try:
        return int(value)
    except ValueError:
        return value

# Convert comma separated string into list, converting strings to
# ints where applicable
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

"""
FileSystem and Related Classes
"""

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
        self.blockPointers = []
        if self.fileType != 's':
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
        self.dirName = linelist[6]

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
    inodes = {} # Map inode number to boolean representing whether it has been allocated
    allocList = set() # Contains allocated inodes
    freeList = set() # Contains free inodes

    # Populate allocList set
    for ai in fs.inodes:
        allocList.add(ai.inodeNum)

    # Populate freeList set
    for fi in fs.freeInodes:
        freeList.add(fi.numFreeInode)

    # Hard code for root inode
    inodes[2] = True if 2 in allocList else False

    # Populate inodes map
    for i in range(fs.superblock.firstInode, fs.superblock.numInodes+1):
        inodes[i] = True if i in allocList else False

    # Check for allocated inodes on freelist
    for inodeNum in allocList:
        if inodeNum in freeList:
            sys.stdout.write("ALLOCATED INODE " + str(inodeNum) + " ON FREELIST\n")

    # Check for unallocated inodes not on freelist
    for inodeNum in inodes:
        if (inodes[inodeNum] == False and inodeNum not in freeList):
            sys.stdout.write("UNALLOCATED INODE " + str(inodeNum) + " NOT ON FREELIST\n")

class BlockObject:
    def __init__(self, blockNum, inoNum, indirection, offset):
        self.blockNum = blockNum
        self.inodeNum = inoNum
        self.indirection = indirection
        self.offset = offset

def reportInconsistentBlock(INorREorDU, blockno, indi, inonum, offset): # 0 for invalid, 1 for reserved
    if INorREorDU == 0:
        sys.stdout.write("INVALID ")
    elif INorREorDU == 1:
        sys.stdout.write("RESERVED ")
    else:
        sys.stdout.write("DUPLICATE ")
    
    if indi == 2:
        sys.stdout.write("DOUBLE ")
    elif indi == 3:
        sys.stdout.write("TRIPLE ")
    if indi >= 1:  #TODO: how to get logical offset
        sys.stdout.write("INDIRECT ")

    sys.stdout.write("BLOCK %d IN INODE %d AT OFFSET %d\n" % (blockno, inonum, offset) )

def blockAudit(fs):
    startingBlock = fs.groups[0].firstInodeBlockNum + (fs.superblock.nodeSize * fs.groups[0].numInodes) / fs.superblock.blockSize

    allBlocks = dict((b, []) for b in range(int(startingBlock),fs.superblock.numBlocks) )

    for frb in fs.freeBlocks:
        allBlocks[frb.numFreeBlock] = None # set free blocks to None

    for ino in fs.inodes:
        offset = 0
        for (idx, bp) in enumerate(ino.blockPointers):
            indirection = idx - 11 # indirection: 1 for indirect, 2 for double, 3 for triple

            if indirection == 1:
                offset = 12
            elif indirection == 2:
                offset = 268
            elif indirection == 3:
                offset = 65804

            if bp in allBlocks:
                if allBlocks[bp] == None:
                    sys.stdout.write("ALLOCATED BLOCK %d ON FREELIST\n" % bp)
                    allBlocks[bp] = []

            if bp < 0 or bp > fs.superblock.numBlocks:
                reportInconsistentBlock(0, bp, indirection, ino.inodeNum, offset)
            elif bp == fs.groups[0].blockBitmapBlockNum or bp == fs.groups[0].nodeBitmapBlockNum or (bp != 0 and bp < int(fs.groups[0].firstInodeBlockNum)):
                reportInconsistentBlock(1, bp, indirection, ino.inodeNum, offset)
            elif bp != 0:
                allBlocks.setdefault(bp,[]).append(BlockObject(bp, ino.inodeNum, indirection, offset))

            offset+=1

    for indiBlock in fs.indirectBlocks:
        if indiBlock.refBlockNum in allBlocks:
            if allBlocks[indiBlock.refBlockNum] == None:
                sys.stdout.write("ALLOCATED BLOCK %d ON FREELIST\n" % indiBlock.refBlockNum)
                allBlocks[indiBlock.refBlockNum] = []
        if indiBlock.refBlockNum < 0 or indiBlock.refBlockNum > fs.superblock.numBlocks:
                reportInconsistentBlock(0, indiBlock.refBlockNum, indiBlock.indirectionLevel, indiBlock.inodeNum, indiBlock.logicalBlockOffset)
        elif indiBlock.refBlockNum == fs.groups[0].blockBitmapBlockNum or indiBlock.refBlockNum == fs.groups[0].nodeBitmapBlockNum or (indiBlock.refBlockNum != 0 and indiBlock.refBlockNum < int(fs.groups[0].firstInodeBlockNum)):
                reportInconsistentBlock(1, indiBlock.refBlockNum, indiBlock.indirectionLevel, indiBlock.inodeNum, indiBlock.logicalBlockOffset)
        elif indiBlock.refBlockNum != 0:
                allBlocks.setdefault(indiBlock.refBlockNum,[]).append(BlockObject(indiBlock.refBlockNum, indiBlock.inodeNum, indiBlock.indirectionLevel, offset))

    for b in range(int(startingBlock),fs.superblock.numBlocks):
        if allBlocks[b] == None:
            continue
        if len(allBlocks[b]) == 0:
            sys.stdout.write("UNREFERENCED BLOCK %d\n" % b)
        elif len(allBlocks[b]) > 1:
            for block in allBlocks[b]:
                reportInconsistentBlock(2, block.blockNum, block.indirection, block.inodeNum, block.offset)




def directoryAudit(fs):
    inodes = {} # Map inode number to number of links it has
    allocList = set() # Contains allocated inodes

    # Populate allocList
    for ai in fs.inodes:
        allocList.add(ai.inodeNum)

    # Initialize inode map to all 0's
    for i in range(1, fs.superblock.numInodes+1):
        inodes[i] = 0

    # Populate inodes map
    for e in fs.dirEntries:
        if e.inodeNum in inodes:
            inodes[e.inodeNum]+=1
        else:
            inodes[e.inodeNum] = 1

    # Check for link and linkcount mismatch
    for i in fs.inodes:
        if i.linkCount != inodes[i.inodeNum]:
            sys.stdout.write("INODE " + str(i.inodeNum) + " HAS " + str(inodes[i.inodeNum]) + " LINKS BUT LINKCOUNT IS " + str(i.linkCount) + "\n")

    # Check for unallocated or invalid inodes
    for e in fs.dirEntries:
        if e.inodeNum < 1 or e.inodeNum > fs.superblock.numInodes:
            sys.stdout.write("DIRECTORY INODE " + str(e.parentInodeNum) + " NAME " + str(e.dirName) + " INVALID INODE " + str(e.inodeNum) + "\n")
        elif not e.inodeNum in allocList:
            sys.stdout.write("DIRECTORY INODE " + str(e.parentInodeNum) + " NAME " + str(e.dirName) + " UNALLOCATED INODE " + str(e.inodeNum) + "\n")

    # Check that . directories are consistent
    for e in fs.dirEntries:
        if e.dirName == "'.'" and e.parentInodeNum != e.inodeNum:
            sys.stdout.write("DIRECTORY INODE " + str(e.parentInodeNum) + " NAME " + str(e.dirName) + " LINK TO INODE " + str(e.inodeNum) + " SHOULD BE " + str(e.parentInodeNum) + "\n")

    # Returns True if given inode number is a directory, false otherwise
    def isDirectory(inodeno):
        for i in fs.inodes:
            if i.inodeNum == inodeno:
                return i.fileType == 'd'
        return False

    # Manually check root ..
    for e in fs.dirEntries:
        if e.dirName == "'..'" and e.parentInodeNum == 2:
            if e.inodeNum != 2:
                sys.stdout.write("DIRECTORY INODE 2 NAME '..' LINK TO INODE " + str(e.inodeNum) + " SHOULD BE 2\n")

    # Check that .. directories are consistent
    for e in fs.dirEntries:
        parentDirNum = e.parentInodeNum
        dirNum = e.inodeNum
        if e.dirName != "'..'" and e.dirName != "'.'" and isDirectory(dirNum):
            for en in fs.dirEntries:
                if en.dirName == "'..'" and en.parentInodeNum == dirNum:
                    if en.inodeNum != parentDirNum:
                        sys.stdout.write("DIRECTORY INODE " + str(en.parentInodeNum) + " NAME " + str(en.dirName) + " LINK TO INODE " + str(en.inodeNum) + " SHOULD BE " + str(parentDirNum) + "\n")


def main():
    csvfile = getFileArg(sys.argv)

    fs = FileSystem(csvfile)
    inodeAudit(fs)
    directoryAudit(fs)

    blockAudit(fs)

    csvfile.close()
    exit(0)

if __name__ == "__main__":
    main()
