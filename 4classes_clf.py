import numpy as np
import pandas as pd
import random
import pickle
import sklearn
from sklearn import svm
from sklearn import preprocessing
from libact.base.dataset import Dataset, import_libsvm_sparse
from sklearn.model_selection import train_test_split
from libact.query_strategies import *
from libact.labelers import IdealLabeler,InteractiveLabeler
from libact.base.interfaces import QueryStrategy,ContinuousModel,ProbabilisticModel
from libact.utils import inherit_docstring_from, zip
from amt import Amt
from sklearn.cluster import KMeans
import time
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

def pre_data(name):
	df = pd.read_csv('clf_data/instanceFeature_'+name+'.csv',na_values='null')
	df.fillna(np.nan)
	print df.info()


	df['releaseDate'] = pd.to_numeric(df['releaseDate'].dropna().str[:4])
	# df['activeYearsStartYear'] = df['activeYearsStartYear'].fillna(pd.to_numeric(df['activeYearsStartDate'].dropna().str[:4]))
	# df['birthDate'] = pd.to_numeric(df['birthDate'].dropna().str[:4])
	# df['draftRound'] = pd.to_numeric(df['draftRound'].dropna(),errors='coerce')
	# df['draftPick'] = pd.to_numeric(df['draftPick'].dropna(),errors='coerce')
	# df['position'] = df['position'].str.lower()
	df['country'] = df['country'].str.replace('Cinema_of_','')
	df['country'] = df['country'].str.replace('the_','')

	df = df.dropna(subset = ['gross','budget','runtime','releaseDate','country']).dropna(axis = 1,how = 'any')
	print df.info()
	df = df[~df['name'].str.contains('%')]
	df = df[~df['country'].str.contains('%',na=False)]
	df = df[df['budget']>1000]
	df['profit'] = df['gross'] - df['budget']
	print df.info()
	df.to_csv('clf_data/data_'+name+'.csv')
	# df.to_csv('clf_data/data_'+name+'1.csv')


def publish_job(flag,dataname,adjname):
	selectlist = dict()
	selectlist['building'] =  ['openingYear','yearOfConstruction','lastyears','cost']
	selectlist['mammal-animal'] =  ['genus','family','order']
	selectlist['football-athlete'] =  ['birthDate','draftYear','activeYearsStartYear','activeYearsEndYear','playtime','weight','height','position','draftRound','draftPick']
	selectlist['film'] =  ['country','releaseDate','runtime','budget','gross','profit']
	datalist = dict()
	datalist['building'] =  ['openingYear','yearOfConstruction','lastyears','cost']
	datalist['mammal-animal'] =  ['genus','family','order']
	datalist['football-athlete'] =  ['birthDate','draftYear','activeYearsStartYear','activeYearsEndYear','playtime','weight','height','draftRound','draftPick','center','guard','cb','ot','s','rb','wr','lb','dt','de','coach','k','p','qb','sp']
	datalist['film'] =  ['country','releaseDate','runtime','budget','gross','profit']

	df = pd.read_csv('clf_data/data_'+dataname+'.csv')
	# print df.info()
	# idlist = range(len(df['name']))
	# random.shuffle(idlist)
	# ask_ids = idlist[:200]
	# name2id = dict(zip(df['name'], range(len(df['name']))))
	cluster_data =  pd.get_dummies(df[datalist[dataname]]).values
	cluster_data = preprocessing.StandardScaler().fit_transform(cluster_data)
	label = KMeans(n_clusters=200,random_state=0).fit(cluster_data).labels_
	# print label
	lset = set([])
		# ask_id = np.argmin(margin)
	ask_ids = []
	for i in range(len(df)):
		if not label[i] in lset:
			lset.add(label[i])
			ask_ids.append(i)
	# print len(ask_ids)
	amt = Amt(flag,dataname)
	f = open('hit_ids-'+dataname+'.txt','w')
	namel =  [df['name'][i] for i in ask_ids]
	infol =  [str(df.loc[i,selectlist[dataname]])[:str(df.loc[i,selectlist[dataname]]).find('Name')].encode("utf-8") for i in ask_ids]
	index = 0

	while index<len(ask_ids):
		hit_id = amt._Create_City_Hit(dataname,namel[index:index+5],infol[index:index+5],adjname)['hit_id']
		f.write(hit_id+'$')  # python will convert \n to os.linesep
		for ename in namel[index:index+5]:
			f.write(ename+' ')
		f.write('\n')
		index += 5
	f.close()

