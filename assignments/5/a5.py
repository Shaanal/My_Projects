import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt
from numpy.linalg import norm
from scipy.stats import multivariate_normal
import librosa
import librosa.display
from sklearn.model_selection import train_test_split
from hmmlearn.hmm import GaussianHMM
from sklearn.metrics import accuracy_score
import re

import os
import sys
sys.path.append("../../")
from models.gmm.gmm import GMM_me
from models.kde.kde import KDE

def generate_synthetic_data(noise_val = 0.12):

	def circle(num_points, radius, center):
		r = radius * np.sqrt(np.random.rand(num_points))  
		theta = np.random.rand(num_points) * 2 * np.pi   
		x = center[0] + r * np.cos(theta)
		y = center[1] + r * np.sin(theta)

		data = np.column_stack((x, y))

		noise = np.random.normal(loc=0, scale=noise_val, size=data.shape)
		data += noise
		
		return data
	
	large_circle = circle(3000, radius=2, center=(0, 0))
	small_circle = circle(500, radius=0.2, center=(1, 1))
	
	plt.figure(figsize=(8, 8))
	plt.scatter(large_circle[:, 0], large_circle[:, 1], s=1, color='purple')
	plt.scatter(small_circle[:, 0], small_circle[:, 1], s=1, color='purple')
	plt.legend()
	plt.axis([-4, 4, -4, 4])
	plt.savefig(f"figures/original_data.png")

	return np.vstack([large_circle, small_circle])

data = generate_synthetic_data()

def plot3D(data, model, fig, h=None, i=None, mn=None, resolution=100):
	x_min, x_max = data[:, 0].min() - 1, data[:, 0].max() + 1
	y_min, y_max = data[:, 1].min() - 1, data[:, 1].max() + 1
	x_vals = np.linspace(x_min, x_max, resolution)
	y_vals = np.linspace(y_min, y_max, resolution)
	xx, yy = np.meshgrid(x_vals, y_vals)
	grid_points = np.vstack([xx.ravel(), yy.ravel()]).T

	if model == 'KDE':
		kde = KDE(hyperparameter='gaussian',dimension=2, bandwidth=h)
		kde.fit(data)
		densities = kde.predict(grid_points).reshape(xx.shape)
		if i is not None:
			ax = fig.add_subplot(mn[0], mn[1], i + 1, projection='3d')
		else:
			ax = fig.add_subplot(111, projection='3d')
		ax.plot_surface(xx, yy, densities, cmap='plasma', alpha=0.5)
		ax.scatter(data[:, 0], data[:, 1], np.zeros_like(data[:, 0]), color='red', s=5)
		ax.set_title(f"KDE with Bandwidth {h}")
		ax.set_xlabel("x")
		ax.set_ylabel("y")
		ax.set_zlabel("Density")

	elif model == 'GMM':
		gmm = GMM_me(X=data, k=h)
		clusters = gmm.means
		covariances = gmm.covariance
		mixing_weights = gmm.mix_coeff
		densities = np.zeros((len(grid_points), gmm.k))
		for j in range(gmm.k):
			densities[:, j] = multivariate_normal.pdf(grid_points, mean=clusters[j], cov=covariances[j])
		weighted_densities = np.dot(densities, mixing_weights)
		weighted_densities = weighted_densities.reshape(xx.shape)
		if i is not None:
			ax = fig.add_subplot(mn[0], mn[1], i + 1, projection='3d')
		else:
			ax = fig.add_subplot(111, projection='3d')
		surf = ax.plot_surface(xx, yy, weighted_densities, cmap='plasma')
		# fig.colorbar(surf, ax=ax)
		ax.scatter(data[:, 0], data[:, 1], np.zeros_like(data[:, 0]))
		ax.set_xlabel("x")
		ax.set_ylabel("y")
		ax.set_zlabel("Density")
		plt.tight_layout()
		
gmm = GMM_me(X=data, k=2)

resolution = 100
x_min, x_max = data[:, 0].min() - 1, data[:, 0].max() + 1
y_min, y_max = data[:, 1].min() - 1, data[:, 1].max() + 1

