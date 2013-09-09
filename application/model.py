from google.appengine.ext import ndb
from application import models as m
import common
import logging
from dateutil import parser

category = None
genre = None
language = None
user = None

def setStream(u, cat, g, lang):
	global user
	global category
	global genre
	global language
	
	user = u
	category = cat
	genre = g
	language = lang

def getUser(userId, source):
	u = None
	if source == 'url':
		userKey = ndb.Key(urlsafe=userId)
		u = userKey.get()
	elif source == 'google':
		q = m.User.query(m.User.gId == userId)
		u = q.get()	
		
	if u:
		return u
	else:
		return False

def createUser(userId, email, source):
	if source == 'google':
		user = m.User(gId=userId, email=email)
	userKey = user.put()
	u = userKey.get()
	setStream(u, 'fiction', 'sci-fi','english')
	buildRecommendations(0, 100, 0, False)
	#Setup the first story in the user's stream
	logging.info('setting first story in Stream for user') 
	stories = getStories(None,False, 0,1,False) 
	s = stories[0]
	updateStream([{
		'userKey':u.key,
		'storyKey': s['key'],
		'title':s['title']
	}])
	return u

def moveGID():
	q = m.User.query()
	for u in q.fetch():
		u.gId = u.userId
		del u._properties['userId']
		u.put()
		
def getCurrentStory(lastOrFurthest='last'):
	logging.info('getting current story')
	snQ = m.StreamNode.query(ancestor=user.key)
	if lastOrFurthest == 'last':
		snQ = snQ.order(-m.StreamNode.updatedAt)
	else:
		snQ = snQ.order(-m.StreamNode.createdAt)
	streamNode = snQ.get()
	story = None
	if streamNode:
		story = streamNode.storyKey.get()
		logging.info('got {0} story from stream: {1}'.format(lastOrFurthest, story.title))
	else:
		logging.info('no stories in stream, no current story found')
	return story

def buildSN(user, story):
	sn = m.StreamNode(
		parent = user.key,
		storyKey = story.key)
	return sn
	
def getAnchor(anchorId, source):
	if source == 'url':
		key = ndb.Key(urlsafe=anchorId)
		anchor = key.get()
	return anchor

def updateStream(stream):
	snList = []
	recList = []
	for p in stream:
		logging.info(p);
		if 'storyKey' in p:
			storyKey = ndb.Key(urlsafe=p['storyKey'])
			q = m.StreamNode.query(ancestor=user.key).filter(m.StreamNode.storyKey == storyKey)
			sn = q.get()			

			#If none found, create a new StreamNode 
			#and remove this story from the recommendation list
			if sn is None:
				logging.info('no sn for the story: {0}, trying to create '.format(storyKey.get().title))
				sn = m.StreamNode(
					parent = user.key, 
					storyKey = storyKey,
					title = storyKey.get().title
				)
				if 'createdAt' in p:
					sn.createdAt = p['createdAt']
				
				recQ = m.Rec.query(ancestor=user.key).filter(m.Rec.storyKey == storyKey)
				r = recQ.get()
				if r:
					logging.info('story appears in recommendations, removing /');		
					recList.append(r.key)
				else:
					logging.info('story does not appear in recommendations /');		
			else:
				logging.info('got the sn for that story /');									
			#Otherwise, just update the existing one
			vp = validateStreamNodeParams(p)
			for prop in vp:
				setattr(sn, prop, vp[prop])
			snList.append(sn)
		else:
			logging.info('no storyKey found in story /');	
	snLen = len(snList)
	rLen = len(recList)
	ndb.put_multi(snList)
	ndb.delete_multi(recList)			
	return [snLen, rLen]
				
def validateStreamNodeParams(p):
	vp = {}
	#Make sure this set of params are valid
	for prop in m.StreamNode._properties:
		logging.info('validating propery: {0}'.format(prop))
		if prop in p:
			if prop == 'storyKey' or prop == 'createdAt':
				pass
			elif prop == 'updatedAt':
				vp['updatedAt'] = parser.parse(p[prop])
			else:
				#TODO add checks on the specific properties
				value = p[prop]
				logging.info('validated streamNode param {0} as {1}'.format(prop, value))
				vp[prop] =  value
	return vp	
			
	