def get_amt_answer(flag,dataname,label_k,feature_k):
	amt = Amt(flag,dataname)
	df = pd.read_csv('clf_data/data_'+dataname+'.csv')
	name2id = dict(zip(df['name'], range(len(df['name']))))
	selectlist = dict()
	selectlist['building'] =  ['openingYear','yearOfConstruction','lastyears','cost']
	selectlist['mammal-animal'] =  ['genus','family','order']
	selectlist['football-athlete'] =  ['birthDate','draftYear','activeYearsStartYear','activeYearsEndYear','playtime','weight','height','position','draftRound','draftPick']
	selectlist['film'] =  ['country','releaseDate','runtime','budget','gross','profit']
	feature_count = dict()
	for f_name in selectlist[dataname]:
		feature_count[f_name] = 0

	y = [None]* len(df['name'])

	finish_hits = set(amt._GetReviewable_Hits())
	for line in open('hit_ids-'+dataname,'r'):
		lines = line.split('$')
		hit_id = lines[0]
		ask_ids = [name2id[x] for x in lines[1].strip().split(' ')]
		for i in ask_ids:
			if y[i]==None:
				y[i] = -1
		while not (hit_id in finish_hits):
			time.sleep(10)
			finish_hits = set(amt._GetReviewable_Hits())
		[ins_result, attribute_result] = amt._Retrive_HIT_Answer(hit_id)
		print ins_result
		print attribute_result
		for yn in ins_result:
			if ins_result[yn]>label_k:
				y[name2id[yn]]=1
			else:
				y[name2id[yn]]=-1
		for ar in attribute_result:
			feature_count[ar] += int(attribute_result[ar])
	
	flist = []
	for f_name in selectlist[dataname]:
		if feature_count[f_name]> feature_k:
			flist.append(f_name)
	return y,flist


def test(X,y):
	'''run test test dataset'''
	names = ["Nearest Neighbors", "Linear SVM", "RBF SVM", "Gaussian Process",\
     "Decision Tree", "Random Forest", "Neural Net", "AdaBoost",\
     "Naive Bayes", "QDA"]	
	
	classifiers = [
    KNeighborsClassifier(3),
    SVC(kernel="linear", C=0.025),
    SVC(gamma=2, C=1),
    GaussianProcessClassifier(1.0 * RBF(1.0), warm_start=True),
    DecisionTreeClassifier(max_depth=5),
    RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
    MLPClassifier(alpha=1),
    AdaBoostClassifier(),
    GaussianNB(),
    QuadraticDiscriminantAnalysis()]
	
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
	print '==================='
	res = dict()
	for name, clf in zip(names, classifiers):
		clf.fit(X_train, y_train)
		print name,clf.score(X_test,y_test)
		res[name] = clf.score(X_test,y_test)
	return res
	# result.append(res)
	# res_df = pd.DataFrame(result,index = range(len(result)))
	# res_df.to_csv('city_result.csv')

def main(dataname):
	sandboxFlag = True
	label_k = 0
	feature_k = 0
	df = pd.read_csv('clf_data/data_'+dataname+'.csv')
	datalist = dict()
	datalist['building'] =  ['openingYear','yearOfConstruction','lastyears','cost']
	datalist['mammal-animal'] =  ['genus','family','order']
	datalist['football-athlete'] =  ['birthDate','draftYear','activeYearsStartYear','activeYearsEndYear','playtime','weight','height','draftRound','draftPick','center','guard','cb','ot','s','rb','wr','lb','dt','de','coach','k','p','qb','sp']
	datalist['film'] =  ['country','releaseDate','runtime','budget','gross','profit']

	y,flist = get_amt_answer(sandboxFlag,dataname,label_k,feature_k)
	X = preprocessing.StandardScaler().fit_transform(pd.get_dummies(df[flist]).values)
	dataset = Dataset(X,y)
	X,y = zip(*dataset.get_labeled_entries())
	print X, y, flist
	# test(X,y)

	


if __name__ == '__main__':
	main('film')

