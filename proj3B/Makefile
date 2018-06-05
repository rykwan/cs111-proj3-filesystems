#NAME: Raymond Kwan,Sanketh Hedge
#EMAIL: raykwan@g.ucla.edu,san2heg@gmail.com
#ID: 304783893,604788993

OBJECTS = lab3b
SOURCES = lab3b.py
TARBALL = lab3b-304783893.tar.gz

default: $(OBJECTS)

lab3b: lab3b.py
	chmod +x lab3b.py
	ln -s lab3b.py lab3b
	chmod +x lab3b

dist:
	tar -czf $(TARBALL) README $(SOURCES) Makefile

clean:
	rm -f $(TARBALL) $(OBJECTS)

.PHONY: default dist clean
