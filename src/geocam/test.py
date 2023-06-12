import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

fig = plt.figure()

ax = fig.add_subplot(111, projection='3d')

# x_poly = np.zeros((3,3))

length_arrows_mm = 40 
color = 'skyblue'
alpha = 0.4
elem_length_1 = .1*length_arrows_mm
elem_length_2 = .6*length_arrows_mm

origin = np.array([1,3,4])
x_plan_normal_to_x = [origin[0], origin[0], origin[0], origin[0]]
y_plan_normal_to_x = [origin[1] + elem_length_1, origin[1] + elem_length_2, origin[1] + elem_length_2, origin[1] + elem_length_1]
z_plan_normal_to_x = [origin[2] + elem_length_1, origin[2] + elem_length_1, origin[2] + elem_length_2, origin[2] + elem_length_2]

x_plan_normal_to_y = [elem_length_1, elem_length_2, elem_length_2, elem_length_1]
y_plan_normal_to_y = [origin[1], origin[1], origin[1], origin[1]]
z_plan_normal_to_y = [origin[2] + elem_length_1, origin[2] + elem_length_1, origin[2] + elem_length_2, origin[2] + elem_length_2]

x_plan_normal_to_z = [elem_length_1, elem_length_2, elem_length_2, elem_length_1]
y_plan_normal_to_z = [origin[1] + elem_length_1, origin[1] + elem_length_1, origin[1] + elem_length_2, origin[1] + elem_length_2]
z_plan_normal_to_z = [origin[2], origin[2], origin[2], origin[2]]

vertice_1 = [list(zip(x_plan_normal_to_x, y_plan_normal_to_x, z_plan_normal_to_x))]
vertice_2 = [list(zip(x_plan_normal_to_y, y_plan_normal_to_y, z_plan_normal_to_y))]
vertice_3 = [list(zip(x_plan_normal_to_z, y_plan_normal_to_z, z_plan_normal_to_z))]

poly_1 = Poly3DCollection(vertice_1, alpha=alpha, facecolors=color)
poly_2 = Poly3DCollection(vertice_2, alpha=alpha, facecolors=color)
poly_3 = Poly3DCollection(vertice_3, alpha=alpha, facecolors=color)

ax.add_collection3d(poly_1)
ax.add_collection3d(poly_2)
ax.add_collection3d(poly_3)

ax.set_xlim(-40,40)
ax.set_ylim(-40,40)
ax.set_zlim(-40,40)

# plt.axes('equal')
plt.show()