def getStories(anchor, includeAnchor=True, numPrevious=0, numAfter=1, fullText=True):
	from collections import deque
	storyList = deque()
	iAfter = 0
	anchorSN = None
	
	#If not anchor is passed in, then try to get the user's current story as anchor
	if not anchor:
		logging.info('no anchor, getting current story')
		anchor = getCurrentStory()
		#The user may not have had a current story (if it was their first login)
	
	if anchor:
		anchorSN = getSNFromStory(anchor)
	if includeAnchor and anchor:
		logging.info('includeing anchor in current results')
		anchorD = storyToDict(anchor, anchorSN, fullText)
		storyList.append(anchorD)

	#First check if the anchor is in the user's stream
	if anchorSN:
		#If so, get the stories before it
		if numPrevious > 0:	
			logging.info('trying to get previous stories')
			snQ = m.StreamNode.query(ancestor=user.key).filter(m.StreamNode.createdAt < anchorSN.createdAt).order(-m.StreamNode.createdAt)
			for sn in snQ.fetch(numPrevious):
				story = sn.storyKey.get()
				storyDict = storyToDict(story, sn, fullText)
				storyList.appendleft(storyDict)
			
		#Then get the stories after it
		if numAfter > 0:
			logging.info('trying to get stories after anchor from stream')
			snQ = m.StreamNode.query(ancestor=user.key).filter(m.StreamNode.createdAt > anchorSN.createdAt).order(m.StreamNode.createdAt)
			for sn in snQ.fetch(numAfter):
				story = sn.storyKey.get()
				storyDict = storyToDict(story, sn, fullText)
				storyList.append(storyDict)
				iAfter += 1
			
	#Finally, get more stories from the recommendation list, until we reach the requested total
	if numAfter - iAfter > 0:
		logging.info('getting recommendations to fill out results')
		recs = getRecommendations(numAfter - iAfter)
		for r in recs:
			story = r.storyKey.get()
			storyDict = storyToDict(story, None, fullText)
			storyList.append(storyDict)
			logging.info('got a recommendation: {0}'.format(story.title))

	return list(storyList)

def getRecommendations(numTarget):
	storyList = []
	numResults = 0
	q = m.Rec.query(ancestor=user.key)
	q = addStreamFilters(q)
	q = q.order(m.Rec.order)
	for s in q.fetch(numTarget):
		storyList.append(s)
		numResults += 1
				
	''' TODO: Build More Recommendations, if I run out	'''	
	return storyList


def buildRecommendations(numComplete, numTarget=100, offset=0, clearExisting=False):
	if clearExisting:
		clearRecommendations()
	
	#Get the list of stories, in order		
	q = m.Story.query()
	q = q.order(-m.Story.firstPub.altScore).order(m.Story.firstPub.date)
	q = addStreamFilters(q)

	
	numResults = 0;
	recList = []
	for s in q.fetch(numTarget, offset=offset):
		numResults +=1
		snQ = m.StreamNode.query(ancestor=user.key).filter(m.StreamNode.storyKey == s.key)
		if not clearExisting:
			recQ = m.Rec.query(ancestor=user.key).filter(m.Rec.storyKey == s.key)
			existingRec = recQ.get()
		else:
			existingRec = False
			
		if not snQ.get() and not existingRec:
			recList.append(buildRec(s, numComplete))
			numComplete +=1		
		if numComplete == numTarget:
			break
	
	#Save the recommendations to the datastore		
	ndb.put_multi(recList)		
	
	#Keep going if we didn't get enough recommendations 
	#and the last query returned as many results as asked for
	if numComplete < numTarget and numResults == numTarget:
		numComplete = buildRecommendations(numComplete, numTarget, offset+numTarget, False, response)
	return numComplete
	
def buildRec(story, order):
	rec = m.Rec(
		parent = user.key
		, storyKey = story.key
		, title = story.title
#		, category = story.category
#		, genre = story.genre
#		, language = story.language
		, order = order
	)
	return rec

def clearRecommendations():
	recQ = m.Rec.query(ancestor=user.key)
	recQ = addStreamFilters(recQ)
	recs = recQ.fetch(keys_only=True)
	ndb.delete_multi(recs)
	return True

def addStreamFilters(q):
	return q
	#return q.filter(m.Story.category == category).filter(m.Story.genre == genre).filter(m.Story.language == language)

def storyListToJson(storyList, fullText):
	import json
	output = []
	if not fullText:
		for s in storyList:
			story = {'id':s.key.urlsafe(),'title':s.title, 'creator':s.creator}
			output.append(story)
	else:
		for s in storyList:
			n = toDict(s)
			n['id'] = s.key.urlsafe()
			output.append(n)
	return json.dumps(output)	

def getSNFromStory(s):
	q = m.StreamNode.query(ancestor=user.key).filter(m.StreamNode.storyKey == s.key)
	return q.get()


def toDict(obj):
	output = {}
	for p in obj._properties:
		if hasattr(obj, p):
			output[p] = unicode(getattr(obj, p)).encode('ascii', 'xmlcharrefreplace')
	return output
	
def storyToDict(self, sn=None, fullText=True):
	output = {}
	output['key'] = self.key.urlsafe()
	for p in self._properties:
		if hasattr(self,p):
			if p == 'firstPub':
				output[p] = toDict(getattr(self,p))
			elif p == 'creator':
				output[p] = unicode(getattr(self, p)[0]).encode('ascii', 'xmlcharrefreplace')
			else:	
				output[p] = unicode(getattr(self, p)).encode('ascii', 'xmlcharrefreplace')
	if sn:
		output['userHistory'] = toDict(sn)
	if not fullText:
		output.pop('text',None)
	return output

def clearDataStore(kind):
	q = ndb.Query(kind=kind)
	stories = q.fetch(keys_only=True)
	ndb.delete_multi(stories)


	
		