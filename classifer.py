import numpy as np
import pandas as pd
import pickle
import sklearn
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from libact.base.dataset import Dataset, import_libsvm_sparse
from libact.models import *
from libact.query_strategies import *
from libact.labelers import IdealLabeler,InteractiveLabeler
from libact.base.interfaces import QueryStrategy,ContinuousModel,ProbabilisticModel
from libact.utils import inherit_docstring_from, zip
from amt import Amt
from sklearn.cluster import KMeans
import time

def pre_data(featurefile,datafile):
	selected_list = ['id','country','areaLand','foundingDate','areaMetro','areaTotal',\
	'areaWater','percentageOfAreaWater','populationDensity','populationTotal','populationUrban','utcOffset','elevation']
	k=0;
	feature_list = list()
	feature_dic = dict()
	for line in open(featurefile, 'r'):
		x = line.strip().split(';')
		xid = x[0].split(':')[1]
		feature_name = x[1].split('/')[1]
		feature_list.append(feature_name)
		feature_dic[xid] = k
		k += 1
	print feature_dic,feature_list
	index = []
	data = []
	for line in open(datafile,'r'):
		x = line.strip().split('\t')
		loc = x[0].index(',')
		eid = x[0][:loc]
		name = x[0][loc+1:]
		if name.find('%')>0:
			continue
		index.append(eid)
		features = x[1].split('$')
		fdata = dict()
		fdata['id'] = int(eid)
		fdata['name'] = name
		for f in features:
			fid,fval = f.split(',',1)[:2]
			if fval[0]!='"':
				if fid!='23697' and fid!='5194':
					fval = float(fval)
				else:
					fval = 2017 - int(fval[:4])
			else:
				fval = fval.lower()
				if fid == '25480':
					if len(fval)< 3 or len(fval)>7:
						fval = 0.0
					else:
						fval = int(fval)
			fdata[feature_list[feature_dic[fid]]] = fval
		data.append(fdata)
	df = pd.DataFrame(data,index = index)

	df.fillna(np.nan)
	# noneed = ['country','areaCode','timeZone','postalCode','motto','leaderName','leaderParty','area']
	selected_list = ['id','name','country','areaLand','foundingDate','areaMetro','areaTotal',\
	'areaWater','percentageOfAreaWater','populationDensity','populationTotal','populationUrban','utcOffset','elevation']
	# print df['foundingDate'].astype('timedelta64[M]')

	df['areaTotal'] = df['areaTotal'].fillna(df['areaWater']+df['areaLand'])
	df['areaTotal'] = df['areaTotal'].fillna(df['area'])
	areaW = df[df['areaTotal'] < df['areaWater']+df['areaLand']]['areaWater']
	areaL = df[df['areaTotal'] < df['areaWater']+df['areaLand']]['areaLand']
	areaIndex = df['areaTotal'] < df['areaWater']+df['areaLand']
	print areaIndex
	df.loc[areaIndex,'areaTotal'] = areaW + areaL
	print df[df['areaTotal'] < df['areaWater']+df['areaLand']][['areaTotal','areaWater','areaLand']]

	df['areaWater'] = df['areaWater'].fillna(df['areaTotal']-df['areaLand'])
	df['areaWater'] = df['areaWater'].fillna(0)
	df['areaMetro'] = df['areaMetro'].fillna(0)
	df['elevation'] = df['elevation'].fillna(int(df['elevation'].mean()))
	df['utcOffset'] = df['utcOffset'].fillna(int(df['utcOffset'].mean()))
	df['foundingDate'] = df['foundingDate'].fillna(int(df['foundingDate'].mean()))
	df['areaLand'] = df['areaLand'].fillna(df['areaTotal']-df['areaWater'])
	df['populationUrban'] = df['populationUrban'].fillna(df['populationTotal'])
	df['populationTotal'] = df['populationTotal'].fillna(df['populationUrban'])
	df['populationDensity'] = df['populationDensity'].fillna(df['populationTotal']/df['areaTotal']*1000000)
	df['percentageOfAreaWater'] = df['percentageOfAreaWater'].fillna(df['areaWater']/df['areaTotal']*100)
	df['country'] = df['country'].str.strip('"')
	print df[selected_list].info()
	df[selected_list].dropna(subset = ['areaTotal','country','percentageOfAreaWater','populationTotal']).to_csv('city.csv')

def read_data():
	selected_atrributes = ['areaLand','foundingDate','areaMetro','areaTotal',\
	'areaWater','percentageOfAreaWater','populationDensity','populationTotal','populationUrban','utcOffset','elevation']
	selected_info = ['id','name','country']
	df = pd.read_csv('city.csv')
	return df[selected_atrributes],df[selected_info]

