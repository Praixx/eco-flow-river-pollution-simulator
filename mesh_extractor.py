import rasterio 
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import label

# define the file path
tif_file = "n29_w096_1arc_v3.tif"

#1. open the file and inspect the metadata
print("Opening satelite data")
with rasterio.open(tif_file) as src:

    # read the first layer of radar elevation data into a numpy matrix
    full_elevation_data = src.read(1).astype(float)

    # clean up any "no data" values from the .tif file
    #elevation = elevation_data.astype(float)
    if src.nodata is not None:
        full_elevation_data[full_elevation_data == src.nodata] = -9999.0

    row_top, col_left = src.index(-95.1100, 29.7750)
    row_bot, col_right = src.index(-95.0600, 29.7400)

    elevation = full_elevation_data[row_top:row_bot, col_left:col_right]

#2. add 2 meters to the lowest elevation point and any point below this will be water(1) and above will be land(0)

    # to find the water baseline
    #water_level = np.nanmin(elevation) + 2
    water_level = 5.0
    print(f"the water threshold is {water_level:.2f} meters")

    # now check if the point is below or above water level and assign 0 or 1 to the matrix
    raw_water_mask = (elevation <= water_level).astype(int)

#3. label the connected ponds of water
    labeled_array, num_features = label(raw_water_mask)
    print(f"number of water bodies found: {num_features}")

    # Find the size of each water body, ignoring the size of land(0)
    sizes = np.bincount(labeled_array.ravel())
    sizes[0] = 0  # ignore the size of land (0)

    #find the larget water body
    main_channel_label = sizes.argmax()

    # create the final fluid mesh for the largest water body
    final_fluid_mesh = (labeled_array == main_channel_label).astype(int)

#4. Save the final mesh
    np.save("huston_final_mesh", final_fluid_mesh)
    print("final mesh successfully saved as huston_final_mesh.npy")

#5. Visualization
    plt.figure(figsize=(14,7))

    plt.subplot(1,2,1)
    plt.title("Raw mask includes all ponds")
    plt.imshow(raw_water_mask, cmap='magma')
    plt.axis('off')

    plt.subplot(1,2,2)
    plt.title("clean computational mesh (main water body only)" )
    plt.imshow(final_fluid_mesh, cmap='Blues')
    plt.axis('off')

    plt.tight_layout()
    plt.show()



