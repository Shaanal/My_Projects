import pandas as pd
import matplotlib.pyplot as mpl
import plotly.express as px
import seaborn as sns
import numpy as np

import os

ds = '../../data/external/spotify.csv' #dataset.csv
ds_path = os.path.abspath(ds)

d = pd.read_csv(ds, low_memory=False)
d = d.dropna(subset = ['track_id', 'track_name'])
d = d.drop_duplicates(subset = 'track_id', keep = 'first')
d = d.drop_duplicates(subset = ['track_name', 'artists', 'popularity', 'duration_ms', 'explicit', 'danceability', 'energy',
                                 'key', 'loudness', 'mode', 'speechiness', 'acousticness',
                                 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature'], 
                                 keep = 'first')
d['explicit'] = d['explicit'].astype(int)

interim = '../../data/interim/1/cleaned_spotify.csv'
interim_path = os.path.abspath(interim)
os.makedirs(os.path.dirname(interim_path), exist_ok=True)

d.to_csv(interim_path, index=False)
#########################################################################################################
### Visualizations
dp = d.drop(d.columns[0], axis=1)

dp.hist(figsize=(12, 10), bins = 80, color= 'violet', edgecolor = 'indigo')
mpl.suptitle('Distribution of Numerical Features: Histogram: Frequency', fontsize=16)
mpl.ylabel('frequency')
mpl.savefig(f"figures/Histogram_features_frequency.png")

###############################################################################################
fig, axes = mpl.subplots(nrows=5, ncols=3, figsize=(16, 16))
axes = axes.flatten()
mpl.suptitle('Box Plots of the Numerical Features: Outliers', fontsize=18, y=1.05)

num_cols = ['popularity', 'duration_ms', 'explicit', 'danceability', 'energy',
           'key', 'loudness', 'mode', 'speechiness', 'acousticness',
           'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature']

for i, col in enumerate(num_cols):
    sns.boxplot(data=d, x=col, ax=axes[i], color='purple')
    axes[i].set_title(col)

mpl.tight_layout()
mpl.savefig(f"figures/Boxplots_outliers.png")

####################################################################################################
ndp = dp.select_dtypes(include=[np.number])
ndi_1 = ['popularity', 'duration_ms', 'time_signature', 'energy', 'explicit', 'mode']
ndp_1 = ndp[ndi_1]
corr_matrix_1 = ndp_1.corr()

ndi_2 = ['energy', 'key', 'loudness', 'danceability', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
ndp_2 = ndp[ndi_2]
corr_matrix_2 = ndp_2.corr()  

mpl.figure(figsize=(10, 8))
sns.heatmap(corr_matrix_1, annot=True, cmap='plasma', center=0.4)
mpl.title('Correlation Heatmap', fontsize=16)
mpl.savefig(f"figures/Heatmap_1.png")

mpl.figure(figsize=(10, 8))
sns.heatmap(corr_matrix_2, annot=True, cmap='viridis')
mpl.title('Correlation: Sound types Heatmap', fontsize=16)
mpl.savefig(f"figures/Heatmap_2.png")

#################################################################################################
ndp_3 = dp.groupby('track_genre')[ndi_2].mean().reset_index()

ndp_3['track_genre_numeric'] = ndp_3['track_genre'].astype('category').cat.codes
fig = px.parallel_coordinates(ndp_3, 
                              dimensions=ndi_2, 
                              color='track_genre_numeric',
                              color_continuous_scale=px.colors.sequential.Viridis,
                              title="Parallel Coordinates Plot of Features by Track Genre")

fig.write_image(f"figures/Parallel_Coordinates.png")

##################################################################################################
grouped_dp = dp.groupby('track_genre')[ndi_2 + ['popularity']].mean().reset_index()

grouped_dp.hist(figsize=(12, 10), bins = 80, color= 'violet', edgecolor = 'indigo')
mpl.suptitle('Distribution of Numerical Features: Histogram: Genres', fontsize=16)
mpl.ylabel('frequency')
mpl.savefig(f"figures/Histogram_per_genre.png")
 
######################################################################################################
### KNN

import sys
sys.path.append("../../")

from models.knn.knn import KNN
from performance_measures.metrics import Metrics

def min_max_scaling(c):
    return (c-c.min())/(c.max()-c.min())
def normalize(d, cols):
    dnorm = d.copy()
    for c in cols:
        dnorm[c] = min_max_scaling(d[c])
    return dnorm
def one_hot_encode(d, cols):
    d_ohe = pd.get_dummies(d, columns = cols, drop_first = True)
    return d_ohe
    
dnormcols = ['popularity', 'duration_ms', 'loudness', 'tempo', 'time_signature']
dnorm = normalize(d, dnormcols)
d_ohe = one_hot_encode(dnorm, ['key'])
oh_cols = [c for c in d_ohe.columns if c.startswith('key_')]
d_ohe[oh_cols] = d_ohe[oh_cols].astype(int)
    
shuf_i = np.random.RandomState(seed = 42).permutation(len(d_ohe))
d_shuf = d_ohe.iloc[shuf_i].reset_index(drop = True)

train_sz = int(0.8*len(d_shuf))
test_sz = int(0.1*len(d_shuf))
val_sz = 100-test_sz-train_sz

d_train = d_shuf[:train_sz]
d_test = d_shuf[train_sz:(train_sz + test_sz)]
d_val = d_shuf[(train_sz + test_sz):]

X_train = d_train.drop(columns=['Unnamed: 0','track_genre', 'track_id', 'artists',
                                 'album_name', 'track_name', 'explicit'])
X_test = d_test.drop(columns=['Unnamed: 0','track_genre', 'track_id', 'artists',
                               'album_name', 'track_name', 'explicit'])
X_val = d_val.drop(columns=['Unnamed: 0','track_genre', 'track_id', 'artists',
                             'album_name', 'track_name', 'explicit'])

Y_train = d_train['track_genre']
Y_test = d_test['track_genre']
Y_val = d_val['track_genre']

metric = 'manhattan'
for k in range(20, 31):
	kn = KNN(k, metric)
	kn.update(X_train.to_numpy(), Y_train.to_numpy(), 
				X_test.to_numpy(), Y_test.to_numpy(), 
				X_val.to_numpy(), Y_val.to_numpy())
	Y_val_pred = kn.prediction(X_val.to_numpy())
	h = Metrics(Y_val.to_numpy(), Y_val_pred)
	print(k,'\n')
	print('accuracy = ', h.accuracy())
	print('precision scores = ', h.precision())
	print('recall scores = ', h.recall())
	print('micro: P =', h.micro_average()[0],'R =',h.micro_average()[1], 'F1 =', h.micro_average()[2])
	print('macro: P =', h.macro_average()[0],'R =',h.macro_average()[1], 'F1 =', h.macro_average()[2])
	print('\n')
     
metric = 'euclidean'
for k in range(25, 31):
	kn = KNN(k, metric)
	kn.update(X_train.to_numpy(), Y_train.to_numpy(), 
				X_test.to_numpy(), Y_test.to_numpy(), 
				X_val.to_numpy(), Y_val.to_numpy())
	Y_val_pred = kn.prediction(X_val.to_numpy())
	h = Metrics(Y_val.to_numpy(), Y_val_pred)
	print(k,'\n')
	print('accuracy = ', h.accuracy())
	print('precision scores = ', h.precision())
	print('recall scores = ', h.recall())
	print('micro: P =', h.micro_average()[0],'R =',h.micro_average()[1], 'F1 =', h.micro_average()[2])
	print('macro: P =', h.macro_average()[0],'R =',h.macro_average()[1], 'F1 =', h.macro_average()[2])
	print('\n')
     
# Thus the best {k, dist_metric} = {28, 'manhattan'}

print("Y_pred shape:", Y_val_pred.shape)
print("Y_val shape:", Y_val.shape)
print("Y_pred values:", Y_val_pred)
print("Y_val values:", Y_val.to_numpy())

####################################################################################
#### Linear Regression

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from models.linear_regression.linear_regression import LinearRegression

dl = '../../data/external/linreg.csv' #dataset.csv
dl_path = os.path.abspath(dl)
data = pd.read_csv(dl_path)
X = data['x'].values
y = data['y'].values

# Shuffle the data
shuffled_indices = np.random.permutation(len(X))
X = X[shuffled_indices]
y = y[shuffled_indices]

# Split the data (80:10:10)
train_size = int(0.8 * len(X))
val_size = int(0.1 * len(X))
test_size = len(X) - train_size - val_size

X_train, X_val, X_test = X[:train_size], X[train_size:train_size+val_size], X[train_size+val_size:]
y_train, y_val, y_test = y[:train_size], y[train_size:train_size+val_size], y[train_size+val_size:]

##############################################################################################################
plt.scatter(X_train, y_train, color='blue', label='Training Data')
plt.scatter(X_test, y_test, color='red', label='Test Data')
plt.scatter(X_val, y_val, color='yellow', label='Validation Data')

plt.legend()
plt.title('Linear Regression Fit')
plt.xlabel('X')
plt.ylabel('y')
plt.savefig(f"figures/split.png")

##############################################################################################################

# Instantiate the LinearRegression model
model = LinearRegression(degree=1)

# Fit the model
model.fit(X_train, y_train)

train_mse, train_std_dev, train_variance = model.calculate_metrics(X_train, y_train)
test_mse, test_std_dev, test_variance = model.calculate_metrics(X_test, y_test)
val_mse, val_std_dev, val_variance = model.calculate_metrics(X_val, y_val)
# Predict and evaluate on training set

print(f"Train MSE: {train_mse}, Variance: {train_variance}, Standard Deviation: {train_std_dev}")
print(f"Test MSE: {test_mse}, Variance: {test_variance}, Standard Deviation: {test_std_dev}")
print(f"Val MSE: {val_mse}, Variance: {val_variance}, Standard Deviation: {val_std_dev}")

##############################################################################################################

plt.scatter(X_train, y_train, color='blue', label='Training Data')
plt.plot(X_train, model.predict(X_train), color='red', label='Fitted Line')
plt.legend()
plt.title('Linear Regression Fit')
plt.xlabel('X')
plt.ylabel('y')
plt.savefig(f"figures/fittedline_deg_1.png")

##############################################################################################################

def plot_for_degree(degree, X_train, y_train, X_test, y_test, iteration):
    model = LinearRegression(degree=degree)
    model.fit(X_train, y_train)
    
    mse_train, std_dev_train, var_train = model.calculate_metrics(X_train, y_train)
    mse_test, std_dev_test, var_test = model.calculate_metrics(X_test, y_test)
    

    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    plt.scatter(X_train, y_train, color='blue', label='Training Data')
    X_range = np.linspace(X_train.min(), X_train.max(), 100)
    plt.plot(X_range, model.predict(X_range), color='red', label=f'Fitted Line/Curve (Degree {degree})')
    plt.title(f'Training Data and Fitted Line/Curve (Degree {degree})')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.legend()
    
    plt.subplot(2, 2, 2)
    plt.bar(['Train', 'Test'], [mse_train, mse_test], color=['blue', 'orange'])
    plt.title('Mean Squared Error')
    
    plt.subplot(2, 2, 3)
    plt.bar(['Train', 'Test'], [std_dev_train, std_dev_test], color=['blue', 'orange'])
    plt.title('Standard Deviation')

    plt.subplot(2, 2, 4)
    plt.bar(['Train', 'Test'], [var_train, var_test], color=['blue', 'orange'])
    plt.title('Variance')
    
    plt.tight_layout()
    plt.savefig(f"figures/PerDegree_{degree}")
   
    # plt.savefig(f"figures/plot_degree_{degree}_iteration_{iteration}.jpg")
    plt.close()

for degree in range(1, 21):
    plot_for_degree(degree, X_train, y_train, X_test, y_test, degree)

##############################################################################################################


