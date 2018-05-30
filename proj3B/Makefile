#NAME: Raymond Kwan,Sanketh Hedge
#EMAIL: raykwan@g.ucla.edu,san2heg@gmail.com
#ID: 304783893,604788993

CC = gcc
CFLAGS = -Wall -Wextra -g -lm
OBJECTS = lab3b
SOURCES = lab3b.c
TARBALL = lab3b-304783893.tar.gz

default: $(OBJECTS)

lab3b: lab3b.c
	$(CC) $(CFLAGS) lab3b.c -o $@

dist:
	tar -czf $(TARBALL) README $(SOURCES) Makefile ext2_fs.h

clean:
	rm -f $(OBJECTS) $(TARBALL)

.PHONY: default dist clean
