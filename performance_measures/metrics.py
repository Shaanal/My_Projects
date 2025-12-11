import numpy as np

class Metrics:
	def __init__(self, y, y_p):
		self.y_true = np.array(y)
		self.y_pred = np.array(y_p)
		self.labels = np.unique(y)

	def accuracy(self):
		# A = TP+TN/total
		tp_tn = np.sum(self.y_true == self.y_pred)
		tot = len(self.y_true)
		A = tp_tn/tot
		return A
	
	def precision(self):  
		# P = TP/(TP+FP)
		Pscores = {}
		for label in self.labels:
			tp = np.sum((self.y_true == label) & (self.y_pred == label))
			fp = np.sum((self.y_true != label) & (self.y_pred == label))
			Pscores[label] = tp/(tp+fp) if tp+fp > 0 else 0 
		return Pscores

	def recall(self):
		# R = TP/(TP+FN)
		Rscores = {}
		for label in self.labels:
			tp = np.sum((self.y_true == label) & (self.y_pred == label))
			fn = np.sum((self.y_true == label) & (self.y_pred != label))
			Rscores[label] = tp/(tp+fn) if tp+fn > 0 else 0
		return Rscores
	
	def _macro_P(self, classes):
		Ps = []
		for c in classes:
			tp = np.sum((self.y_true == c) & (self.y_pred == c))
			pp = np.sum(self.y_pred == c)
			p = tp/pp if pp > 0 else 0 
			Ps.append(p)
		P = np.sum(Ps)/len(classes)
		return P
	def _macro_R(self, classes):
		Rc = []
		for c in classes:
			tp = np.sum((self.y_true == c) & (self.y_pred == c))
			ap = np.sum(self.y_true == c)
			r = tp/ap if ap > 0 else 0
			Rc.append(r)
		R = np.sum(Rc)/len(classes)
		return R 
	def macro_f1_score(self, classes):
		P = self._macro_P(classes)
		R = self._macro_R(classes)
		F1 = 2*(P*R)/(P+R) if (P+R) > 0 else 0
		return F1
	
	def _micro_P(self):
		tp = 0
		fp = 0
		for label in self.labels:
			tp += np.sum((self.y_true == label) & (self.y_pred == label))
			fp += np.sum((self.y_true != label) & (self.y_pred == label))
		pp = tp + fp
		P = tp/pp if pp > 0 else 0 
		return P
	def _micro_R(self):
		tp = 0
		fn = 0
		for label in self.labels:
			tp += np.sum((self.y_true == label) & (self.y_pred == label))
			fn += np.sum((self.y_true == label) & (self.y_pred != label))
		ap = tp + fn
		R = tp/ap if ap > 0 else 0
		return R 
	def micro_f1_score(self):
		P = self._micro_P()
		R = self._micro_R()
		F1 = 2*(P*R)/(P+R) if (P+R) > 0 else 0
		return F1
	
	def macro_average(self):
		P = self._macro_P(self.labels)
		R = self._macro_R(self.labels)
		F1 = self.macro_f1_score(self.labels)
		return P, R, F1

	def micro_average(self):
		P = self._micro_P()
		R = self._micro_R()
		F1 = self.micro_f1_score()
		return P, R, F1

#f-1 score, accuracy, precision, and recall after splitting the provided dataset into train and val subsets. 