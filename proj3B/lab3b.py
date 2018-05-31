#!/usr/bin/env python

import sys

def main():
    usage_msg = "./lab3b CSV_FILE"
    if len(sys.argv) != 2:
        print("Wrong number of arguments.")
        print(usage_msg)
        exit(1)

    csvfile = sys.argv[1]
    try:
        open(csvfile, "r")
    except IOError:
        print("Error: could not open file '%s'" %csvfile)
        exit(1)
    

if __name__ == "__main__":
    main()
