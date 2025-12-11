import pandas as pd 
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
from scipy.stats import multivariate_normal
import random as rnd
import numpy as np

import os
import sys
sys.path.append("../../")

from models.kmeans.kmeans import KMeans_me
from models.gmm.gmm import GMM_me
from models.pca.pca import PCA

from models.knn.knn import KNN
from performance_measures.metrics import Metrics
import time

# 2 ######################################################
ds = '../../data/external/word-embeddings.feather'
d = pd.read_feather(ds)

# 3 ######################################################
# 3.2 #

def elbow_method(X, max_k, text=None):
	wcss = []
	for k in range(1, max_k+1):
		Xk = KMeans_me(X=X, k=k, n=50)
		wcss.append(Xk.getCost())

	plt.plot(range(1, max_k+1), wcss, marker = 'x', color = '#d62728')
	plt.xlabel('No. of clusters (k)')
	plt.ylabel('WCSS')
	plt.title('Elbow Method')
	plt.savefig(f"figures/{text}_KMeans_Elbow_Method.png")
	
X = np.stack(d['vit'].values)
elbow_method(X, max_k=25, text='3_2')

k_kmeans1 = 2
X_kmeans_k1 = KMeans_me(X=X, k=k_kmeans1, n=50)

# 4 #######################################################
# 4.2 #
gmm_me = GMM_me(X=X, k=2)

mix_coeff_me, means_me, covariances_me = gmm_me.getParams()
membership_me = gmm_me.getMembership()
likelihood_me = gmm_me.getLikelihood()

print(f"Likelihood (me GMM): {likelihood_me}")

from sklearn.mixture import GaussianMixture

gmm_sklearn = GaussianMixture(n_components=2, max_iter=100, tol=1e-4)
gmm_sklearn.fit(X)

membership_sklearn = gmm_sklearn.predict_proba(X)
likelihood_sklearn = gmm_sklearn.score(X)*200

print(f"Likelihood (Sklearn GMM): {likelihood_sklearn}")

def BIC(gmm):
		free_params = gmm.k * gmm.d + gmm.k * (gmm.d * (gmm.d + 1) / 2) + gmm.k - 1
		log_likelihood = gmm.getLikelihood()
		return -2 * log_likelihood + free_params * np.log(gmm.n)

def AIC(gmm):
		free_params = gmm.k * gmm.d + gmm.k * (gmm.d * (gmm.d + 1) / 2) + gmm.k - 1
		log_likelihood = gmm.getLikelihood()
		return -2 * log_likelihood + 2 * free_params

def evaluate_gmm(X, GMM_func, max_clusters=10, p=1, text=None):
	
	aic_scores = []
	bic_scores = []
	k_values = list(range(1, max_clusters + 1))
	
	for k in k_values:
		if GMM_func == GMM_me:
			gmm = GMM_me(X, k)
			aic = AIC(gmm)
			bic = BIC(gmm)
		elif GMM_func == GaussianMixture:
			gmm = GMM_func(n_components = k, max_iter=100, tol=1e-4)
			gmm.fit(X)
			aic = gmm.aic(X)
			bic = gmm.bic(X)
		
		aic_scores.append(aic)
		bic_scores.append(bic)
		print(f'For k={k}, AIC: {aic:.2f}, BIC: {bic:.2f}')
	
	if p!=0:
		plt.figure(figsize=(8, 5))
		plt.plot(k_values, aic_scores, label='AIC', marker='o', color = 'blue')
		plt.plot(k_values, bic_scores, label='BIC', marker='x', color = 'purple')
		plt.xlabel('Number of Clusters (k)')
		plt.ylabel('Score')
		plt.legend()
		plt.title('AIC and BIC for different k')
		plt.savefig(f"figures/{text}_AIC_BIC_scores_plot.png")
	
	k_range = range(1, max_clusters+1)
	optimal_k_bic = k_range[np.argmin(bic_scores)]
	optimal_k_aic = k_range[np.argmin(aic_scores)]
	
	return optimal_k_bic, optimal_k_aic

