import numpy as np
import matplotlib.pyplot as plt

#1. load the mesh generated
try:
    mesh = np.load("huston_final_mesh.npy")
except FileNotFoundError:
    print("Error: could not find the mesh, run mesh_extractor.py first to generate the mesh")
    exit()

Ny, Nx = mesh.shape
print(f"Mesh loaded successfully with dimensions: {Ny} x {Nx}")

#seal the top and bottom of the mesh to prevent fluid from escaping
mesh[0, :] = 0
mesh[-1, :] = 0

# identify all solid land pixel
obstacle = (mesh == 0)


#2. Stability Parameters
Nt = 3000   #total time steps
omega = 1.2     #controls fluid viscosity, 1.0 < omega < 1.9
u_in_max = 0.05  # inlet injection velocity, must be low to prevent instability

# D2Q9 Lattice Definitions
# the order of movement: Center, East, North, West, South, NE, NW, SW, SE
cxs = np.array([0, 1, 0, -1, 0, 1, -1, -1, 1])
cys = np.array([0, 0, 1, 0, -1, 1, 1, -1, -1])

# collision weight for each direction
weights = np.array([4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36])

# 180 degree bounce back for hitting wall
opposite = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6])



#3. Memory Allocation
# create a 3d array with 9 faces( for each direction) and fills it withthe collision weights
f = np.zeros((9, Ny, Nx))
for i in range(9):
    f[i, :, :] = weights[i]

print(f"Ingniting LBM Physics Engine on {Ny} x {Nx} grid")
print(f"processing 3000 time steps ...")

#4. Main LBM Loop
for step in range(Nt):

    #a. calculate the macroscopic density(rho) and velocity (u, v)
    rho = np.sum(f, axis=0)
    u = np.sum(f * cxs[:, np.newaxis, np.newaxis], axis=0) / rho
    v = np.sum(f * cys[:, np.newaxis, np.newaxis], axis=0) / rho

    #b. Enforce boundary condition
    # inlet. inject fresh water velocity
    u[:, 0] = u_in_max * (mesh[:, 0] == 1)
    v[:, 0] = 0
    rho[:, 0] = 1.0

    # outlet. allow fluid to exit freely by copying values from the adjacent column
    # u[:, -1] = u[:, -2]
    # v[:, -1] = v[:, -2]
    # rho[:, -1] = rho[:, -2]

    # walls. it will be zero velocity
    u[obstacle] = 0
    v[obstacle] = 0

    #c. collision phase
    f_eq = np.zeros((9, Ny, Nx))
    u2 = u**2 + v**2
    for i in range(9):
        cu = cxs[i] * u + cys[i] * v
        #  Lattice Boltzmann equilibrium distribution equation
        f_eq[i, :, :] = rho * weights[i] * (1 + 3*cu + 4.5*cu**2 - 1.5*u2)

        # Apply the BGK collision operator for the fluid cells only (not the obstacles)
        f[i, ~obstacle] = f[i, ~obstacle] - omega * (f[i, ~obstacle] - f_eq[i, ~obstacle])
        

    #d. streaming phase (particles moves to the next cell)
    for i in range(9):
        f[i, :, :] = np.roll(f[i, :, :], cxs[i], axis=1) #moves east-west
        f[i, :, :] = np.roll(f[i, :,:], cys[i], axis=0) #moves north-south
    
    
    #e. solid wall(bounce back)
    # flip particles that hit wall by 180 degree
    bounced_f = f[:, obstacle]
    for i in range(9):
        f[i, obstacle] = bounced_f[opposite[i]]

    # immediatley overwrite the wrap-around garbage
    for i in range(9):
        f[i, :, 0] = f_eq[i, :, 0]    #force fresh water in from the left
        f[i, :, -1] = f[i, :, -2]    # let water escape from the right

    
    if step % 500 == 0:
        print(f"calculated step {step} / {Nt} ")


print("LBM simulation completed successfully! visualizing results ...")


# 5. Visualize the Final State
velocity_magnitude = np.sqrt(u**2 + v**2)
velocity_magnitude[obstacle] = np.nan 

plt.figure(figsize=(14, 7))
plt.title("LBM Hydrodynamic Velocity Field\nHouston Ship Channel (t=3000)", fontsize=14)
plt.imshow(velocity_magnitude, cmap='turbo')
plt.colorbar(label='Flow Velocity Magnitude')
plt.axis('off')
plt.tight_layout()
plt.show()

#6. Export to VTK for ParaView
def export_vtk(filename, u, v, obstacle):
    Ny, Nx = u.shape

    with open(filename, 'w') as f:
        # VTK Header
        f.write("# vtk DataFile Version 3.0\n")
        f.write("LBM Velocity Field\n")
        f.write("ASCII\n")
        f.write("DATASET STRUCTURED_POINTS\n")

        # vtk operates in 3d so we will set z to 1
        f.write(f"DIMENSIONS {Nx} {Ny} 1\n")
        f.write("ORIGIN 0 0 0\n")
        f.write("SPACING 1 1 1\n")  
        f.write(f"POINT_DATA {Nx*Ny}\n")

        # velocity vector field (u, v, w)
        f.write("VECTORS velocity float\n")

        # VTK reads data with X moving fastest, then Y. 
        for y in range(Ny):
            for x in range(Nx):
                if obstacle[y, x]:
                    # Land has zero velocity
                    f.write("0.0 0.0 0.0\n")
                else:
                    # Water has u and v. Z-velocity is 0.0
                    f.write(f"{u[y, x]:.6f} {v[y, x]:.6f} 0.0\n")
                    
        # Write the Land Mask (so we can extrude the dirt in 3D later)
        f.write("SCALARS geometry float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for y in range(Ny):
            for x in range(Nx):
                # Tag Land as 1.0 and Water as 0.0
                val = 1.0 if obstacle[y, x] else 0.0
                f.write(f"{val}\n")

print("Exporting mathematical grid to ParaView VTK format...")
export_vtk("huston_flow_results.vtk", u, v, obstacle)
print("Success! 'huston_flow_results.vtk' is securely saved to your drive.")