def make_query(dataset,model,method):
	model.train(dataset)
	unlabeled_entry_ids, X_pool = zip(*dataset.get_unlabeled_entries())
    
	if isinstance(model, ContinuousModel):
		dvalue = model.predict_real(X_pool)
	elif isinstance(model, ProbabilisticModel):
		dvalue = model.predict_proba(X_pool)

	if method == 'lc':  # least confident
		# ask_id = np.argmin(np.max(dvalue, axis=1))
		ask_ids = np.argsort(np.max(dvalue, axis=1))[:5]

	elif method == 'sm':  # smallest margin
		if np.shape(dvalue)[1] > 2:
	    # Find 2 largest decision values
			dvalue = -(np.partition(-dvalue, 2, axis=1)[:, :2])
		margin = np.abs(dvalue[:, 0] - dvalue[:, 1])
		X,_ = zip(*dataset.data)
		cluster_data = [X[i] for i in np.argsort(margin)[:100]]
		label = KMeans(n_clusters=5,random_state=0).fit(cluster_data).labels_
		lset = set([])
		# ask_id = np.argmin(margin)
		ask_ids = []
		for i in range(100):
			if not label[i] in lset:
				lset.add(label[i])
				ask_ids.append(np.argsort(margin)[i])

	elif method == 'entropy':
		entropy = np.sum(-dvalue * np.log(dvalue), axis=1)
		# ask_id = np.argmax(entropy)
		ask_ids = np.argsort(entropy)[-5:]
	return [unlabeled_entry_ids[ask_id] for ask_id in ask_ids]

def ask_hit(df,ask_ids,train_ds,sandboxFlag):
	city2id = dict(zip(df['name'], range(len(df['name']))))
	amt = Amt(sandboxFlag)
	for i in ask_ids:
		train_ds.update(i,-1)
	if sandboxFlag:
		f = open('sand_hit_ids','a')
	else:
		f = open('hit_ids','a')
	namel =  [df['name'][i] for i in ask_ids]
	countryl =  [df['country'][i] for i in ask_ids]
	hit_id = amt._Create_City_Hit(namel,countryl,'big')['hit_id']
	
	f.write(hit_id+'$')  # python will convert \n to os.linesep
	for i in ask_ids:
		f.write(str(i)+' ')
	f.write('\n')
	f.close()
	
	finish_hits = set(amt._GetReviewable_Hits())
	print finish_hits
	print hit_id
	while not (hit_id in finish_hits):
		time.sleep(10)
		finish_hits = set(amt._GetReviewable_Hits())

	[ins_result, attribute_result] = amt._Retrive_HIT_Answer(hit_id)
	for yn in ins_result:
		if ins_result[yn]>0:
			train_ds.update(city2id[yn],1)
		else:
			train_ds.update(city2id[yn],-1)
		print("Answer:{0},Count:{1}".format(yn,ins_result[yn]))
	
	for ar in attribute_result:
		print("Attribtue:{0},Count:{1}".format(ar,attribute_result[ar]))
	return train_ds

def get_labels(df,sandboxFlag):
	city2id = dict(zip(df['name'], range(len(df['name']))))
	amt = Amt(sandboxFlag)
	y = [None]* len(df['name'])
	if sandboxFlag:
		f = open('sand_hit_ids','r')
	else:
		f = open('hit_ids','r')
	for line in f:
		lines = line.split('$')
		hit_id = lines[0]
		ask_ids = [int(x) for x in lines[1].strip().split(' ')]
		for i in ask_ids:
			y[i] = -1
		[ins_result, attribute_result] = amt._Retrive_HIT_Answer(hit_id)
		for yn in ins_result:
			if ins_result[yn]>0:
				y[city2id[yn]]=1
			else:
				y[city2id[yn]]=-1
	return y



def main():
	sandboxFlag = False
	quota = 5
	df,amt_info_df = read_data()
	X = StandardScaler().fit_transform(df.values)
	y = get_labels(amt_info_df,sandboxFlag)
	train_ds = Dataset(X,y)
	model = SVM()
	model.train(train_ds)
	print 'init score is ',model.score(train_ds)
	for i in range(quota):
		ask_ids = make_query(train_ds,model,'sm')
		print ask_ids
		train_ds = ask_hit(amt_info_df,ask_ids,train_ds,sandboxFlag)
		model.train(train_ds)
		print 'score ',i,'th is ',model.score(train_ds)


#pre_data('testInstance_PropertyList.txt','testInstanceFeature1.txt')
if __name__ == '__main__':
	main()