kb, ka = evaluate_gmm(X, GMM_me, text="4_2_My_GMM")
print('My_Optimal_k_BIC:', kb,'\nMy_Optimal_k_AIC:', ka)

kb, ka = evaluate_gmm(X, GaussianMixture, text="4_2_Sklearn_GMM")
print('Sklearn_Optimal_k_BIC:', kb,'\nSklearn_Optimal_k_AIC:', ka)

k_gmm1 = 1
X_gmm_k1 = GMM_me(X=X, k=k_gmm1, n=50)
mix_coeff_me, means_me, covariances_me = X_gmm_k1.getParams()
membership_me = X_gmm_k1.getMembership()
likelihood_me = X_gmm_k1.getLikelihood()

print(f"Likelihood (for k = k_gmm1 GMM): {likelihood_me}")

# 5 ######################################################
# 5.2 #

pca_2D = PCA(X = X, n_components=2)
pca_3D = PCA(X = X, n_components=3)

X_pca2D = pca_2D.transform()
X_pca3D = pca_3D.transform()

print(pca_2D.checkPCA(X_pca2D, X)) 
print(pca_3D.checkPCA(X_pca3D, X)) 

plt.scatter(X_pca2D[:, 0], X_pca2D[:, 1], c = 'purple')
plt.title('PCA - 2D Projection')
plt.xlabel('PC 1')
plt.ylabel('PC 2')
# plt.show()
# plt.savefig(f'figures/5_2_PCA_2D.png')

fig = plt.figure(figsize=(5, 5))
ax = fig.add_subplot(111, projection='3d')
ax.scatter(X_pca3D[:, 0], X_pca3D[:, 1], X_pca3D[:, 2], c = 'green')
ax.set_title('PCA - 3D Projection')
ax.set_xlabel('PC 1')
ax.set_ylabel('PC 2')
ax.set_zlabel('PC 3')
plt.savefig(f'figures/5_2_PCA_3D.png')

k2 = 3

# 6 #######################################################
# 6.1 #
X_kmeans_k2 = KMeans_me(X=X, k=k2)
kmeans_labels_k2 = X_kmeans_k2.predict()

# 6.2 #
pca = PCA(X = X, n_components=20)
X_expl_var_ratio = pca.expl_var_ratio
d = 20
max_d = range(1, d+1)

plt.plot(max_d, X_expl_var_ratio[:d], marker='o')
plt.title('Scree Plot')
plt.xlabel('Number of Components')
plt.ylabel('Variance Explained')
# plt.savefig(f'figures/6_2_Scree_Plot.png')

red_ds = PCA(X=X, n_components=5)
X_red_ds = red_ds.transform()
red_ds.checkPCA(X_red_ds, X)

# elbow_method(X_red_ds, max_k=20, text='6_2')

k_kmeans3 = 6
X_red_ds_kmeans3 = KMeans_me(X=X_red_ds, k=k_kmeans3)

# 6.3 #
X_gmm_k2 = GMM_me(X=X, k=k2)
gmm_labels_k2 = X_gmm_k2.predict()

# 6.4 #
print("My GMM:")
kb, ka = evaluate_gmm(X_red_ds, GMM_me, p=0)
print('Optimal_k_BIC:', kb,'\nOptimal_k_AIC:', ka)

print("\nSklearn GMM:")
kb, ka = evaluate_gmm(X_red_ds, GaussianMixture, p=0)
print('Optimal_k_BIC:', kb,'\nOptimal_k_AIC:', ka)

k_gmm3 = 1
X_red_ds_gmm3 = GMM_me(X=X_red_ds, k=k_gmm3, n=50)

# 7 ######################################################
# 7.1 #

from sklearn.metrics import silhouette_score

kmeans1_labels = X_kmeans_k1.predict()
kmeans_k2_labels = X_kmeans_k2.predict()
kmeans3_labels = X_red_ds_kmeans3.predict()

