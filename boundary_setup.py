import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


#1. first load the mesh generated
try:
    mesh = np.load("huston_final_mesh.npy")
except FileNotFoundError:
    Print("Error: could not find 'huston_final_mesh.npy' file")
    exit()

#2. Copy the mesh. land(0), water (1)
boundary_map = np.copy(mesh)

# 3. to make the inlet and outlet, we scan the outer most column on both the left hand and 
# right hand,and tag active cell( value == 1). we will then make the upstream inlet =2 and 
# downstream inlet = 3

# leftmost boundary (Inlet)
boundary_map[:, 0][boundary_map[:,0] == 1] = 2

#Rightmost boundary (outlet)
boundary_map[:, -1][boundary_map[:,-1] == 1] = 3

#4. Read the array metadata
Ny, Nx = mesh.shape
total_nodes = Nx * Ny
active_fluid = np.sum(mesh == 1)
inlet_count = np.sum(boundary_map == 2)
outlet_count = np.sum(boundary_map == 3)


print("\n-- LBM Computational Domain ---")
print(f"Grid Array Structure (Rows x Columns): {Nx} x {Ny}")
print(f"Total nodes: {total_nodes}")
print(f" Active fluid cels: {active_fluid}")
print(f" Inlet node count: {inlet_count}")
print(f"Outlet node count: {outlet_count}")

color_palette = ListedColormap(['black', '#1f77b4', '#2ca02c', '#d62728'])

plt.figure(figsize=(12,6))
plt.title("LBM Structural Boundary Map\nGreen: Fluid Inlet | Red: Fluid Outlet | Black: No-slip wall")
plt.imshow(boundary_map, cmap=color_palette)
plt.axis('off')
plt.tight_layout()
plt.show()