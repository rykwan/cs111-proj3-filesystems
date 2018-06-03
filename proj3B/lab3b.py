#!/usr/bin/env python

import sys

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

def main():
    csvfile = getFileArg(sys.argv)

    
    csvfile.close()
    exit(0)

if __name__ == "__main__":
    main()
