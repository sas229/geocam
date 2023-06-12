import numpy as np

X = np.linspace(0, 10, 100)
Y = np.sin(X)

f = open("sin.out", "w")
for k in range(len(X)):
    f.write(str(X[k])+"  "+str(Y[k])+"\n")
f.close()