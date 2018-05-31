#!/usr/bin/env python

import sys

def getFileArg(args): # checks number of args and returns opened file
    usage_msg = "./lab3b CSV_FILE"
    if len(args) != 2:
        print("Wrong number of arguments.")
        print(usage_msg)
        exit(1)

    filename = args[1]
    try:
        return open(filename, "r")
    except IOError:
        print("Error: could not open file '%s'" %filename)
        exit(1)

def main():
    csvfile = getFileArg(sys.argv)

    
    csvfile.close()
    exit(0)

if __name__ == "__main__":
    main()
