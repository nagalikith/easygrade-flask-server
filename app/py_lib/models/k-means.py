from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt

# Example data (replace with your actual dataset)
X = np.random.rand(100, 2)  # 100 data points with 2 features

# Initialize KMeans
kmeans = KMeans(n_clusters=3, max_iter=100, tol=1e-4, random_state=42)

# Fit the model
kmeans.fit(X)

# Get the cluster centers and labels
centers = kmeans.cluster_centers_
labels = kmeans.labels_

# Plot the results
plt.scatter(X[:, 0], X[:, 1], c=labels, cmap='viridis')
plt.scatter(centers[:, 0], centers[:, 1], marker='X', color='red', s=200)
plt.title("KMeans Clustering")
plt.show()