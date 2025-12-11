import numpy as np
from collections import Counter

class KNN:
	def __init__(self, k, dm):
		self.k = k
		self.dist_met = dm
	
	def getset_k(self, gs, k = None):
		if gs==0:
			self.k = k
		else:
			return self.k  
		
	def getset_dm(self, gs, dm = None):
		if gs==0:
			self.dist_met = dm
		else:
			return self.dist_met
		
	def _manhattan(self, p, q):
		d = np.sum(np.abs(p - q), axis = 1)
		return d
	
	def _euclidean(self, p, q):
		d = np.linalg.norm((p - q), axis=1)
		return d
	
	def _cosine(self, p, q):
		mag_p = np.linalg.norm(p, axis=1)
		mag_q = np.linalg.norm(q, axis=1)
		cs = np.dot(p, q)/(mag_p*mag_q)
		d = 1 - cs
		return d
		
	def _calc_dist(self, p, q):
		if self.dist_met == 'manhattan':
			return self._manhattan(p, q)
		elif self.dist_met == 'euclidean':
			return self._euclidean(p, q)
		elif self.dist_met == 'cosine':
			return self._cosine(p, q)
		else: 
			raise ValueError("Unsupported Distance Metric")
	
	def update(self, Xtrain, Ytrain, Xtest, Ytest, Xval, Yval):
		self.X_train = Xtrain
		self.Y_train = Ytrain
		self.X_test = Xtest
		self.Y_test = Ytest
		self.X_val = Xval
		self.Y_val = Yval

	def prediction(self, X):
		p = []

		for point_test in X:
			ds = self._calc_dist(self.X_train, point_test)
			ki = np.argpartition(ds, self.k)[:self.k]
			knl = self.Y_train[ki]
			most_common_label = Counter(knl.flatten()).most_common(1)[0][0]
			p.append(most_common_label)

		return np.array(p)    
	