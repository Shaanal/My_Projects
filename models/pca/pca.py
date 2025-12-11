import numpy as np

class PCA:
	def __init__(self, X, n_components=None):
		self.X = X
		self.new_d = n_components
		self.new_d_comp = None
		self.means_cent = None
		self.means = None
		self.covariance = None
		self.expl_var_ratio = None
		self.fit()
		
	def fit(self):
		self.means = np.mean(self.X, axis=0)
		self.means_cent = self.X - self.means
		
		cov_matrix = np.cov(self.means_cent, rowvar=False)
		eig_vals, eig_vecs = np.linalg.eigh(cov_matrix)
		
		sorted_i = np.argsort(eig_vals)[::-1]

		eig_vals = eig_vals[sorted_i]
		eig_vecs = eig_vecs[:, sorted_i]
		
		if self.new_d is not None:
			self.new_d_comp = eig_vecs[:, :self.new_d]
			
		self.expl_var_ratio = eig_vals / np.sum(eig_vals)

	def transform(self, X = None):
		if X is not None:
			means_cent = self.X - self.means
		else:
			means_cent = self.means_cent
		X_red = np.dot(means_cent, self.new_d_comp)
		if X_red.ndim == 1:
			X_red = X_red.reshape(-1, 1)
		return X_red

	def checkPCA(self, X_red, X):
		X_red = self.transform()
		X_recon = np.dot(X_red, self.new_d_comp.T) + self.means
		recon_error = np.mean((X - X_recon)**2)
		threshold = 0.05
		if recon_error < threshold:
			return True
		else:
			return False
