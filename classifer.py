import numpy as np
import pandas as pd
import pickle
import sklearn
from sklearn.preprocessing import StandardScaler
from libact.base.dataset import Dataset, import_libsvm_sparse
from libact.models import *
from libact.query_strategies import *
from libact.labelers import IdealLabeler,InteractiveLabeler
from libact.base.interfaces import QueryStrategy,ContinuousModel,ProbabilisticModel
from libact.utils import inherit_docstring_from, zip
from amt import Amt

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
		dvalue = model.predict_proba(X_pool)
	elif isinstance(model, ProbabilisticModel):
		dvalue = model.predict_real(X_pool)

	if method == 'lc':  # least confident
		# ask_id = np.argmin(np.max(dvalue, axis=1))
		ask_ids = np.argsort(np.max(dvalue, axis=1))[:5]

	elif method == 'sm':  # smallest margin
		if np.shape(dvalue)[1] > 2:
	    # Find 2 largest decision values
			dvalue = -(np.partition(-dvalue, 2, axis=1)[:, :2])
		margin = np.abs(dvalue[:, 0] - dvalue[:, 1])
		# ask_id = np.argmin(margin)
		ask_ids = np.argsort(margin)[:5]

	elif method == 'entropy':
		entropy = np.sum(-dvalue * np.log(dvalue), axis=1)
		# ask_id = np.argmax(entropy)
		ask_ids = np.argsort(entropy)[-5:]
	return [unlabeled_entry_ids[ask_id] for ask_id in ask_ids]

def ask_hit(df,ask_ids,train_ds):
	city2id = dict(zip(df['name'], range(len(df['name']))))
	sandboxFlag = True
	cityamt = Amt(sandboxFlag)
	
	if sandboxFlag:
		f = open('sand_hit_ids','a')
	else:
		f = open('hit_ids','a')
	hit_ids = []
	namel =  [df['name'][i] for i in ask_ids]
	countryl =  [df['country'][i] for i in ask_ids]
	hit_id = cityamt._Create_City_Hit(namel,countryl,'big')
	hit_ids.append(hit_id['hit_id'])
	f.write(hit_id['hit_id']+'\n')  # python will convert \n to os.linesep
	f.close()
	finish_hits = set([x.HITId for x in cityamt.mtc.get_reviewable_hits()])
	print finish_hits
	# while not (hit_id['hit_id'] in finish_hits):
	# 	finish_hits = set([x.HITId for x in cityamt.mtc.get_reviewable_hits()])
	for hit_id in hit_ids:
		[ins_result, attribute_result] = cityamt._Retrive_HIT_Answer(hit_id)
		for yn in ins_result:
			if ins_result[yn]>1:
				train_ds.update(city2id[yn],1)
			else:
				train_ds.update(city2id[yn],0)
			print("Answer:{0},Count:{1}".format(yn,ins_result[yn]))
		for ar in attribute_result:
			print("Attribtue:{0},Count:{1}".format(ar,attribute_result[ar]))
	return train_ds

def main():
	df,amt_info_df = read_data()
	X = StandardScaler().fit_transform(df.values)
	with open('label','rb') as f:
		label = pickle.load(f)
	# y_train = [1,1,0,1,1,1,0,0,0,1,1,1,1,0,1]
	print X.shape[0]
	print len(label)
	train_ds = Dataset(X,label)
	model = LogisticRegression()
	quota = 1
	model.train(train_ds)
	print model.score(train_ds)
	for i in range(quota):
		ask_ids = make_query(train_ds,model,'lc')
		print ask_ids
		train_ds = ask_hit(amt_info_df,ask_ids,train_ds)
		model.train(train_ds)
		print model.score(train_ds)


#pre_data('testInstance_PropertyList.txt','testInstanceFeature1.txt')
main()
