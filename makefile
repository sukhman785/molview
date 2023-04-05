CC = clang
CFLAGS = -Wall -std=c99 -pedantic


_molecule.so: molecule.py molecule_wrap.o libmol.so
	$(CC) -shared -L. -lmol -dynamiclib -L/usr/lib/python3.7/config-3.7m-x86_64-linux-gnu -lpython3.7m molecule_wrap.o -o _molecule.so
molecule_wrap.o: molecule_wrap.c
	$(CC) $(CFLAGS) -c -fpic -I/usr/include/python3.7m molecule_wrap.c -o molecule_wrap.o
libmol.so: mol.o
	$(CC) mol.o -shared -o libmol.so
mol.o: mol.c mol.h 
	$(CC) $(CFLAGS) -c mol.c -fpic -o mol.o
clean:
	rm -f *.o *.so start