silhouette_kmeans1 = silhouette_score(X, kmeans1_labels)
silhouette_kmeans2 = silhouette_score(X, kmeans_k2_labels)
silhouette_kmeans3 = silhouette_score(X_red_ds, kmeans3_labels)

print(f"Silhouette Score for k_kmeans1: {silhouette_kmeans1:.4f}")
print(f"Silhouette Score for k_2: {silhouette_kmeans2:.4f}")
print(f"Silhouette Score for k_kmeans3: {silhouette_kmeans3:.4f}")

kmeans1_wcss = X_kmeans_k1.getCost()
kmeans_k2_wcss = X_kmeans_k2.getCost()
kmeans3_wcss = X_red_ds_kmeans3.getCost()

print(f"\nWCSS for k_kmeans1: {kmeans1_wcss:.4f}")
print(f"WCSS for k_2: {kmeans_k2_wcss:.4f}")
print(f"WCSS for k_kmeans3: {kmeans3_wcss:.4f}")

silhouette_scores_kmeans = [silhouette_kmeans1, silhouette_kmeans2, silhouette_kmeans3]
wcss_values = [kmeans1_wcss, kmeans_k2_wcss, kmeans3_wcss]
k_values = [f"kkmeans1 ({k_kmeans1})", f"k2 ({k2})", f"kkmeans3 ({k_kmeans3})"]

plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.bar(k_values, silhouette_scores_kmeans, color=['aquamarine', 'teal', 'purple'])
plt.title('Silhouette Scores')
plt.xlabel('KMeans Models')
plt.ylabel('Score')

plt.subplot(1, 2, 2)
plt.bar(k_values, wcss_values, color=['lightcoral', 'skyblue', 'pink'])
plt.title('WCSS Scores')
plt.xlabel('KMeans Models')
plt.ylabel('wcss')

plt.tight_layout()
plt.savefig(f'figures/7_1_KMeans_Cluster_Analysis.png')

k_kmeans = 6
X_kmeans = KMeans_me(X=X_red_ds, k=k_kmeans)
kmeans_labels = X_kmeans.predict()

# 7.2 #

gmm1_labels = X_gmm_k1.predict()
gmm2_labels = X_gmm_k2.predict()
gmm3_labels = X_red_ds_gmm3.predict()

log_likelihood_kgmm1 = X_gmm_k1.getLikelihood()
log_likelihood_k2 = X_gmm_k2.getLikelihood()
log_likelihood_kgmm3 = X_red_ds_gmm3.getLikelihood()

log_likelihoods = [log_likelihood_kgmm1, log_likelihood_k2, log_likelihood_kgmm3]
k_values_gmm = [f"kgmm1 ({k_gmm1})", f"k2 ({k2})", f"kgmm3 ({k_gmm3})"]

plt.figure(figsize=(8, 6))
plt.bar(k_values_gmm, log_likelihoods, color=['aquamarine', 'teal', 'purple'])

plt.ylabel('Log-Likelihood')
plt.title('Log-Likelihood for GMM Clustering with Different k Values')
plt.savefig(f'figures/7_2_GMM_Cluster_Analysis.png')

k_gmm = 3
X_gmm = GMM_me(X=X, k=k_gmm)
gmm_labels = X_gmm.predict()

# 7.3 #
silhouette_kmeans = silhouette_score(X_kmeans.X, kmeans_labels)
silhouette_gmm = silhouette_score(X_gmm.X, gmm_labels)
k_values = [f"k_kmeans ({k_kmeans})", f"k_gmm ({k_gmm})"]

print(f"Silhouette Score for K-Means: {silhouette_kmeans:.4f}")
print(f"Silhouette Score for GMM: {silhouette_gmm:.4f}")

plt.bar(k_values, [silhouette_kmeans, silhouette_gmm], color=['aquamarine', 'pink'])
plt.title('Silhouette Scores')
plt.xlabel('KMeans Models')
plt.ylabel('Score')
plt.tight_layout()

