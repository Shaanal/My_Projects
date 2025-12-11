import numpy as np
import matplotlib.pyplot as plt

class LinearRegression:
    def __init__(self, degree=1, reg_type=None, lambda_=0.0, learning_rate=0.01, n_iterations=1000):
        self.degree = degree
        self.reg_type = reg_type
        self.lambda_ = lambda_
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.coefficients = None

    def fit(self, X, y):
        # Generate polynomial features
        X_poly = self._polynomial_features(X)
        # Add intercept term
        X_poly = np.hstack([np.ones((X_poly.shape[0], 1)), X_poly])
        
        # Initialize coefficients
        self.coefficients = np.zeros(X_poly.shape[1])
        
        # Gradient Descent
        for iteration in range(self.n_iterations):
            predictions = X_poly @ self.coefficients
            errors = predictions - y
            gradient = (X_poly.T @ errors) / X_poly.shape[0]
            
            # Regularization
            if self.reg_type == 'L2':
                gradient[1:] += (self.lambda_ / X_poly.shape[0]) * self.coefficients[1:]  # Regularize coefficients (excluding intercept)
            elif self.reg_type == 'L1':
                # L1 regularization (LASSO)
                gradient[1:] += (self.lambda_ / X_poly.shape[0]) * np.sign(self.coefficients[1:])
            
            self.coefficients -= self.learning_rate * gradient

            # Save the model at every iteration for visualization 
            # if (iteration+1)%100==0 :
            #     self.save_plot(X, y, iteration)
    
    def predict(self, X):
        X_poly = self._polynomial_features(X)
        X_poly = np.hstack([np.ones((X_poly.shape[0], 1)), X_poly])
        return X_poly @ self.coefficients

    def _polynomial_features(self, X):
        X_poly = np.vander(X.flatten(), N=self.degree + 1, increasing=True)
        return X_poly

    def calculate_metrics(self, X, y):
        y_pred = self.predict(X)
        mse = np.mean((y - y_pred) ** 2)
        std_dev = np.std(y - y_pred)
        variance = np.var(y - y_pred)
        return mse, std_dev, variance

    def save_plot(self, X, y, iteration):
        X_range = np.linspace(X.min(), X.max(), 100)
        y_pred = self.predict(X_range)
        
        plt.figure(figsize=(10, 6))
        plt.scatter(X, y, color='blue', label='Training Data')
        plt.plot(X_range, y_pred, color='red', label=f'Fitted Line/Curve (Degree {self.degree})')
        plt.title(f'Iteration {iteration + 1}')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.legend()
        plt.savefig(f"figures/plot_degree_{self.degree}_iteration_{iteration + 1}.png")
        plt.close()