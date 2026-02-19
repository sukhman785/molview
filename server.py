from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import io
import urllib
import json
import os
import cgi
import molsql
import MolDisplay

# Publicly accessible files
public_files = ['/index.html', '/script.js', '/style.css']

# Initialize Database
db = molsql.Database(reset=False)
db.create_tables()

ATOMIC_MASS = {
    "H": 1.008, "He": 4.0026, "Li": 6.94, "Be": 9.0122, "B": 10.81, "C": 12.011,
    "N": 14.007, "O": 15.999, "F": 18.998, "Ne": 20.180, "Na": 22.990, "Mg": 24.305,
    "Al": 26.982, "Si": 28.085, "P": 30.974, "S": 32.06, "Cl": 35.45, "Ar": 39.948,
    "K": 39.098, "Ca": 40.078, "Br": 79.904, "I": 126.90
}

def make_formula(atom_counts):
    if not atom_counts:
        return ""

    parts = []
    if "C" in atom_counts:
        count = atom_counts["C"]
        parts.append("C" if count == 1 else f"C{count}")
    if "H" in atom_counts:
        count = atom_counts["H"]
        parts.append("H" if count == 1 else f"H{count}")

    for element in sorted(k for k in atom_counts if k not in ("C", "H")):
        count = atom_counts[element]
        parts.append(element if count == 1 else f"{element}{count}")

    return "".join(parts)

class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'

        if self.path in public_files:
            file_path = self.path[1:]
            if os.path.exists(file_path):
                self.send_response(200)
                if file_path.endswith('.html'):
                    self.send_header('Content-type', 'text/html')
                elif file_path.endswith('.js'):
                    self.send_header('Content-type', 'application/javascript')
                elif file_path.endswith('.css'):
                    self.send_header('Content-type', 'text/css')
                
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_header('Content-length', len(content))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, 'File Not Found')
        
        elif self.path == '/molecules':
            # List all molecules
            molecules = db.cursor.execute("SELECT NAME FROM Molecules").fetchall()
            molecule_list = [row[0] for row in molecules]
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(molecule_list).encode('utf-8'))

        elif self.path == '/elements':
            # List all elements
            elements = db.cursor.execute("SELECT * FROM Elements").fetchall()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(elements).encode('utf-8'))

        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        if self.path == '/add':
            postvars = urllib.parse.parse_qs(body.decode('utf-8'))
            try:
                values = (
                    int(postvars['elementnumber'][0]),
                    postvars['elementcode'][0],
                    postvars['elementname'][0],
                    postvars['color1'][0].lstrip('#'),
                    postvars['color2'][0].lstrip('#'),
                    postvars['color3'][0].lstrip('#'),
                    float(postvars['elementradius'][0])
                )
                db.__setitem__('Elements', values)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))
            except Exception as e:
                self.send_error(400, str(e))

        elif self.path == '/upload':
            try:
                content_type = self.headers.get('Content-Type', '')
                if not content_type.startswith('multipart/form-data'):
                    self.send_error(400, "Expected multipart/form-data")
                    return

                form = cgi.FieldStorage(
                    fp=io.BytesIO(body),
                    headers=self.headers,
                    environ={
                        "REQUEST_METHOD": "POST",
                        "CONTENT_TYPE": content_type,
                    },
                )

                mol_name = form.getfirst('molname', '').strip()
                if not mol_name:
                    self.send_error(400, "Missing molecule name")
                    return

                if 'sdf_file' not in form or not getattr(form['sdf_file'], 'file', None):
                    self.send_error(400, "Missing SDF file")
                    return

                sdf_content = form['sdf_file'].file.read().decode('utf-8', errors='replace')
                db.add_molecule(mol_name, io.StringIO(sdf_content))
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'name': mol_name}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))

        elif self.path == '/display':
            # Get SVG for a molecule with rotation
            postvars = urllib.parse.parse_qs(body.decode('utf-8'))
            mol_name = postvars.get('name', [None])[0]
            phi_x = int(postvars.get('phi_x', [0])[0])
            phi_y = int(postvars.get('phi_y', [0])[0])
            phi_z = int(postvars.get('phi_z', [0])[0])

            if mol_name:
                try:
                    mol = db.load_mol(mol_name)
                except ValueError as e:
                    self.send_error(404, str(e))
                    return

                # Apply rotations in Python and recompute bond geometry.
                mol.rotate(phi_x, phi_y, phi_z)
                
                # Update radii and names for display
                MolDisplay.radius = db.radius()
                MolDisplay.element_name = db.element_name()
                MolDisplay.header = (
                    '<svg version="1.1" width="1000" height="1000" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid meet" '
                    'xmlns="http://www.w3.org/2000/svg"><defs>'
                    + db.radial_gradients()
                    + '</defs>'
                )
                
                svg_content = mol.svg()
                self.send_response(200)
                self.send_header('Content-type', 'image/svg+xml')
                self.end_headers()
                self.wfile.write(svg_content.encode('utf-8'))
            else:
                self.send_error(400, "Molecule name required")

        elif self.path == '/analyze':
            postvars = urllib.parse.parse_qs(body.decode('utf-8'))
            mol_name = postvars.get('name', [None])[0]
            if not mol_name:
                self.send_error(400, "Molecule name required")
                return

            try:
                mol = db.load_mol(mol_name)
            except ValueError as e:
                self.send_error(404, str(e))
                return

            atom_counts = {}
            for i in range(mol.atom_no):
                atom = mol.get_atom(i)
                atom_counts[atom.element] = atom_counts.get(atom.element, 0) + 1

            bond_orders = {}
            for i in range(mol.bond_no):
                bond = mol.get_bond(i)
                key = str(int(bond.epairs))
                bond_orders[key] = bond_orders.get(key, 0) + 1

            molar_mass = 0.0
            unknown = []
            for element, count in atom_counts.items():
                if element in ATOMIC_MASS:
                    molar_mass += ATOMIC_MASS[element] * count
                else:
                    unknown.append(element)

            response = {
                "name": mol_name,
                "formula": make_formula(atom_counts),
                "atom_count": mol.atom_no,
                "bond_count": mol.bond_no,
                "element_counts": atom_counts,
                "bond_order_distribution": bond_orders,
                "molar_mass": round(molar_mass, 3),
                "unknown_mass_elements": sorted(unknown),
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        else:
            self.send_error(404, 'Not Found')

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    httpd = HTTPServer(('localhost', port), Server)
    print(f"Server starting on port {port}...")
    httpd.serve_forever()