x_vals = np.linspace(x_min, x_max, resolution)
y_vals = np.linspace(x_min, x_max, resolution)
xx, yy = np.meshgrid(x_vals, y_vals)
grid_points = np.c_[xx.ravel(), yy.ravel()]
clusters = gmm.predict(data)
cluster_centers = gmm.means

plt.figure(figsize=(6, 6))
plt.scatter(data[:, 0], data[:, 1], c=clusters, cmap='plasma', s=1)
plt.scatter(cluster_centers[:, 0], cluster_centers[:, 1], c='red', marker='x', s=50, label='Cluster Centers')
plt.title('GMM with 2 Components')
plt.xlim((-4, 4))
plt.ylim((-4, 4))
plt.xlabel('x')
plt.ylabel('y')
plt.savefig(f"figures/GMM_clustering.png")

k_values = [2, 3, 4]
plt.figure(figsize=(18, 6))

for i, k in enumerate(k_values):
    gmm_k = GMM_me(X=data, k=k)
    
    clusters = gmm_k.predict(data)
    cluster_centers = gmm_k.means
    
    plt.subplot(1, len(k_values), i + 1)
    plt.scatter(data[:, 0], data[:, 1], c=clusters, cmap='plasma', s=1)
    plt.scatter(cluster_centers[:, 0], cluster_centers[:, 1], marker='x', s=25, c='red')
    plt.title(f'GMM Clusters with k={k}')
    plt.xlabel('x')
    plt.ylabel('y')

plt.tight_layout()
plt.savefig(f"figures/GMM_k_clustering.png")

kde = KDE(hyperparameter='gaussian', dimension=2, bandwidth=1.0)
kde.fit(data)

kde.visualize(x_range=(-4, 4), y_range=(-4, 4))
fig = plt.figure(figsize=(4, 4))
plot3D(data, 'KDE', fig, h=1)
plt.savefig(f"figures/KDE_3D.png")

hs = [0.05, 0.1, 0.3, 0.5, 1, 2]

fig = plt.figure(figsize=(20, 12))
for i, h in enumerate(hs):
    plot3D(data, 'KDE', fig, h, i=i, mn=[2,3])

plt.savefig(f"figures/KDE_3D_bandwidths.png")

ks = [2, 3, 4, 5, 6, 7]

fig = plt.figure(figsize=(20, 12))
for i, h in enumerate(ks):
    plot3D(data, 'GMM', fig, h, i=i, mn=[2,3])

plt.savefig(f"figures/GMM_3D_ks.png")


#####################################################

DATASET_PATH = "../../data/external/Dataset_3/recordings/"

class MFCC:
	def __init__(self, dataset_path=None, filepath=None):
		self.fp = filepath if filepath is not None else '1_lucas_1.wav'
		self.dp = dataset_path if dataset_path is not None else DATASET_PATH
		self.data = self.load_dataset()

	def extract_mfcc(self, fp = None, n_mfcc=13):
		if fp is None:
			fp = self.fp
		signal, sr = librosa.load(fp)
		mfcc = librosa.feature.mfcc(y=signal, sr=sr, n_mfcc=13)  
		return mfcc

	def visualize_mfcc(self, digit, sample):
		mfcc = self.data[digit][sample]
		plt.figure(figsize=(10, 4))
		n_coeffs = mfcc.shape[0]

		librosa.display.specshow(mfcc, x_axis='time', cmap='plasma')
		plt.colorbar(format='%+2.0f dB')
		plt.xlabel('Time (s)')
		plt.ylabel('MFCC Coefficients')
		plt.yticks(ticks=range(n_coeffs), labels=[f'{i+1}' for i in range(n_coeffs)])
		plt.title(f'MFCC for Digit {digit}')
		plt.tight_layout() 
		plt.savefig(f"figures/MFCC_visualize_sample.png")
		
	def load_dataset(self):
		recordings = [f for f in os.listdir(self.dp) if f.endswith('.wav')]
		data = {}

		for file in recordings:
			file_path = os.path.join(self.dp, file)
			mfcc = self.extract_mfcc(fp = file_path)
			digit = int(file.split('_')[0]) 
			if digit not in data:
				data[digit] = []
			data[digit].append(mfcc)

		self.data = data		
		return data

