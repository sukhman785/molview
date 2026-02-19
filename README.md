# MolView 

MolView is an interactive molecule visualization web app. It lets users define element styles, upload SDF molecule files, render SVG molecular structures, rotate the model directly by dragging in the viewer, inspect atoms/bonds with hover and click interactions, and view live molecular analytics such as formula, molar mass, atom counts, and bond-order distribution.

## Demo

https://github.com/user-attachments/assets/00c1a9c8-b94b-428a-915f-4c44c808db00


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
