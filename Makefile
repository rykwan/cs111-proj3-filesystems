#NAME: Raymond Kwan, Sanketh Hedge
#EMAIL: raykwan@g.ucla.edu, san2heg@gmail.com
#ID: 304783893, 604788993

CC = gcc
CFLAGS = -Wall -Wextra -g
OBJECTS = lab3a
SOURCES = lab3a.c
TARBALL = lab3a-304783893.tar.gz

default: $(OBJECTS)

lab3a: lab3a.c
	$(CC) $(CFLAGS) lab3a.c -o $@

dist:
	tar -czf $(TARBALL) README $(SOURCES) Makefile ext2_fs.h

clean:
	rm -f $(OBJECTS) $(TARBALL)

.PHONY: default dist clean
