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
        self.blockPointers = list[12:]

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
        self.dirName = list[6]

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

    csvfile.close()
    exit(0)

if __name__ == "__main__":
    main()
