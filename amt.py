# imports the Boto library so that it can be used
import boto
import collections
from boto.mturk.layoutparam import LayoutParameter
from boto.mturk.layoutparam import LayoutParameters
# Tells Python where to find the MTurkConnection client in the boto library
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import HTMLQuestion
# Create your connection to MTurk

###############################################
#Test Functions
def _GET_Balance( mtc):
	account_balance = mtc.get_account_balance()[0]
	print ("You have a balance of: {}".format(account_balance))
	return account_balance

# This is the example of the tutorial that create HIT from HTML input
def _Create_HIT (mtc):
	question_html_value = """
	<html>
	<head>
	<meta http-equiv='Content-Type' content='text/html; charset=UTF-8'/>
	<script src='https://s3.amazonaws.com/mturk-public/externalHIT_v1.js' type='text/javascript'></script>
	</head>
	<body>
	<!-- HTML to handle creating the HIT form -->
	<form name='mturk_form' method='post' id='mturk_form' action='https://workersandbox.mturk.com/mturk/externalSubmit'>
	<input type='hidden' value='' name='assignmentId' id='assignmentId'/>
	<!-- This is where you define your question(s) --> 
	<h1>Please name the company that created the Galaxy</h1>
	<p><textarea name='answer' rows=3 cols=80></textarea></p>
	
	<!-- HTML to handle submitting the HIT -->
	<p><input type='submit' id='submitButton' value='Submit' /></p></form>
	<script language='Javascript'>turkSetAssignmentID();</script>
	</body>
	</html>
	"""
	# The first parameter is the HTML content
	# The second is the height of the frame it will be shown in
	# Check out the documentation on HTMLQuestion for more details
	html_question = HTMLQuestion(question_html_value, 500)
	# These parameters define the HIT that will be created
	# question is what we defined above
	# max_assignments is the # of unique Workers you're requesting
	# title, description, and keywords help Workers find your HIT
	# duration is the # of seconds Workers have to complete your HIT
	# reward is what Workers will be paid when you approve their work
	# Check out the documentation on CreateHIT for more details
	response = mtc.create_hit(question=html_question,
                          max_assignments=1,
                          title="Answer a simple question",
                          description="Help research a topic",
                          keywords="question, answer, research",
                          duration=120,
                          reward=0.50)
	# The response included several fields that will be helpful later
	hit_type_id = response[0].HITTypeId
	hit_id = response[0].HITId

	myfile =  open ("HIT_Info1.txt","w")
	myfile.write("{0}\n{1}\n{2}\n".format("Your HIT has been created. You can see it at this link:","https://workersandbox.mturk.com/mturk/preview?groupId={}".format(hit_type_id),
	"Your HIT ID is: {}".format(hit_id)))
	myfile.close();
	print ("Your HIT has been created. You can see it at this link:")
	print ("https://workersandbox.mturk.com/mturk/preview?groupId={}".format(hit_type_id))
	print ("Your HIT ID is: {}".format(hit_id))
	return{'hit_type_id':hit_type_id,'hit_id':hit_id}

################################################################################
# Create a single Hits of type City
# Note that we fix the attributes of all the properties, so each type has its own HIT template
# Parameters: {Fifth,First,Forth,Second,Third,attribute,type}
# return{'hit_type_id':hit_type_id,'hit_id':hit_id}
def _Create_City_Hit(mtc, ins_lis, contrylist ,attribtueName):

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
	response = mtc.create_hit(hit_type='3Z53LF8QZE90JGGUTI4YTOYIVBFFCT',
							  hit_layout='3W3S1A7N3YDL5VIBRWHYJ4DPH2JZBP',
							  layout_params = params
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
def _Retrive_HIT_Answer (mtc, hit_id):
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
def _Search_HIT(mtc):
	hits = mtc.get_all_hits()
	hits_id = []
	for hit in hits :
		hits_id.append(hit.HITId)
	return hits_id

# HIT attribtues
# HITStatus, HITTypeId, Keywords, MaxAssignments, NumberofAssignmentsCompleted, Title, Reward Description

# get all HITs by filter keywords, our subjective KB HIT keywords could filter by 'knowledge'
# return a list of HITId
def _Get_Hits_Keyword (mtc, filter):
	hits_list = mtc.get_all_hits()
	answer = []
	for hit in hits_list:
		#cur_answer = _Retrive_HIT_Answer(mtc, hit_id)
		#answer_pair.setdefault(hit_id,cur_answer)
		if hasattr(hit,'Keywords') and hit.HITStatus != "Expired":
			key_word = hit.Keywords
			if key_word.find(filter) == -1:
				continue
			answer.append(hit.HITId)
			#print("cur hit:{0}, Description:{2}, status:{1}".format(hit.HITId, hit.HITStatus, hit.Keywords))
	return answer

# Approve an assignment 
# mtc.approve_assignment(assignment_id)
# mtc.dispose_hit(hit_id)





ACCESS_ID = 'AKIAJUT7UAPF2JZYLK6A'
SECRET_KEY = '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'
sandbox_HOST = 'mechanicalturk.sandbox.amazonaws.com'
real_HOST = 'mechanicalturk.amazonaws.com'

mtc = MTurkConnection(aws_access_key_id = ACCESS_ID, aws_secret_access_key = SECRET_KEY, host = sandbox_HOST)

#_GET_Balance(mtc)
#_Create_HIT(mtc)
#answer_pair = _Retrive_Answers(mtc)
#for hit_id in answer_pair:
#	print("HIT:{0}, answer is {1}".format(hit_id, answer_pair[hit_id]))
#_Retrive_HIT_Answer(mtc,"3R5LWXWHR09AANE1160M46QDXFVXGA")
#_Retrive_ReviewableHits(mtc)
#mtc.dispose_hit

#hitList = _Get_Hits_Keyword(mtc,"research")
#hit_answer = _Retrive_Answers(mtc, hitList)
#for key in hit_answer:
#	print("ID:{0}, Answer:{1}".format(key,hit_answer[key]))

#print(_Retrive_HIT_Answer(mtc,"3R5LWXWHR09AANE1160M46QDXFVXGA"))

#test method create a Hit of bit city
instList = ['New York','Beijing','London','Shanghai','Paris']
contrylist = ['1','2','3','4','5']
id1 = _Create_City_Hit(mtc,instList,contrylist,'big')
for i in range(0,len(instList),5):
	print i
# id2 = _Create_City_Hit(mtc,instList[1],'big')
# print id1
[ins_result, attribute_result] = _Retrive_HIT_Answer(mtc,'3V7ICJJAZAHNL4IG19636K2IO8GB4C')

for yn in ins_result:
	print("Answer:{0},Count:{1}".format(yn,ins_result[yn]))
for ar in attribute_result:
	print("Attribtue:{0},Count:{1}".format(ar,attribute_result[ar]))
