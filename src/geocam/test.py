import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import glob


def find_the_real_world_coor_of_the_corners(squareLength=0.005, cylinderRadius=0.07/2, boardColumns=44, boardRows=28, flag = True):
    deltaTheta = squareLength/cylinderRadius
    real_coord = {}
    horizontalNumberOfcorners = boardColumns-1
    verticalNumberOfcorners = boardRows-1
    cornerId = 0

    #for plots 
    x_coordinates = []
    y_coordinates = []
    z_coordinates = []

    for i in range(verticalNumberOfcorners):
        for j in range(horizontalNumberOfcorners):
            
            cornerId = horizontalNumberOfcorners*i + j
            theta = j*deltaTheta
            x_coordinate = cylinderRadius*np.cos(theta) 
            y_coordinate = cylinderRadius*np.sin(theta)
            z_coordinate = cylinderRadius*4 - (i*squareLength + squareLength)

            # update dict 
            real_coord[cornerId] = np.array([x_coordinate, y_coordinate, z_coordinate], np.float32)

            # update lists for plotting 
            x_coordinates.append(x_coordinate)
            y_coordinates.append(y_coordinate)
            z_coordinates.append(z_coordinate)

    if flag: 
        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')
        ax.scatter(x_coordinates, y_coordinates, z_coordinates, marker=".")
        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        ax.set_zlabel('Z Label')
        plt.axis('equal')
        plt.show()

    return real_coord


if __name__ == "__main__": 
    find_the_real_world_coor_of_the_corners(squareLength=0.005, markerLength=0.003, cylinderRadius=0.07/2, boardColumns=44, boardRows=28)