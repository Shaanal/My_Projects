import pandas as pd
import numpy as np
import wandb
from sklearn.metrics import accuracy_score

class MLP:
	def __init__(self, input_size, hidden_layers, hidden_neurons_perlayer, output_size, learning_rate=0.01, activation='relu', optimizer='sgd', batch_size=None, epochs=100, log_scores=False):
		
		self.input_size = input_size
		self.hidden_layers = hidden_layers
		self.hidden_neurons = hidden_neurons_perlayer
		if len(self.hidden_neurons) != hidden_layers:
			raise ValueError(f"hidden_layers and no. of elements in hidden_neurons do not match.")
		self.output_size = output_size

		self.lr = learning_rate
		self.actv_func, self.actv_der = self.get_activation_function(activation)
		self.optimizer = optimizer
		if self.optimizer == 'mini_batch_gd':
			if batch_size is None:
				raise ValueError("No Batch size: must be specified for Mini-Batch Gradient Descent")
			self.batch_size = batch_size
		else:
			self.batch_size = None

		self.epochs = epochs
		self.weights = []
		self.biases = []
		self.losses = []
		self.initialize_wandb()

		self.log_scores = log_scores		

	def initialize_wandb(self):
		layer_szs = [self.input_size] + self.hidden_neurons + [self.output_size]
		for i in range(len(layer_szs) - 1):
			weight_matrix = np.random.randn(layer_szs[i], layer_szs[i + 1]) * np.sqrt(2 / layer_szs[i])
			bias_vector = np.zeros((1, layer_szs[i + 1]))
			self.weights.append(weight_matrix)
			self.biases.append(bias_vector)
	
	def _sigmoid(self, x):
		return 1 / (1 + np.exp(-x))

	def _sigmoid_der(self, x):
		return self._sigmoid(x) * (1 - self._sigmoid(x))

	def _tanh(self, x):
		return np.tanh(x)

	def _tanh_der(self, x):
		return 1 - self._tanh(x)**2

	def _relu(self, x):
		return np.maximum(0, x)

	def _relu_der(self, x):
		return np.where(x > 0, 1, 0)

	def _linear(self, x):
		return x

	def _linear_der(self, x):
		return x/x

	def get_activation_function(self, name):
		if name == 'sigmoid':
			return self._sigmoid, self._sigmoid_der
		elif name == 'tanh':
			return self._tanh, self._tanh_der
		elif name == 'relu':
			return self._relu, self._relu_der
		elif name == 'linear':
			return self._linear, self._linear_der
		else:
			raise ValueError(f"Unknown activation function: {name}")

	def forward_propagation(self, X):
		self.z = []
		self.A = [X]

		for i in range(self.hidden_layers): 
			z = np.dot(self.A[i], self.weights[i]) + self.biases[i]
			self.z.append(z)
			a = self.actv_func(z)
			self.A.append(a)

		z = np.dot(self.A[-1], self.weights[-1]) + self.biases[-1]
		self.z.append(z)
		a = self.softmax(z)  
		self.A.append(a)

		return a

	def softmax(self, x):
		e_x = np.exp(x - np.max(x, axis=1, keepdims=True))
		return e_x / np.sum(e_x, axis=1, keepdims=True)

	def compute_loss(self, X, y_true):
		Y_pred = self.forward_propagation(X)
		loss = -np.mean(np.sum(y_true * np.log(Y_pred + 1e-15), axis=1))
		return loss

	def back_propagation(self, X, y, g=None):
		m = X.shape[0]
		dz = self.A[-1] - y  
		dzs = []
		dzs.append(dz)

		for i in reversed(range(self.hidden_layers)):
			error_i = dzs[-1].dot(self.weights[i + 1].T)
			dz_i = error_i * self.actv_der(self.z[i])
			dzs.append(dz_i)

		dzs = list(reversed(dzs))
		dw = []
		db = []
		
		for i in range(len(self.weights)):
			dw_i = np.dot(self.A[i].T, dzs[i]) / m
			dw.append(dw_i)
			db_i = np.sum(dzs[i], axis=0, keepdims=True) / m
			db.append(db_i)

		if g is None:
			self.update_weights(dw, db)
		return dw, db

	def update_weights(self, dw, db):
		for i in range(len(self.weights)):
			self.weights[i] -= self.lr * dw[i]
			self.biases[i] -= self.lr * db[i] 

	def fit(self, X_train, Y_train, X_val, Y_val, early_stopping=False):
		if self.optimizer == "sgd":
			self.fit_sgd(X_train, Y_train, X_val, Y_val, es=early_stopping, patience=100)
		elif self.optimizer == "mini_batch_gd":
			self.fit_mini_batch_gd(X_train, Y_train, X_val, Y_val, es=early_stopping, patience=100)
		elif self.optimizer == "batch_gd":
			self.fit_batch_gd(X_train, Y_train, X_val, Y_val, es=early_stopping, patience=100)

	def fit_sgd(self, X_train, Y_train, X_val=None, Y_val=None, es=False, patience=5):
		self.batch_size = 1
		for epoch in range(self.epochs):
			for i in range(0, X_train.shape[0], self.batch_size):
				X_batch = X_train[i:i + self.batch_size]
				Y_batch = Y_train[i:i + self.batch_size]

				Y_pred = self.forward_propagation(X_batch)
				dw, db = self.back_propagation(X_batch, Y_batch)

			Y_train_pred = self.predict(X_train)
			train_loss = self.compute_loss(X_train, Y_train)

			self.losses.append(train_loss)

			if X_val is not None and Y_val is not None:
				Y_val_pred = self.predict(X_val)
				if (epoch + 1) % 100 == 0:
					val_loss = self.compute_loss(X_val, Y_val)
					print(f'Epoch {epoch + 1}/{self.epochs}, Train Loss: {train_loss}, Validation Loss: {val_loss}')
					
				if es and self.early_stopping(val_loss, patience):
					print(f"Early stopping... at epoch {epoch}")
					break

				val_acc = accuracy_score(np.argmax(Y_val, axis=1), Y_val_pred)

			elif (epoch + 1) % 100 == 0:
				print(f'Epoch {epoch + 1}/{self.epochs}, Train Loss: {train_loss}')

			train_acc = accuracy_score(np.argmax(Y_train, axis=1), Y_train_pred)

			# if self.log_scores:
			# 	wandb.log({
			# 		"epoch": epoch,
			# 		"train_loss": train_loss,
			# 		"val_loss": val_loss,
			# 		"train_accuracy": train_acc,
			# 		"val_accuracy": val_acc
			# 	})
			
		# wandb.finish()

	def fit_mini_batch_gd(self, X_train, Y_train, X_val=None, Y_val=None, es=False, patience=5):
		for epoch in range(self.epochs):
			for i in range(0, X_train.shape[0], self.batch_size):
				X_batch = X_train[i:i + self.batch_size]
				Y_batch = Y_train[i:i + self.batch_size]

				Y_pred = self.forward_propagation(X_batch)
				dw, db = self.back_propagation(X_batch, Y_batch)

			Y_train_pred = self.forward_propagation(X_train)
			train_loss = self.compute_loss(X_train, Y_train)
			self.losses.append(train_loss)

			if X_val is not None and Y_val is not None:
				Y_val_pred = self.forward_propagation(X_val)
				if (epoch + 1) % 100 == 0:
					val_loss = self.compute_loss(X_val, Y_val)
					print(f'Epoch {epoch + 1}/{self.epochs}, Train Loss: {train_loss}, Validation Loss: {val_loss}')
					
				if es and self.early_stopping(val_loss, patience):
					print(f"Early stopping... at epoch {epoch}")
					break
				val_acc = accuracy_score(np.argmax(Y_val, axis=1), Y_val_pred)

			elif (epoch + 1) % 100 == 0:
				print(f'Epoch {epoch + 1}/{self.epochs}, Train Loss: {train_loss}')

			train_acc = accuracy_score(np.argmax(Y_train, axis=1), Y_train_pred)

			# if self.log_scores:
			# 	wandb.log({
			# 		"epoch": epoch,
			# 		"train_loss": train_loss,
			# 		"val_loss": val_loss,
			# 		"train_accuracy": train_acc,
			# 		"val_accuracy": val_acc
			# 	})
			
		# wandb.finish()
		
	def fit_batch_gd(self, X_train, Y_train, X_val=None, Y_val=None, es=False, patience=5):
		for epoch in range(self.epochs):

			Y_train_pred = self.forward_propagation(X_train)
			dw, db = self.back_propagation(X_train, Y_train)

			train_loss = self.compute_loss(X_train, Y_train)
			self.losses.append(train_loss)

			if X_val is not None and Y_val is not None:
				Y_val_pred = self.forward_propagation(X_val)
				if (epoch + 1) % 100 == 0:
					val_loss = self.compute_loss(X_val, Y_val)
					print(f'Epoch {epoch + 1}/{self.epochs}, Train Loss: {train_loss}, Validation Loss: {val_loss}')
					
				if es and self.early_stopping(val_loss, patience):
					print(f"Early stopping... at epoch {epoch}")
					break

				val_acc = accuracy_score(np.argmax(Y_val, axis=1), Y_val_pred)

			elif (epoch + 1) % 100 == 0:
				print(f'Epoch {epoch + 1}/{self.epochs}, Train Loss: {train_loss}')

			train_acc = accuracy_score(np.argmax(Y_train, axis=1), Y_train_pred)

			# if self.log_scores:
			# 	wandb.log({
			# 		"epoch": epoch,
			# 		"train_loss": train_loss,
			# 		"val_loss": val_loss,
			# 		"train_accuracy": train_acc,
			# 		"val_accuracy": val_acc
			# 	})
			
		# wandb.finish()

	def early_stopping(self, val_loss, patience):
		if len(self.losses) > patience and val_loss >= min(self.losses[-patience:]):
			return True
		return False

	def predict(self, X):
		Y_pred = self.forward_propagation(X)
		return np.argmax(Y_pred, axis=1)

	def comp_num_grad(self, X, y, epsilon = 1e-5):
		num_d_w = []
		num_d_b = []

		for i in range(len(self.weights)):

			num_w = np.zeros_like(self.weights[i])
			for j in range(self.weights[i].shape[0]):
				for k in range(self.weights[i].shape[1]):
					original_weight = self.weights[i][j, k]

					self.weights[i][j, k] = original_weight + epsilon
					plus_cost = self.compute_loss(X, y)
					self.weights[i][j, k] = original_weight - epsilon
					minus_cost = self.compute_loss(X, y)

					num_w[j, k] = (plus_cost - minus_cost) / (2 * epsilon)
					self.weights[i][j, k] = original_weight

			num_d_w.append(num_w)

			num_b = np.zeros_like(self.biases[i])
			for j in range(self.biases[i].shape[1]):
				original_bias = self.biases[i][0, j]

				self.biases[i][0, j] = original_bias + epsilon
				plus_cost = self.compute_loss(X, y)
				self.biases[i][0, j] = original_bias - epsilon
				minus_cost = self.compute_loss(X, y)

				num_b[0, j] = (plus_cost - minus_cost) / (2 * epsilon)
				self.biases[i][0, j] = original_bias

			num_d_b.append(num_b)

		return num_d_w, num_d_b

	def gradient_check(self, X, y):
		y_pred = self.forward_propagation(X)
		dw, db = self.back_propagation(X, y, 1)

		num_d_w, num_d_b = self.comp_num_grad(X, y)

		for i in range(len(self.weights)):
			relative_diff_weights = np.linalg.norm(dw[i] - num_d_w[i]) / (np.linalg.norm(dw[i]) + np.linalg.norm(num_d_w[i]))
			if relative_diff_weights > 1e-7:
				print(f"Gradient Check passed for weights at layer {i + 1}, Difference - {relative_diff_weights}")
			else:
				print(f"Gradient Check passed for weights at layer {i + 1}, Difference - {relative_diff_weights}")

			relative_diff_biases = np.linalg.norm(db[i] - num_d_b[i]) / (np.linalg.norm(db[i]) + np.linalg.norm(num_d_b[i]))
			if relative_diff_biases > 1e-7:
				print(f"Gradient Check failed for biases at layer {i + 1}, Difference - {relative_diff_biases}")
			else:
				print(f"Gradient Check passed for biases at layer {i + 1}, Difference - {relative_diff_biases}")