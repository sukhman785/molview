# MolView (CIS2750)

Cleaned project structure for GitHub.

## Project Layout

- `index.html`, `style.css`, `script.js`: frontend UI and interactions
- `server.py`: HTTP API server
- `molsql.py`: SQLite database layer
- `MolDisplay.py`: SVG rendering and molecule transforms
- `mol.c`, `mol.h`, `molecule.i`, `makefile`: C + SWIG build source
- `samples/`: example SDF files for testing
- `local_only/`: local artifacts/archive (ignored by git)

## Run

```bash
make
python3 server.py 8080
```

Open `http://localhost:8080`.

## Notes

- Run `make` after cloning to generate bindings and shared libraries.
- `molecules.db` is local runtime state and is gitignored.
