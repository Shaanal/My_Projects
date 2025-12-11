import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class KDE:
	def __init__(self, hyperparameter, dimension, bandwidth):
		self.hyperparameter = hyperparameter
		self.n = dimension
		self.h = bandwidth
		# self.w = weights

	def norm(self, x, x_i):
		return np.power(np.sum((x - x_i) ** self.n, axis=1), 1/self.n)

	def fit(self, x):
		self.X = np.array(x)

	def kernel(self, dist):
		if self.hyperparameter == 'box':
			return 0.5 * (np.abs(dist) <= 1)
		elif self.hyperparameter == 'gaussian':
			return (1 / np.sqrt(2 * np.pi)) * np.exp(-0.5 * dist ** 2)
		elif self.hyperparameter == 'triangular':
			return (1 - np.abs(dist)) * (np.abs(dist) <= 1)

	def predict(self, x):
		densities = []
		for x_i in x:
			x_i = np.array(x_i).reshape(1, -1)
			dx = self.predict_at_x(x_i)
			densities.append(dx)
		return np.array(densities)

	def predict_at_x(self, x_i):
		dist = self.norm(self.X, x_i) / self.h
		kernel_values = self.kernel(dist)
		dx = np.sum(kernel_values) / (len(self.X) * self.h ** self.X.shape[1])	
		return dx 

	def visualize(self, x_range, y_range, resolution=100):
		x_min, x_max = self.X[:, 0].min() - 1, self.X[:, 0].max() + 1
		y_min, y_max = self.X[:, 1].min() - 1, self.X[:, 1].max() + 1

		x_vals = np.linspace(x_min, x_max, resolution)
		y_vals = np.linspace(y_min, y_max, resolution)
		xx, yy = np.meshgrid(x_vals, y_vals)
		grid_points = np.vstack([xx.ravel(), yy.ravel()]).T
		densities = self.predict(grid_points).reshape(xx.shape)
		
		plt.figure(figsize=(8, 6))
		plt.contourf(xx, yy, densities, cmap='viridis')
		plt.scatter(self.X[:, 0], self.X[:, 1], color='black', s=2, alpha=0.5)
		plt.colorbar(label="Density")
		plt.title(f"KDE Density Estimation with {self.hyperparameter.capitalize()} Kernel")
		plt.xlabel("X-axis")
		plt.ylabel("Y-axis")
		plt.gca().set_aspect('equal', adjustable='box')	
		plt.savefig(f"figures/KDE_visualize.png")