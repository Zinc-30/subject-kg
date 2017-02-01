# imports the Boto library so that it can be used
import boto
import collections
import pandas as pd
from boto.mturk.layoutparam import LayoutParameter
from boto.mturk.layoutparam import LayoutParameters
# Tells Python where to find the MTurkConnection client in the boto library
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import HTMLQuestion
import pickle
# Create your connection to MTurk

###############################################
#Test Functions
class Amt():
	ACCESS_ID = 'AKIAJUT7UAPF2JZYLK6A'
	SECRET_KEY = 'kvOcmRfpUmrRTvDykwOxLjec/cp4Y24/0qJtW+Am'
	sandbox_HOST = 'mechanicalturk.sandbox.amazonaws.com'
	real_HOST = 'mechanicalturk.amazonaws.com'
	real_ID = ['33KTOXRB2LW4PI5DBFZPH8KMJK5FRN','34FHTOY99EQJL9R5QQSQRPJZ03RASC']
	sandbox_ID = ['3MVRTDU8OEPFKV7FE8HQFIS83UU5FC','38X1F3X9FX9JBPRXU0O22B4V1CUY5X']
	mtc = MTurkConnection(aws_access_key_id = ACCESS_ID, aws_secret_access_key = SECRET_KEY, host = sandbox_HOST)
	
	
	def __init__(self, flag):
		if flag:
			self.hit_type = self.sandbox_ID[0]
			self.hit_layout = self.sandbox_ID[1]
		else:
			self.hit_type = self.real_ID[0]
			self.hit_layout = self.real_ID[1]

	def _GET_Balance(self):
		mtc = self.mtc
		account_balance = mtc.get_account_balance()[0]
		print ("You have a balance of: {}".format(account_balance))
		return account_balance

	################################################################################
	# Create a single Hits of type City
	# Note that we fix the attributes of all the properties, so each type has its own HIT template
	# Parameters: {Fifth,First,Forth,Second,Third,attribute,type}
	# return{'hit_type_id':hit_type_id,'hit_id':hit_id}
	def _Create_City_Hit(self, ins_lis, contrylist ,attribtueName):
		mtc = self.mtc
		# These parameters define the HIT that will be created
		# question is what we defined above
		# max_assignments is the # of unique Workers you're requesting
		# title, description, and keywords help Workers find your HIT
		# duration is the # of seconds Workers have to complete your HIT
		# reward is what Workers will be paid when you approve their work
		# Check out the documentation on CreateHIT for more details
		#instance_value = LayoutParameter('instance',instanceName)
		attribute_value = LayoutParameter('attribute',attribtueName)
		first_ins = LayoutParameter('First', ins_lis[0])
		second_ins = LayoutParameter('Second', ins_lis[1])
		third_ins = LayoutParameter('Third', ins_lis[2])
		forth_ins = LayoutParameter('Forth', ins_lis[3])
		fifth_ins = LayoutParameter('Fifth', ins_lis[4])
		countryFirst = LayoutParameter('countryFirst', contrylist[0])
		countrySecond = LayoutParameter('countrySecond', contrylist[1])
		countryThird = LayoutParameter('countryThird', contrylist[2])
		countryForth = LayoutParameter('countryForth', contrylist[3])
		countryFifth = LayoutParameter('countryFifth', contrylist[4])
		
		type_value = LayoutParameter('type', 'City')
		params = LayoutParameters([fifth_ins,first_ins,forth_ins,second_ins,third_ins,attribute_value,type_value,countryFirst,countrySecond,countryThird,countryForth,countryFifth])
		response = mtc.create_hit(hit_type=self.hit_type,
								  hit_layout=self.hit_layout,
								  layout_params = params,
								  max_assignments = 3,
								  )
		# The response included several fields that will be helpful later
		hit_type_id = response[0].HITTypeId
		hit_id = response[0].HITId

		myfile =  open ("HIT_Info1.txt","a")
		myfile.write("{0}\n{1}\n{2}\n".format("Your HIT has been created. You can see it at this link:","https://workersandbox.mturk.com/mturk/preview?groupId={}".format(hit_type_id),
		"Your HIT ID is: {}".format(hit_id)))
		myfile.close();
		print ("Your HIT has been created. You can see it at this link:")
		print ("https://workersandbox.mturk.com/mturk/preview?groupId={}".format(hit_type_id))
		print ("Your HIT ID is: {}".format(hit_id))
		return{'hit_id':hit_id}

	# return Yes|No count dic
	# return attributeName dic
	#[yes_no_dic, attribute_dic]
	def _Retrive_HIT_Answer (self, hit_id):
		mtc = self.mtc
		# This is the value you reeceived when you created the HIT
		# You can also retrieve HIT IDs by calling GetReviewableHITs
		# and SearchHITs. See the links to read more about these APIs.
		#result = mtc.get_assignments("3R5LWXWHR09AANE1160M46QDXFVXGA")
		print("Retrive Answer for id:{0}".format(hit_id))

		result = mtc.get_assignments(hit_id)
		#print("result:{0}".format(result.NumResults))
		# result is a list of assignments

		# check the attributes of the assignments
		# AcceptTime, Assignment, AssignmentId, AssignmentStatus, AutoApprovalTime, HITId, SubmitTime, WorkerId, answers
		# result === xml <Assignment>

		ins_result = []
		attribute_result = []

		for assignment in result:
			assignmentid = assignment.AssignmentId
			worker_id = assignment.WorkerId
			# answers is a list of QuestionFormAnswer object
			answerlist = assignment.answers
			
			for answer in answerlist[0]:
				# check the attributes of answer
				#print("qid:{0}; value:{1}".format(answer.qid,answer.fields[0]))
				
				#if answer.qid == 'answer':
				#	worker_answer = answer.fields[0]
					# answer.field is a list, for this task, it has only one element
					#return worker_answer

				if answer.qid == 'Instance':
					iList = answer.fields[0].split('|')
					for ins in iList:
						ins_result.append(ins)
					

				if answer.qid == 'Attribute':
					aList = answer.fields[0].split('|')
					for attr in aList:
						attribute_result.append(attr)

	       
	  			#if answer.qid == 'answer':
	  			#	worker_answer = answer.fields[0]
	  			#	print ("The Worker with ID {} submitted assignment {} \
	  			#		and gave the answer {}".format(worker_id, assignmentid, worker_answer))
	  				#return worker_answer
		return dict(collections.Counter(ins_result)),dict(collections.Counter(attribute_result))
		 

	# retrive all reviewable HITs, return is a list of HITId
	def _Search_HIT(self):
		mtc = self.mtc
		hits = mtc.get_all_hits()
		hits_id = []
		for hit in hits :
			hits_id.append(hit.HITId)
		return hits_id

	# HIT attribtues
	# HITStatus, HITTypeId, Keywords, MaxAssignments, NumberofAssignmentsCompleted, Title, Reward Description

	# get all HITs by filter keywords, our subjective KB HIT keywords could filter by 'knowledge'
	# return a list of HITId
	def _Get_Hits_Keyword (self, filter):
		mtc = self.mtc
		hits_list = mtc.get_all_hits()
		answer = []
		for hit in hits_list:
			if hasattr(hit,'Keywords') and hit.HITStatus != "Expired":
				key_word = hit.Keywords
				if key_word.find(filter) == -1:
					continue
				answer.append(hit.HITId)
		return answer


