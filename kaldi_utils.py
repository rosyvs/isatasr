import numpy as np
import sklearn
import matplotlib.pyplot as plt

def loadXV(file, plot=True):
    label=[]
    vec=[]
    with open(file) as f:
        for l in f:
            tok=l.strip().split()
            label.append(tok[0])
            vec.append([float(v) for v in tok[2:-1]])
            data = np.array(vec)

    if plot:
        # visualise XV
        emb=sklearn.manifold.TSNE(n_components=2).fit_transform(data)
        plt.scatter(emb[:,0],emb[:,1])

    return label, data
