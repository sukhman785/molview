import molecule

# radius = { 'H': 25,'C': 40,'O': 40,'N': 40,};
# element_name = { 'H': 'grey','C': 'black','O': 'red','N': 'blue',};
header = """<svg version="1.1" width="1000" height="1000"
xmlns="http://www.w3.org/2000/svg">""";
footer = """</svg>""";
offsetx = 500;
offsety = 500;

class Atom: 
    def __init__(self,c_atom):
        self.atom = c_atom
        self.z = c_atom.z

    def __str__(self):
        return f"Atom({self.atom.element}, x={self.atom.x}, y={self.atom.y}, z={self.z})"

    def svg(self): 
        #Compute x and y coordinates

        cx = self.atom.x * 100.0 + offsetx
        cy = self.atom.y * 100.0 + offsety

        #Get radius from dictionary
        r = radius.get(self.atom.element, 0)

        #Colour of circle
        colour = element_name.get(self.atom.element)

        #Return svg string
        return f'  <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="url(#{colour})"/>\n'
    
class Bond:
    def __init__(self, c_bond):
        self.bond = c_bond
        self.z = c_bond.z
        
    def __str__(self):
        return f"Bond({self.bond.a1}, {self.bond.a2}, {self.bond.len})"
    
    def svg(self):
        x1 = (self.bond.x1 * 100) + offsetx
        y1 = (self.bond.y1 * 100) + offsety
        x2 = (self.bond.x2 * 100) + offsetx
        y2 = (self.bond.y2 * 100) + offsety
        p1 = (x1 + (self.bond.dy * 10), y1 - (self.bond.dx * 10))
        p2 = (x1 - (self.bond.dy * 10), y1 + (self.bond.dx * 10))
        p3 = (x2 - (self.bond.dy * 10), y2 + (self.bond.dx * 10))
        p4 = (x2 + (self.bond.dy * 10), y2 - (self.bond.dx * 10))
        return '  <polygon points="%.2f,%.2f %.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="green"/>\n' % (p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1])

class Molecule(molecule.molecule):
    def __str__(self):
        atom_strings = [str(atom) for atom in self.atoms]
        bond_strings = [str(bond) for bond in self.bonds]
        return "Molecule(\n" + ",\n".join(atom_strings + bond_strings)+ "\n)"

    def svg(self):

        atoms = []
        bonds = []

        for i in range(self.atom_no):
            atom = Atom(self.get_atom(i))
            atoms.append(atom)
        
        for i in range(self.bond_no):
            bond = Bond(self.get_bond(i))
            bonds.append(bond)
        
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
            self.append_bond(a1, a2, epairs)
        
        return self
        