# plt.savefig(f'figures/7_3_Comparision_Kmeans_GMM')


# 8 #######################################################

import scipy.cluster.hierarchy as hc
from scipy.cluster.hierarchy import dendrogram, fcluster

linkage_methods = ['single', 'complete', 'average', 'ward'] 
dist_metrics = ['euclidean', 'cosine'] 

i = 0
plt.figure(figsize=(40, 60))
for method in linkage_methods:
	Z = hc.linkage(X, method=method, metric='euclidean')
	
	plt.subplot(4, 1, i+1)
	
	plt.title(f'Dendrogram for {method} linkage')
	dendrogram(Z)
	i+=1
plt.savefig(f'figures/8_Dendogram_method_metric_experiments_1.png')

plt.figure(figsize=(40, 40))
i = 0
for method in linkage_methods:
	Z = hc.linkage(X, method=method, metric='cosine')
	
	plt.subplot(4, 1, i+1)
	
	plt.title(f'Dendrogram for {method} linkage')
	dendrogram(Z)
	i+=1

	if i==3:
		break
plt.savefig(f'figures/8_Dendogram_method_metric_experiments_2.png')

linkage_matrix = hc.linkage(X, method='ward', metric='euclidean')  

clusters_k_kmeans = fcluster(linkage_matrix, t=k_kmeans, criterion='maxclust')
print(f'Clusters for k_kmeans ({k_kmeans} clusters):\n', clusters_k_kmeans)

clusters_k_gmm = fcluster(linkage_matrix, t=k_gmm, criterion='maxclust')
print(f'Clusters for k_gmm ({k_gmm} clusters):\n', clusters_k_gmm)

X_pca2D_gmm = PCA(X=X_gmm.X, n_components=2).transform()
X_pca2D_kmeans = PCA(X=X_red_ds, n_components=2).transform()

plt.figure(figsize=(16, 16))
plt.subplot(2, 2, 1)
sns.scatterplot(x=X_pca2D_kmeans[:, 0], y=X_pca2D_kmeans[:, 1], hue=kmeans_labels, palette='viridis', legend='full')
plt.title('K-Means Clusters')


plt.subplot(2, 2, 2)
sns.scatterplot(x=X_pca2D[:, 0], y=X_pca2D[:, 1], hue=clusters_k_kmeans, palette='viridis', legend='full')
plt.title('Hierarchical Clusters (kbest1)')

plt.subplot(2, 2, 3)
sns.scatterplot(x=X_pca2D[:, 0], y=X_pca2D[:, 1], hue=clusters_k_gmm, palette='viridis', legend='full')
plt.title('Hierarchical Clusters (kbest1)')


plt.subplot(2, 2, 4)
sns.scatterplot(x=X_pca2D_gmm[:, 0], y=X_pca2D_gmm[:, 1], hue=gmm_labels, palette='viridis', legend='full')
plt.title('GMM Clusters')

plt.savefig(f'figures/8_km_hc_gmm_Comparision.png')

# 9 ########################################################
# 9.1 #
ds = '../../data/interim/1/cleaned_spotify.csv'
X_sp = pd.read_csv(ds)

def frequency_encoding(X, col):
    f = X[col].value_counts()
    X[col] = X[col].map(f)
    return X

def Shuffle_n_Split(d, columns):
	def min_max_scaling(c):
		return (c-c.min())/(c.max()-c.min())
	def normalize(d, cols):
		dnorm = d.copy()
		for c in cols:
			dnorm[c] = dnorm[c].astype('float64')
			dnorm[c] = min_max_scaling(d[c])
		return dnorm
	def one_hot_encode(d, cols):
		d_ohe = pd.get_dummies(d, columns = cols, drop_first = True)
		return d_ohe
		
	dnorm = normalize(d, columns)
	d_ohe = one_hot_encode(dnorm, ['key'])
	oh_cols = [c for c in d_ohe.columns if c.startswith('key_')]
	d_ohe[oh_cols] = d_ohe[oh_cols].astype(int)
	labels = d_ohe['track_genre']

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

	return d_ohe, labels, X_train, X_test, X_val, Y_train, Y_test, Y_val

