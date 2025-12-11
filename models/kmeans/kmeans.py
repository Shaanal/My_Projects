import numpy as np

class KMeans_me:
	def __init__(self, X, k, n=200):
		self.X = X
		self.k = k
		self.max_itr = n
		self.centroids = None
		self.fit()

	def fit(self, p = None):
		np.random.seed(42)
		rand_i = np.random.choice(len(self.X), self.k, replace=False)
		self.centroids = self.X[rand_i]

		for n in range(self.max_itr):
			clusters = self._assignclusters()
			old_centroids = self.centroids.copy()
			self.centroids = np.array([self.X[clusters == i].mean(axis=0) for i in range(self.k)])
			
			if p is not None:
				print('Itr-', n, )
			if np.linalg.norm(self.centroids - old_centroids) == 0:
				break

	def predict(self):
		return self._assignclusters()

	def _assignclusters(self):
		distances = np.linalg.norm(self.X[:, np.newaxis] - self.centroids, axis=2)
		return np.argmin(distances, axis=1)

	def getCost(self):
		clusters = self.predict()
		wcss = sum(np.sum((self.X[clusters == i] - self.centroids[i])**2) for i in range(self.k))
		return wcss

