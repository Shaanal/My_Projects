from scipy.stats import multivariate_normal
import numpy as np

class GMM_me:
	def __init__(self, X, k, n=100, tol=1e-4):
		self.X = X
		self.k = k
		self.max_itr = n
		self.tol = tol
		self.n, self.d = self.X.shape
		self.mix_coeff = None
		self.means = None
		self.covariance = None
		self._mix_coeff_fit()
		self._means_fit()
		self._covariance_fit()
		self.fit()
	
	def fit(self):
		log_likelihoods = []	
		
		for _ in range(self.max_itr):
			# E-step: 
			resp = self._expectation(self.X)
			
			# M-step:
			self._maximization(self.X, resp)
			
			# Convergence
			log_likelihood = self.getLikelihood()
			log_likelihoods.append(log_likelihood)
			if len(log_likelihoods) > 1 and abs(log_likelihoods[-1] - log_likelihoods[-2]) < self.tol:
				break

	def _mix_coeff_fit(self):
		self.mix_coeff = np.random.rand(self.k)
		self.mix_coeff /= np.sum(self.mix_coeff) 
	def _means_fit(self):
		self.means = self.X[np.random.choice(self.n, self.k, replace=False)]
	def _covariance_fit(self):
		self.covariance = np.array([np.eye(self.d)] * self.k)

	def _expectation(self, X):
		log_resp = np.zeros((self.n, self.k))
		for i in range(self.k):
			try:
				log_pdf = multivariate_normal.logpdf(X, mean=self.means[i], cov=self.covariance[i], allow_singular=True)
				log_resp[:, i] = np.log(self.mix_coeff[i] + 1e-10) + log_pdf
			except ValueError as er:
				print(f"{i}-Covariance matrix is not valid:")
				print(self.covariance[i])
				raise er		
		log_resp -= np.logaddexp.reduce(log_resp, axis=1, keepdims=True)
		resp = np.exp(log_resp)
		return resp
	def _maximization(self, X, resp):
		self.mix_coeff = np.mean(resp, axis=0)
		N_k = np.sum(resp, axis=0)
		N_k = np.maximum(N_k, 1e-6)
		for i in range(self.k):
			self.means[i] = np.sum(resp[:, i].reshape(-1, 1) * X, axis=0) / N_k[i]
			diff = X - self.means[i]
			self.covariance[i] = np.dot((resp[:, i].reshape(-1, 1)*diff).T, diff) / N_k[i]
			self.covariance[i] += np.eye(self.d) * 1e-6
		

	def getParams(self):
		return self.mix_coeff, self.means, self.covariance

	def getMembership(self, X=None):
		if X is not None:
			return self._expectation(X)
		else:
			return self._expectation(self.X)
	
	def getLikelihood(self):
		log_likelihood = 0.0   
		lws = np.zeros(self.n)
		for i in range(self.k):
			try:
				log_pdf = multivariate_normal.logpdf(self.X, mean=self.means[i], cov=self.covariance[i], allow_singular=True)
				lws = np.logaddexp(lws, np.log(self.mix_coeff[i] + 1e-10) + log_pdf)

			except ValueError as er:
				print(f"{i}-Covariance matrix is not valid:")
				print(self.covariance[i])
				raise er
		
		log_likelihood = lws.sum()
		return log_likelihood
	
	def predict(self, X=None):
		if X is not None:
			return self.getMembership(X).argmax(axis=1)
		else:
			return self.getMembership(self.X).argmax(axis=1)