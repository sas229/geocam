import numpy as np
import matplotlib.pyplot as plt 

def get_cloud_of_3d_points(charuco_num_of_columns:int = 44, 
                           charuco_num_of_rows:int = 28,
                           sample_height_mm:float = 140,
                           sample_diameter_mm:float = 70,
                           flag1:bool = False, 
                           flag2:bool = False) -> dict:
    """
    Generate a cloud of 3D points based on the given parameters.

    Parameters
    ----------
    charuco_num_of_columns : int, optional
        Number of columns in the charuco board, by default 44.
    charuco_num_of_rows : int, optional
        Number of rows in the charuco board, by default 28.
    sample_height_mm : float, optional
        Height of the sample in millimeters, by default 140.
    sample_diameter_mm : float, optional
        Diameter of the sample in millimeters, by default 70.
    flag1 : bool, optional
        Whether to plot the generated points or not, by default False.
    flag2 : bool, optional
        Whether to plot the corners ids or not, by default False.

    Returns
    -------
    dict
        Dictionary containing the 3D coordinates of each corner.
    """

    horz_num_of_squares = charuco_num_of_columns - 1
    sample_radius_mm = 0.5 * sample_diameter_mm
    charuco_square_length_mm = round((np.pi*sample_diameter_mm)/charuco_num_of_columns)
    elementary_angle_rad = charuco_square_length_mm / sample_radius_mm


    num_of_corners = (charuco_num_of_rows - 1) * (charuco_num_of_columns - 1)
    x_coordinates = np.zeros(num_of_corners)
    y_coordinates = np.zeros(num_of_corners)
    z_coordinates = np.zeros(num_of_corners)

    for ver_corner_index in range(charuco_num_of_rows - 1):
        for horz_corner_index in range(charuco_num_of_columns - 1):
            corner_id = horz_corner_index + ver_corner_index * horz_num_of_squares
            theta = horz_corner_index * elementary_angle_rad
            x_coordinates[corner_id] = sample_radius_mm * np.cos(theta) 
            y_coordinates[corner_id] = sample_radius_mm * np.sin(theta)
            # z_coordinates[corner_id] = sample_height_mm - (ver_corner_index * charuco_square_length_mm + charuco_square_length_mm)
            z_coordinates[corner_id] = (ver_corner_index * charuco_square_length_mm + charuco_square_length_mm)

    coords_3d_points = {
        corner_id: np.array([x, y, z], np.float32)
        for corner_id, x, y, z in zip(range(num_of_corners), x_coordinates, y_coordinates, z_coordinates)
    }

    if flag1:
        # plot the points
        plot_3d_points(coords_3d_points, flag=flag2)
    
    return coords_3d_points

def plot_3d_points(coords_3d_points: dict, flag: bool = False):
    """
    Plot the 3D points in a scatter plot.

    Parameters
    ----------
    coords_3d_points : dict
        Dictionary containing the 3D coordinates of each corner.
    flag : bool, optional
        Whether to plot the corners ids or not, by default False.
    
    Returns
    -------
    None
        The function plots the 3D points.

    """
    x_coordinates = np.array([])
    y_coordinates = np.array([])
    z_coordinates = np.array([])
    corner_ids = np.array([])

    for corner_id, coords in coords_3d_points.items():
        corner_ids = np.append(corner_ids, corner_id)
        x_coordinates = np.append(x_coordinates, coords[0])
        y_coordinates = np.append(y_coordinates, coords[1])
        z_coordinates = np.append(z_coordinates, coords[2])

    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.scatter(x_coordinates, y_coordinates, z_coordinates, marker=".")

    if flag:
        # show the ids of the corners
        for i, corner_id in enumerate(corner_ids):
            ax.text(x_coordinates[i], y_coordinates[i], z_coordinates[i], str(int(corner_id)), fontsize=4)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Cloud of 3D points')
    plt.axis('equal')
    plt.show()

if __name__ == "__main__":
    get_cloud_of_3d_points(flag1=True, flag2=True)