CC = clang
CFLAGS = -Wall -std=c99 -pedantic
PYTHON_INCLUDE = $(shell python3-config --includes)
PYTHON_LIB = $(shell python3-config --ldflags --libs)

_molecule.so: molecule_wrap.o libmol.so
	$(CC) -shared -L. -lmol -dynamiclib -undefined dynamic_lookup molecule_wrap.o -o _molecule.so

molecule_wrap.c molecule.py: molecule.i mol.h
	swig -python molecule.i

molecule_wrap.o: molecule_wrap.c
	$(CC) $(CFLAGS) -c -fpic $(PYTHON_INCLUDE) molecule_wrap.c -o molecule_wrap.o

libmol.so: mol.o
	$(CC) mol.o -shared -o libmol.so

mol.o: mol.c mol.h 
	$(CC) $(CFLAGS) -c mol.c -fpic -o mol.o

clean:
	rm -f *.o *.so molecule_wrap.c molecule.py
