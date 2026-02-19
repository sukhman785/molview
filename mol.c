#include "mol.h"


void atomset( atom *atom, char element[3], double *x, double *y, double *z ) {

    //Copying element name to atom structure
    memcpy(atom->element, element, sizeof(char[3]));

    //Setting xyz coordinates of atom values
    atom->x = *x; 
    atom->y = *y;
    atom->z = *z;
}
void atomget( atom *atom, char element[3], double *x, double *y, double *z ) { 
    
    //Copying element name from atom structure
    memcpy(element, atom->element, sizeof(char[3]));

    //Setting xyz coordinates from the atom 
    *x = atom->x;
    *y = atom->y;
    *z = atom->z;
}
void bondset(bond* bond, unsigned short* a1, unsigned short* a2, atom** atoms, unsigned char* epairs) {
    bond->a1 = *a1;
    bond->a2 = *a2;
    bond->atoms = *atoms;
    bond->epairs = *epairs;
    
    compute_coords(bond);
}
void bondget( bond *bond, unsigned short *a1, unsigned short *a2, atom **atoms, unsigned char *epairs ) {
    *a1 = bond->a1;
    *a2 = bond->a2;
    *atoms = bond->atoms;
    *epairs = bond->epairs;
}
molecule *molmalloc( unsigned short atom_max, unsigned short bond_max ) { 
   
    molecule *ptr;

    //Allocating memory for the molecule structure
    ptr = malloc(sizeof(molecule));
    if (ptr == NULL) { 
        return NULL;
    }

    //Set max number of atoms in the molecule
    ptr->atom_max = atom_max;

    ptr->atom_no = 0;

    //Allocating memory for atom structures
    ptr->atoms = malloc(sizeof(atom)*atom_max);
    if (ptr->atoms == NULL) { 
        free(ptr->atoms);
        free(ptr);
        return NULL;
    }

    //Allocating memory for array of atom pointers
    ptr->atom_ptrs = malloc(sizeof(atom*)*atom_max);
    if (ptr->atom_ptrs == NULL) {
        free(ptr->atoms);
        free(ptr);
        return NULL;
    }

    //Set max number of bonds in the molecule
    ptr->bond_max = bond_max;

    ptr->bond_no = 0;

    //Allocating memory for bond structures
    ptr->bonds = malloc(sizeof(bond)*bond_max);
    if (ptr->bonds == NULL) { 
        free(ptr->atom_ptrs);
        free(ptr->atoms);
        free(ptr);
        return NULL;
    }

    //Allocating memory for array of bond pointers
    ptr->bond_ptrs = malloc(sizeof(bond*)*bond_max);
    if(ptr->bond_ptrs == NULL) {
        free(ptr->bonds);
        free(ptr->atom_ptrs);
        free(ptr->atoms);
        free(ptr);
        return NULL;
    }   

    return ptr;
}
molecule *molcopy( molecule *src ) { 
    
    molecule *ptr;

    //Allocating memory for new molecule
    ptr = molmalloc(src->atom_max, src->bond_max);

    //Return if memory allocation fails
    if (ptr == NULL) { 
        return NULL;
    }

    //Copying atoms and bonds in the src to new molecule
    for (int i = 0; i < src->atom_no;i++) {
        molappend_atom(ptr, &src->atoms[i]);
    }
    for (int i = 0; i < src->bond_no; i++) {
        molappend_bond(ptr, &src->bonds[i]);
    }
    //Return pointer to new molecule
    return ptr;
}
void molfree( molecule *ptr ) { 

    //Freeing memory of molecule struct
    free(ptr->bond_ptrs);
    free(ptr->atom_ptrs);
    free(ptr->bonds);
    free(ptr->atoms);
    free(ptr);
}
void molappend_atom( molecule *molecule, atom *atom ) {
    //Check if the number of atoms in molecule has reached max 
    if (molecule->atom_no == molecule->atom_max) {
        molecule->atom_max *= 2;
        if (molecule->atom_max == 0) { 
            molecule->atom_max = 1;
        }

        // Store old atoms pointer to check if it changes
        struct atom *old_atoms = molecule->atoms;

        //Reallocate memory for array of atoms
        void *temp_ptr = realloc(molecule->atoms, molecule->atom_max * sizeof(struct atom)); 
        //Check if realloc failed
        if (temp_ptr == NULL) {
            fprintf(stderr, "Memory Allocation failed, exiting program.\n");
            exit(EXIT_FAILURE);
        }
        //Assign pointer to the atoms array
        molecule->atoms = temp_ptr;

        // If the address of atoms changed, update all bond pointers
        if (molecule->atoms != old_atoms) {
            for (int i = 0; i < molecule->bond_no; i++) {
                molecule->bonds[i].atoms = molecule->atoms;
            }
        }

        //Reallocate memory for array of pointers to the atoms
        temp_ptr = realloc(molecule->atom_ptrs, molecule->atom_max * sizeof(struct atom*));
        //Check if realloc failed
        if (temp_ptr == NULL) {
            fprintf(stderr, "Memory Allocation failed, exiting program.\n");
            exit(EXIT_FAILURE);
        }
        //Assign pointer to the atom_ptrs array
        molecule->atom_ptrs = temp_ptr;
    }
    //Adding atom to array of atoms in molecule
    molecule->atoms[molecule->atom_no] = *atom;

    //Updating array of pointers to add new atom
    for (int i = 0; i < molecule->atom_no + 1;i++) { 
        molecule->atom_ptrs[i] = &molecule->atoms[i];
    }
    //Increment number of atoms 
    molecule->atom_no++;
}
void molappend_bond( molecule *molecule, bond *bond ) {
    //Check if the number of bonds in molecule has reached max 
    if (molecule->bond_no == molecule->bond_max) { 
        molecule->bond_max *= 2;
        if (molecule->bond_max == 0) {
        
            molecule->bond_max = 1;
        }
        //Reallocate memory for array of bonds
        void *temp_ptr = realloc(molecule->bonds, molecule->bond_max * sizeof(struct bond));
        //Check if realloc failed
        if (temp_ptr == NULL) { 
            fprintf(stderr, "Memory Allocation failed, exiting program.\n");
            exit(EXIT_FAILURE);            
        }
        //Assign pointer to the bonds array
        molecule->bonds = temp_ptr;

        //Reallocate memory for array of pointers to the bonds
        temp_ptr = realloc(molecule->bond_ptrs, molecule->bond_max * sizeof(struct bond*));
        //Check if realloc failed
        if (temp_ptr == NULL) {
            fprintf(stderr, "Memory Allocation failed, exiting program.\n");
            exit(EXIT_FAILURE);             
        }
        //Assign pointer to the bond_ptrs array
        molecule->bond_ptrs = temp_ptr;
    }
    //Adding bond to array of bonds in molecule
    molecule->bonds[molecule->bond_no] = *bond;

    //Updating array of pointers to add new bond
    for (int i = 0; i < molecule->bond_no + 1; i++) {
        molecule->bond_ptrs[i] = &molecule->bonds[i];
    }

    //Increment number of bonds 
    molecule->bond_no++;
}
int compare_atoms(const void *a, const void *b) {
    //Cast pointers to atoms
    atom* atom1 = *(atom**)a;
    atom* atom2 = *(atom**)b;

    //Compare Z values of the two atoms
    if (atom1->z > atom2->z) { 
        return 1;
    }
    else if (atom1->z < atom2->z) { 
        return -1;
    }
    else {
        return 0;
    }
}
int bond_comp(const void* a, const void* b) {
    // Cast pointers to bonds
    bond* bond1 = (bond*)a;
    bond* bond2 = (bond*)b;

    // Compare z values of bonds
    if (bond1->z > bond2->z) {
        return 1;
    }
    else if (bond2->z > bond1->z) {
        return -1;
    }
    else {
        return 0;
    }
}
void molsort( molecule *molecule ) { 
    //Sort atoms and bonds based on return vals from compar functions
    qsort(molecule->atom_ptrs, molecule->atom_no, sizeof(struct atom*), compare_atoms);
    qsort(molecule->bond_ptrs, molecule->bond_no, sizeof(struct bond*), bond_comp);
}
void xrotation( xform_matrix xform_matrix, unsigned short deg ) { 
    //Convert degrees to rad
    double rad = deg * (M_PI / 180);

    //Rotation along x-axis
    double rotation_matrix[3][3] = {
        {1, 0, 0},
        {0, cos(rad), -sin(rad)},
        {0, sin(rad), cos(rad)}
    };
    //Assign rotation matrix to the xform matrix
    for (int i = 0; i < 3; i++) { 
        for (int j = 0; j < 3; j++) {
            xform_matrix[i][j] = rotation_matrix[i][j];
        }
    }
}
void yrotation( xform_matrix xform_matrix, unsigned short deg ) {
    //Convert degrees to rad
    double rad = deg * (M_PI / 180);  

    //Rotation along y-axis
    double rotation_matrix[3][3] = {
        {cos(rad), 0, sin(rad)},
        {0, 1, 0},
        {-sin(rad), 0, cos(rad)}
    };
    //Assign rotation matrix to the xform matrix
    for (int i = 0; i < 3; i++) { 
        for (int j = 0; j < 3; j++) {
            xform_matrix[i][j] = rotation_matrix[i][j];
        }
    }    
}
void zrotation( xform_matrix xform_matrix, unsigned short deg ) {
    //Convert degrees to rad 
    double rad = deg * (M_PI / 180);  

    //Rotation along z-axis
    double rotation_matrix[3][3] = {
        {cos(rad), -sin(rad), 0},
        {sin(rad), cos(rad), 0},
        {0, 0, 1}
    };
    //Assign rotation matrix to the xform matrix
    for (int i = 0; i < 3; i++) { 
        for (int j = 0; j < 3; j++) {
            xform_matrix[i][j] = rotation_matrix[i][j];
        }
    }
}
void mol_xform(molecule *molecule, xform_matrix matrix) {
    double result[3];

    // Loop through each bond and apply compute_coords
    for (int i = 0; i < molecule->bond_no; i++) {
        compute_coords(&molecule->bonds[i]);
    }

    // Loop through each atom and apply the transformation matrix
    for (int i = 0; i < molecule->atom_no; i++) {
        result[0] = matrix[0][0] * molecule->atoms[i].x + matrix[0][1] * molecule->atoms[i].y + matrix[0][2] * molecule->atoms[i].z;
        result[1] = matrix[1][0] * molecule->atoms[i].x + matrix[1][1] * molecule->atoms[i].y + matrix[1][2] * molecule->atoms[i].z;
        result[2] = matrix[2][0] * molecule->atoms[i].x + matrix[2][1] * molecule->atoms[i].y + matrix[2][2] * molecule->atoms[i].z;

        // Sets final transformations in the atoms xyz coordinates
        molecule->atoms[i].x = result[0];
        molecule->atoms[i].y = result[1];
        molecule->atoms[i].z = result[2];
    }
}


void compute_coords( bond *bond ) {

    // Compute the average z value
    bond->z = (bond->atoms[bond->a1].z + bond->atoms[bond->a2].z) / 2.0;

    // Compute the x and y coordinates of the atoms
    bond->x1 = bond->atoms[bond->a1].x;
    bond->y1 = bond->atoms[bond->a1].y;
    bond->x2 = bond->atoms[bond->a2].x;
    bond->y2 = bond->atoms[bond->a2].y;


    // Compute the length of the bond
    bond->len = sqrt(pow(bond->x2-bond->x1,2) + pow(bond->y2 - bond->y1,2));
    bond->dx = (bond->x2 - bond->x1)/bond->len;
    bond->dy = (bond->y2 - bond->y1)/bond->len;

}