mfcc = MFCC()
data = mfcc.data
mfcc.visualize_mfcc(1, 9)

train_data = {}
test_data = {}
for digit, mfcc_list in data.items():
	train_mfccs, test_mfccs = train_test_split(mfcc_list, test_size=0.2, random_state=42)
	train_data[digit] = train_mfccs
	test_data[digit] = test_mfccs


class HMM:
	def __init__(self, n_components=5, n_iter=1000, cov_type='diag'):
		self.n_components = n_components
		self.n_iter = n_iter
		self.cov_type = cov_type
		self.models = {}

	def train(self, train_data):
		for digit, mfcc in train_data.items():
			if mfcc:
				flat_mfcc = np.concatenate([m.T for m in mfcc])
				len_s = [m.shape[1] for m in mfcc]
				model = GaussianHMM(n_components=self.n_components, covariance_type=self.cov_type, n_iter=self.n_iter)
				model.fit(flat_mfcc, len_s)
				self.models[digit] = model
				print(f"Trained HMM for digit {digit}.")
		print("Training complete for all digits.")

	def predict(self, sample):
		scores = {}
		for digit, model in self.models.items():
			try:
				scores[digit] = model.score(sample)
			except:
				scores[digit] = float('-inf')  
		return max(scores, key=scores.get)

	def evaluate(self, test_data):
		correct_predictions = 0
		total = 0
		for td, mfcc_list in test_data.items():
			for mfcc in mfcc_list:
				pd = self.predict(mfcc.T)
				if pd == td:
					correct_predictions += 1
				total += 1
		accuracy = correct_predictions / total
		return accuracy

hmm = HMM(n_components=5, n_iter=1000, cov_type='diag')
hmm.train(train_data)

accuracy = hmm.evaluate(test_data)
print(f"Final Test Accuracy: {accuracy * 100:.2f}%")

personal_files = [
	{'file': '../../data/external/shaanal_audio/0_shaanal_1.wav', 'expected_label': 0},
	{'file': '../../data/external/shaanal_audio/1_shaanal_0.wav', 'expected_label': 1},
	{'file': '../../data/external/shaanal_audio/2_shaanal_0.wav', 'expected_label': 2},
	{'file': '../../data/external/shaanal_audio/3_shaanal_0.wav', 'expected_label': 3},
	{'file': '../../data/external/shaanal_audio/4_shaanal_0.wav', 'expected_label': 4},
	{'file': '../../data/external/shaanal_audio/5_shaanal_0.wav', 'expected_label': 5},
	{'file': '../../data/external/shaanal_audio/6_shaanal_0.wav', 'expected_label': 6},
	{'file': '../../data/external/shaanal_audio/7_shaanal_0.wav', 'expected_label': 7},
	{'file': '../../data/external/shaanal_audio/8_shaanal_0.wav', 'expected_label': 8},
	{'file': '../../data/external/shaanal_audio/9_shaanal_0.wav', 'expected_label': 9}
]

personal_predictions = []
personal_true_labels = []
dataset_path = '../../data/external/shaanal_audio'
for file_info in personal_files:
	file_path = file_info['file']
	expected_label = file_info['expected_label']
	
	mfcc_m = MFCC(filepath=file_path)
	mfcc = mfcc_m.extract_mfcc()
	# mfcc.visualize_mfcc(1, 9)

	predicted_digit = hmm.predict(mfcc)
	# accuracy = hmm.evaluate(test_data)
	# print(f"Final Test Accuracy: {accuracy * 100:.2f}%")
	personal_predictions.append(predicted_digit)
	personal_true_labels.append(expected_label)

accuracy_personal = accuracy_score(personal_true_labels, personal_predictions)
print(f"Recognition Accuracy on Personal Recordings: {accuracy_personal * 100:.2f}%")
