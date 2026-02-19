import molecule
import math

radius = {}
element_name = {}
header = """<svg version="1.1" width="1000" height="1000" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid meet"
xmlns="http://www.w3.org/2000/svg">""";
footer = """</svg>""";
offsetx = 500;
offsety = 500;
render_scale = 100.0
render_offsetx = offsetx
render_offsety = offsety

class Atom: 
    def __init__(self,c_atom, index=-1):
        self.atom = c_atom
        self.index = index
        self.z = c_atom.z

    def __str__(self):
        return f"Atom({self.atom.element}, x={self.atom.x}, y={self.atom.y}, z={self.z})"

    def svg(self): 
        #Compute x and y coordinates

        cx = self.atom.x * render_scale + render_offsetx
        cy = self.atom.y * render_scale + render_offsety

        #Get radius from dictionary
        r = radius.get(self.atom.element, 0)

        #Colour of circle
        colour = element_name.get(self.atom.element)

        #Return svg string
        return (
            f'  <circle class="atom" data-atom-index="{self.index}" '
            f'data-element="{self.atom.element}" cx="{cx:.2f}" cy="{cy:.2f}" '
            f'r="{r}" fill="url(#{colour})"/>\n'
        )
    
class Bond:
    def __init__(self, c_bond, index=-1):
        self.bond = c_bond
        self.index = index
        self.z = c_bond.z
        
    def __str__(self):
        return f"Bond({self.bond.a1}, {self.bond.a2}, {self.bond.len})"
    
    def svg(self):
        x1 = (self.bond.x1 * render_scale) + render_offsetx
        y1 = (self.bond.y1 * render_scale) + render_offsety
        x2 = (self.bond.x2 * render_scale) + render_offsetx
        y2 = (self.bond.y2 * render_scale) + render_offsety
        p1 = (x1 + (self.bond.dy * 10), y1 - (self.bond.dx * 10))
        p2 = (x1 - (self.bond.dy * 10), y1 + (self.bond.dx * 10))
        p3 = (x2 - (self.bond.dy * 10), y2 + (self.bond.dx * 10))
        p4 = (x2 + (self.bond.dy * 10), y2 - (self.bond.dx * 10))
        return (
            '  <polygon class="bond" data-bond-index="%d" data-a1="%d" data-a2="%d" '
            'data-epairs="%d" points="%.2f,%.2f %.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="#16a34a"/>\n'
        ) % (
            self.index,
            self.bond.a1,
            self.bond.a2,
            self.bond.epairs,
            p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1]
        )

class Molecule(molecule.molecule):
    def __init__(self, c_molecule=None):
        super().__init__()
        # Preserve compatibility with older code that expects a wrapped C molecule at .molecule.
        self.molecule = self
        if c_molecule:
            for i in range(c_molecule.atom_no):
                atom = c_molecule.get_atom(i)
                self.append_atom(atom.element, atom.x, atom.y, atom.z)
            for i in range(c_molecule.bond_no):
                bond = c_molecule.get_bond(i)
                self.append_bond(bond.a1, bond.a2, bond.epairs)

    def __str__(self):
        atom_strings = [str(atom) for atom in self.atoms]
        bond_strings = [str(bond) for bond in self.bonds]
        return "Molecule(\n" + ",\n".join(atom_strings + bond_strings)+ "\n)"

    def svg(self):
        global render_scale, render_offsetx, render_offsety

        atoms = []
        bonds = []

        for i in range(self.atom_no):
            atom = Atom(self.get_atom(i), i)
            atoms.append(atom)
        
        for i in range(self.bond_no):
            bond = Bond(self.get_bond(i), i)
            bonds.append(bond)

        if atoms:
            min_x = min(a.atom.x for a in atoms)
            max_x = max(a.atom.x for a in atoms)
            min_y = min(a.atom.y for a in atoms)
            max_y = max(a.atom.y for a in atoms)
            max_r = max(radius.get(a.atom.element, 0) for a in atoms)

            span_x = max(max_x - min_x, 1e-6)
            span_y = max(max_y - min_y, 1e-6)
            usable = 900.0 - (2.0 * max_r)
            scale_x = usable / span_x
            scale_y = usable / span_y
            render_scale = min(max(20.0, min(scale_x, scale_y)), 180.0)

            center_x = (min_x + max_x) / 2.0
            center_y = (min_y + max_y) / 2.0
            render_offsetx = 500.0 - (center_x * render_scale)
            render_offsety = 500.0 - (center_y * render_scale)
        else:
            render_scale = 100.0
            render_offsetx = 500.0
            render_offsety = 500.0
        
        objects = atoms + bonds
        objects.sort(key=lambda obj: obj.z)
        
        svg_strs = [obj.svg() for obj in objects]
        svg_str = ''.join(svg_strs)
        
        return header + svg_str + footer
    
    def parse(self,file_obj):
        
        #Skip first 3 lines 
        for i in range(3):
            next(file_obj)
        
        #Parse number of atoms and bonds 
        line = next(file_obj).split()
        num_atoms, num_bonds = int(line[0]), int (line[1])

        #Parse Atom Information

        for i in range(num_atoms):
            line = next(file_obj).split()
            x, y, z, element = float(line[0]), float(line[1]), float(line[2]), line[3]
            self.append_atom(element, x, y, z)
        
        #Parse Bond Information
        for i in range(num_bonds):
            line = next(file_obj).split()
            a1, a2, epairs = int(line[0]), int(line[1]), int (line[2])
            # SDF files use 1-based atom indices; C code expects 0-based indices.
            self.append_bond(a1 - 1, a2 - 1, epairs)
        
        return self

    def rotate(self, phi_x=0, phi_y=0, phi_z=0):
        if self.atom_no == 0:
            return

        rx = math.radians(phi_x)
        ry = math.radians(phi_y)
        rz = math.radians(phi_z)
        sx, cx = math.sin(rx), math.cos(rx)
        sy, cy = math.sin(ry), math.cos(ry)
        sz, cz = math.sin(rz), math.cos(rz)

        # Rotate around molecule centroid so the model stays in frame.
        cx0 = sum(self.get_atom(i).x for i in range(self.atom_no)) / self.atom_no
        cy0 = sum(self.get_atom(i).y for i in range(self.atom_no)) / self.atom_no
        cz0 = sum(self.get_atom(i).z for i in range(self.atom_no)) / self.atom_no

        for i in range(self.atom_no):
            atom = self.get_atom(i)
            x = atom.x - cx0
            y = atom.y - cy0
            z = atom.z - cz0

            if phi_x:
                y, z = (y * cx) - (z * sx), (y * sx) + (z * cx)
            if phi_y:
                x, z = (x * cy) + (z * sy), (-x * sy) + (z * cy)
            if phi_z:
                x, y = (x * cz) - (y * sz), (x * sz) + (y * cz)

            atom.x = x + cx0
            atom.y = y + cy0
            atom.z = z + cz0

        for i in range(self.bond_no):
            molecule.compute_coords(self.get_bond(i))
        
