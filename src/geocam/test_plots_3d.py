import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# https://matplotlib.org/stable/gallery/mplot3d/quiver3d.html#sphx-glr-gallery-mplot3d-quiver3d-py

roa_vek = np.array([0, 0, 12])
rob_vek = np.array([4, 12, 0])
rab_vek = rob_vek - roa_vek
f = 2000
fab_vek = f * rab_vek / np.linalg.norm(rab_vek)
mo = np.cross(roa_vek, fab_vek)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

ax.set_xlim([-1, 1])
ax.set_ylim([-1, 1])
ax.set_zlim([-1, 1])

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")

origo = np.array([0, 0, 0])
ax.view_init(30, 45)

ax.quiver(origo[0], origo[1], origo[2], 2, 0, 0, color="r", normalize=True)
ax.quiver(origo[0], origo[1], origo[2], 0, 2, 0, color="g", normalize=True)
ax.quiver(origo[0], origo[1], origo[2], 0, 0, 2, color="b", normalize=True)

ax.text(0.1, 0.0, -0.2, r'$0$')
ax.text(1.3, 0, 0, r'$x$')
ax.text(0, 1.3, 0, r'$y$')
ax.text(0, 0, 1.3, r'$z$')

ax.quiver(origo[0], origo[1], origo[2], mo[0], mo[1], mo[2], color="c", normalize=True)
ax.text(mo[0], mo[1], mo[2], '%s' % (str("mo")), size=10, zorder=1, color='k')

plt.show()
