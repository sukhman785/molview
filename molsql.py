import sqlite3;
import os;
import molecule
import MolDisplay
from MolDisplay import Atom,Bond,Molecule


class Database: 
    
    def __init__(self, reset=False):
        if reset == True and os.path.exists('molecules.db'): 
            os.remove('molecules.db')

        self.conn = sqlite3.connect('molecules.db')
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Elements (
                    ELEMENT_ID INTEGER NOT NULL,
                    ELEMENT_CODE VARCHAR(3) PRIMARY KEY NOT NULL,
                    ELEMENT_NAME VARCHAR(32) NOT NULL,
                    COLOUR1 CHAR(6) NOT NULL,
                    COLOUR2 CHAR(6) NOT NULL,
                    COLOUR3 CHAR(6) NOT NULL,
                    RADIUS DECIMAL(3) NOT NULL
                )
            """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Atoms (
            ATOM_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            ELEMENT_CODE VARCHAR(3) NOT NULL,
            X DECIMAL(7,4) NOT NULL,
            Y DECIMAL(7,4) NOT NULL,
            Z DECIMAL(7,4) NOT NULL,
            FOREIGN KEY(ELEMENT_CODE) REFERENCES Elements(ELEMENT_CODE)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Bonds ( 
            BOND_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            A1 INTEGER NOT NULL,
            A2 INTEGER NOT NULL,
            EPAIRS INTEGER NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Molecules (
            MOLECULE_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            NAME TEXT UNIQUE NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS MoleculeAtom (
            MOLECULE_ID INTEGER NOT NULL,
            ATOM_ID INTEGER NOT NULL,
            PRIMARY KEY (MOLECULE_ID, ATOM_ID),
            FOREIGN KEY(MOLECULE_ID) REFERENCES Molecules(MOLECULE_ID),
            FOREIGN KEY (ATOM_ID) REFERENCES Atoms(ATOM_ID)
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS MoleculeBond (
            MOLECULE_ID INTEGER NOT NULL,
            BOND_ID INTEGER NOT NULL,
            PRIMARY KEY (MOLECULE_ID, BOND_ID),
            FOREIGN KEY(MOLECULE_ID) REFERENCES Molecules(MOLECULE_ID),
            FOREIGN KEY(BOND_ID) REFERENCES Bonds(BOND_ID)
            )
        """)
        self.conn.commit()

    def __setitem__ (self, table, values ):
        insert_placeholders =",".join(["?"] * len(values))
        sql = f"INSERT OR REPLACE INTO {table} VALUES ({insert_placeholders})"
        self.cursor.execute(sql, values)
        self.conn.commit()

    def add_atom( self, molname, atom ):
        # Insert the atom into the Atoms table
        values = (atom.atom.element, atom.atom.x, atom.atom.y, atom.atom.z)
        self.cursor.execute("INSERT INTO Atoms (ELEMENT_CODE, X, Y, Z) VALUES (?, ?, ?, ?)", values)
        atom_id = self.cursor.lastrowid

        # Get the molecule id for the given molecule name
        self.cursor.execute("SELECT MOLECULE_ID FROM Molecules WHERE NAME=?", (molname,))
        molecule_id = self.cursor.fetchone()[0]

        # Insert the relationship into the MoleculeAtom table
        values = (molecule_id, atom_id)
        self.cursor.execute("INSERT INTO MoleculeAtom (MOLECULE_ID, ATOM_ID) VALUES (?, ?)", values)
    
    def add_bond(self, molname, bond):
        # Insert bond attributes into the Bonds table
        self.cursor.execute(
            "INSERT INTO Bonds (A1, A2, EPAIRS) VALUES (?, ?, ?)",
            (bond.bond.a1, bond.bond.a2, bond.bond.epairs)
        )
        bond_id = self.cursor.lastrowid

        self.cursor.execute("SELECT MOLECULE_ID FROM Molecules WHERE NAME=?", (molname,))
        molecule_id = self.cursor.fetchone()[0]

        # Insert a row into the MoleculeBond table linking the named molecule to the bond in the Bonds table
        self.cursor.execute(
            "INSERT INTO MoleculeBond (MOLECULE_ID, BOND_ID) VALUES (?, ?)",
            (molecule_id, bond_id)
        )
    
    def _delete_molecule_if_exists(self, name):
        self.cursor.execute("SELECT MOLECULE_ID FROM Molecules WHERE NAME = ?", (name,))
        row = self.cursor.fetchone()
        if not row:
            return

        molecule_id = row[0]
        atom_ids = [x[0] for x in self.cursor.execute(
            "SELECT ATOM_ID FROM MoleculeAtom WHERE MOLECULE_ID = ?", (molecule_id,)
        ).fetchall()]
        bond_ids = [x[0] for x in self.cursor.execute(
            "SELECT BOND_ID FROM MoleculeBond WHERE MOLECULE_ID = ?", (molecule_id,)
        ).fetchall()]

        self.cursor.execute("DELETE FROM MoleculeAtom WHERE MOLECULE_ID = ?", (molecule_id,))
        self.cursor.execute("DELETE FROM MoleculeBond WHERE MOLECULE_ID = ?", (molecule_id,))

        if atom_ids:
            placeholders = ",".join(["?"] * len(atom_ids))
            self.cursor.execute(f"DELETE FROM Atoms WHERE ATOM_ID IN ({placeholders})", atom_ids)
        if bond_ids:
            placeholders = ",".join(["?"] * len(bond_ids))
            self.cursor.execute(f"DELETE FROM Bonds WHERE BOND_ID IN ({placeholders})", bond_ids)

        self.cursor.execute("DELETE FROM Molecules WHERE MOLECULE_ID = ?", (molecule_id,))

    def add_molecule(self, name, fp):
        mol = Molecule()
        mol.parse(fp)
        if mol.atom_no == 0:
            raise ValueError("SDF did not contain any atoms")

        try:
            self.cursor.execute("BEGIN")
            self._delete_molecule_if_exists(name)
            self.cursor.execute("INSERT INTO Molecules (NAME) VALUES (?)", (name,))

            for i in range(mol.atom_no):
                self.add_atom(name, Atom(mol.get_atom(i)))
            for i in range(mol.bond_no):
                self.add_bond(name, Bond(mol.get_bond(i)))

            self.conn.commit()
        except:
            self.conn.rollback()
            raise

    def load_mol (self, name ):

        atom_results = self.cursor.execute("""
            SELECT * 
            FROM Molecules
            JOIN MoleculeAtom ON Molecules.MOLECULE_ID = MoleculeAtom.MOLECULE_ID
            JOIN Atoms ON MoleculeAtom.ATOM_ID = Atoms.ATOM_ID
            JOIN Elements ON Atoms.ELEMENT_CODE = Elements.ELEMENT_CODE
            WHERE Molecules.NAME =?
            ORDER BY Atoms.ATOM_ID ASC
        """, (name,)).fetchall()


        bond_results = self.cursor.execute("""
            SELECT * 
            FROM Molecules 
            JOIN MoleculeBond ON Molecules.MOLECULE_ID = MoleculeBond.MOLECULE_ID
            JOIN Bonds ON MoleculeBond.BOND_ID = Bonds.BOND_ID
            WHERE Molecules.NAME = ? 
            ORDER BY Bonds.BOND_ID ASC
        """,(name,)).fetchall()

        if not atom_results:
            raise ValueError(f"Molecule '{name}' not found")

        mol = Molecule()
        for i in range (len(atom_results)):
            #Appending Atom
            mol.append_atom(atom_results[i][5], atom_results[i][6], atom_results[i][7], atom_results[i][8])
        
        raw_bonds = [(row[5], row[6], row[7]) for row in bond_results]
        if raw_bonds:
            max_idx = max(max(a1, a2) for a1, a2, _ in raw_bonds)
            min_idx = min(min(a1, a2) for a1, a2, _ in raw_bonds)

            # Legacy DB rows may store 1-based indices. If so, convert all bonds.
            use_one_based = (max_idx == mol.atom_no and min_idx >= 1)

            for a1, a2, epairs in raw_bonds:
                if use_one_based:
                    a1 -= 1
                    a2 -= 1

                if not (0 <= a1 < mol.atom_no and 0 <= a2 < mol.atom_no):
                    raise ValueError(f"Invalid bond indices in molecule '{name}': {a1}, {a2}")

                mol.append_bond(a1, a2, epairs)
        
        return mol
        
    def radius(self):
        sql = "SELECT * FROM Elements"

        self.cursor.execute(sql)
        rows = self.cursor.fetchall()

        #Mapping to row indices with values needed
        radius_dict = {row[1]: row[6] for row in rows}

        return radius_dict
    
    def element_name(self):
        query = "SELECT ELEMENT_CODE, ELEMENT_NAME FROM Elements"

        self.cursor.execute(query)

        rows = self.cursor.fetchall()

        #Mapping to row indices with values needed
        element_dict = {row[0]: row[1] for row in rows}

        return element_dict

    def radial_gradients(self):
        #Retrieve data from the Elements table
        sql =  "SELECT ELEMENT_NAME, COLOUR1, COLOUR2, COLOUR3 FROM Elements"

        self.cursor.execute(sql)
        
        rows = self.cursor.fetchall()

        gradients= ""
        for row in rows:
            element_name,colour1,colour2,colour3 = row

            gradient_svg = """
            <radialGradient id="%s" cx="-50%%" cy="-50%%" r="220%%" fx="20%%" fy="20%%">
            <stop offset="0%%" stop-color="#%s"/>
            <stop offset="50%%" stop-color="#%s"/>
            <stop offset="100%%" stop-color="#%s"/>
            </radialGradient>""" % (element_name, colour1, colour2, colour3)
            gradients += gradient_svg

        return gradients
        




    