cat_cols = X_sp.select_dtypes(include = [object]).columns
X_sp_encd = X_sp.copy()
for c in cat_cols:
    X_sp_encd = frequency_encoding(X_sp_encd, c)
num_cols = X_sp_encd.select_dtypes(include=[np.number]).columns.tolist()

X_sp_new, labels, X_train, Y_train, X_test, Y_test, X_val, Y_val = Shuffle_n_Split(X_sp_encd, num_cols)
X_sp_new = X_sp_new.drop(columns = ['Unnamed: 0','track_genre', 'track_id', 'artists',
									'album_name', 'track_name', 'explicit'])

X_sp_pca = X_sp_new.values

pca_full= PCA(X = X_sp_pca, n_components=24)
X_sp_pca = pca_full.transform()
X_expl_var_ratio = pca_full.expl_var_ratio
d = 24
max_d = range(1, d+1)

plt.plot(max_d, X_expl_var_ratio[:d], marker='o')
plt.title('Scree Plot')
plt.xlabel('Number of Components')
plt.ylabel('Variance Explained')
plt.tight_layout()
# plt.savefig(f"figures/9_1_Scree_Plot.png")

opt_d = 3
X_sp_pca = X_sp_new.values
sp_pca = PCA(X=X_sp_pca, n_components=opt_d)
X_sp_pca = sp_pca.transform()

d_sp_pca = pd.DataFrame(X_sp_pca, columns=['PC1', 'PC2','PC3'])
d_sp_pca['track_genre'] = labels
	
shuf_i = np.random.RandomState(seed = 42).permutation(len(d_sp_pca))
d_shuf = d_sp_pca.iloc[shuf_i].reset_index(drop = True)

train_sz = int(0.8*len(d_shuf))
test_sz = int(0.1*len(d_shuf))
val_sz = 100-test_sz-train_sz

d_train = d_shuf[:train_sz]
d_test = d_shuf[train_sz:(train_sz + test_sz)]
d_val = d_shuf[(train_sz + test_sz):]

X_train_pca = d_train.drop(columns = ['track_genre'])
X_test_pca = d_test.drop(columns = ['track_genre'])
X_val_pca = d_val.drop(columns = ['track_genre'])

Y_train_pca = d_train['track_genre']
Y_test_pca = d_test['track_genre']
Y_val_pca = d_val['track_genre']

#best k and dist_met
k_knn = 28
dist_met = 'manhattan'

knn = KNN(k=k_knn, dm=dist_met)
knn.update(np.array(X_train_pca), np.array(Y_train_pca), 
				np.array(X_test_pca), np.array(Y_test_pca), 
				np.array(X_val_pca), np.array(Y_val_pca))

t_st = time.time()
Y_pred = knn.prediction(np.array(X_val_pca))
t_e = time.time()
inf_time_pca = t_e - t_st

metrics = Metrics(Y_val_pca, Y_pred)
accuracy = metrics.accuracy()

print(f"PCA + KNN Results:")
print(f"Accuracy: {accuracy:.4f}")
print('micro: P =', metrics.micro_average()[0],'R =',metrics.micro_average()[1], 'F1 =', metrics.micro_average()[2])
print('macro: P =', metrics.macro_average()[0],'R =',metrics.macro_average()[1], 'F1 =', metrics.macro_average()[2])
print('\n')
print(f"Inference Time: {inf_time_pca:.4f} seconds")

inf_time_org = 66.7

plt.figure(figsize=(8, 6))
plt.bar(['Original Dataset', 'PCA Reduced Dataset'], [inf_time_org, inf_time_pca])
plt.ylabel('Inference Time (seconds)')
plt.title('KNN Inference Time Comparison')
plt.savefig(f"figures/9_2_Inference_Time_Comparision.png")