CC = clang
CFLAGS = -Wall -std=c99 -pedantic 


_molecule.so: molecule.py molecule_wrap.o libmol.so
	$(CC) -shared -L/Users/sukhi/Desktop/CIS2750/A4 -lmol -dynamiclib -L/Library/Frameworks/Python.framework/Versions/3.10/lib -lpython3.10 molecule_wrap.o -o _molecule.so
molecule_wrap.o: molecule_wrap.c mol.o
	$(CC) $(CFLAGS) -c mol.o -fpic -I/Library/Frameworks/Python.framework/Versions/3.10/include/python3.10 molecule_wrap.c -o molecule_wrap.o
libmol.so: mol.o
	$(CC) mol.o -shared -o libmol.so
mol.o: mol.c mol.h
	$(CC) $(CFLAGS) -c mol.c -fpic -o mol.o

clean:
	rm -f *.o *.so myprog
