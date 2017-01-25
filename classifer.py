import numpy as np
import pandas as pd
import sklearn
from sklearn.preprocessing import StandardScaler

def read_data(featurefile,datafile):
	k=0;
	feature_list = list()
	feature_dic = dict()
	for line in open(featurefile, "r"):
		x = line.strip().split(';')
		xid = x[0].split(':')[1]
		feature_name = x[1].split('/')[1]
		feature_list.append(feature_name)
		feature_dic[xid] = k
		k += 1
	print feature_dic,feature_list
	index = []
	data = []
	for line in open(datafile,"r"):
		x = line.strip().split('\t')
		entity = x[0]
		index.append(entity)
		features = x[1].split(';')
		fdata = dict()
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
			fdata[feature_list[feature_dic[fid]]] = fval;
		data.append(fdata)
	df = pd.DataFrame(data,index = index)

	df.fillna(np.nan)
	# noneed = ['areaCode','timeZone','postalCode','motto','leaderName','leaderParty','area']
	selected_list = ['country','areaLand','foundingDate',\
	'areaMetro','areaTotal','areaWater','percentageOfAreaWater','populationDensity','populationTotal','populationUrban','utcOffset','elevation']
	# print df['foundingDate'].astype('timedelta64[M]')

	print df.info()
	df['areaTotal'] = df['areaTotal'].fillna(df['areaWater']+df['areaLand'])
	df['areaTotal'] = df['areaTotal'].fillna(df['area'])
	df['areaWater'] = df['areaWater'].fillna(df['areaTotal']-df['areaLand'])
	df['areaWater'] = df['areaWater'].fillna(0)
	df['areaMetro'] = df['areaMetro'].fillna(0)
	df['elevation'] = df['elevation'].fillna(int(df['elevation'].mean()))
	df['foundingDate'] = df['foundingDate'].fillna(int(df['foundingDate'].mean()))
	df['areaLand'] = df['areaLand'].fillna(df['areaTotal']-df['areaWater'])
	df['populationUrban'] = df['populationUrban'].fillna(df['populationTotal'])
	df['populationTotal'] = df['populationTotal'].fillna(df['populationUrban'])
	df['populationDensity'] = df['populationDensity'].fillna(df['populationTotal']/df['areaTotal'])
	
	df['percentageOfAreaWater'] = df['percentageOfAreaWater'].fillna(df['areaWater']/df['areaTotal'])
	print df[selected_list].info()
	df[selected_list].dropna(subset = ['areaTotal']).to_csv('city.csv')
	df = pd.get_dummies(df[selected_list],dummy_na = True).dropna()
	d1 = pd.read_csv('city.csv')
	print d1.info()
	# X = df.values
	# stdsc = StandardScaler()
	# X_std = stdsc.fit_transform(X)



read_data("testInstance_PropertyList.txt","testInstanceFeature.txt")