def read_data():
	selected_list = ['id','name','country']
	df = pd.read_csv('city.csv')[selected_list]
	print df.info()
	return df




# CREATE_HIT_FLAG = True
if __name__ == '__main__':
	sandboxFlag = True
	CREATE_HIT_FLAG = False
	NUM_OF_INIT_HITS = 4
	START_INDEX = 0

	#test method create a Hit of bit city
	df = read_data()
	label = [None]* len(df['name'])
	city2id = dict(zip(df['name'], range(len(df['name']))))
	cityamt = Amt(sandboxFlag)
	if CREATE_HIT_FLAG:
		# for hit in mtc.get_all_hits():
		# 	mtc.disable_hit(hit.HITId)
		if sandboxFlag:
			f = open('sand_hit_ids','a')
		else:
			f = open('hit_ids','a')
		hit_ids = []
		for i in range(START_INDEX,START_INDEX+NUM_OF_INIT_HITS*5,5):
			namel =  list(df['name'][i:i+5])
			countryl =  list(df['country'][i:i+5])
			hit_id = cityamt._Create_City_Hit(namel,countryl,'big')
			hit_ids.append(hit_id['hit_id'])
			f.write(hit_id['hit_id']+'\n')  # python will convert \n to os.linesep
		f.close()
	else:
		if sandboxFlag:
			f = open('sand_hit_ids','r')
		else:
			f = open('hit_ids','r')
		hit_ids = []
		for line in f:
			hit_ids.append(line.strip())

	print hit_ids


	# get answer
	for i in range(START_INDEX,START_INDEX+NUM_OF_INIT_HITS*5,1):
		label[i] = 0
	for hit_id in hit_ids:
		[ins_result, attribute_result] = cityamt._Retrive_HIT_Answer(hit_id)
		for yn in ins_result:
			if ins_result[yn]>0:
				label[city2id[yn]] = 1
			else:
				label[city2id[yn]] = 0
			print city2id[yn],label[city2id[yn]]
			print("Answer:{0},Count:{1}".format(yn,ins_result[yn]))
		for ar in attribute_result:
			print("Attribtue:{0},Count:{1}".format(ar,attribute_result[ar]))
	print label[START_INDEX:START_INDEX+NUM_OF_INIT_HITS*5]
	print label
	with open('label','w') as f:
	    pickle.dump(label,f)
	with open('label','rb') as f:
	    label1 = pickle.load(f)
	# print label1
