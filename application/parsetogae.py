from parse_rest.connection import register
from parse_rest.datatypes import Object
from google.appengine.ext import ndb
from application import models as db

register('arVFof1gZO9kqxJl5GboE5UEb93JQ0Fmc9lifegC', 'chl6mb6OxgcAyhcCPEQtaQgYfCjveNxP2x0fDUYs')

class Story(Object):
	pass

class UserRatings(Object):
	pass

def clearDataStore(kind):
	q = ndb.Query(kind=kind)
	stories = q.fetch(keys_only=True)
	ndb.delete_multi(stories)

	
			
def importStories(r, limit=400, skip=0, overwrite=False):

	storyList = Story.Query.all().order_by('title').limit(limit).skip(skip)
	storyCount = 0
	wordCount = 0
	r.out.write('got stories from parse, overwrite='+str(overwrite)+'<br/>')
	targetList = []
	for s in storyList:
		storyCount += 1
		r.out.write(str(storyCount) +'. ')
		story = processStory(s, r, overwrite)
		if story:
			targetList.append(story)
			wordCount += story.wordCount
	
	if(storyCount>0):
		source = db.StorySource(
			title = 'Nature',
			storyCount = storyCount,
			wordCount = wordCount
		)
		targetList.append(source)
		ndb.put_multi(targetList)
	
	r.out.write('end of importStories<br/>')

def processStory(s, r, overwrite):
	r.out.write(s.title +'...')
	
	q = db.Story.query(db.Story.creator == s.author, db.Story.title == s.title)
	storyInStore = q.get()
	
	if storyInStore:
		if overwrite:
			r.out.write('story exists, overwriting...')
			story = storyInStore
		else:
			r.out.write('story exists...story skipped <br/>')
			return None
	else:
		story = db.Story()

	p = db.FirstPub(
		date = s.publicationDate,
		url = s.url,
		doi = s.doi,
		publication = 'Nature',
		section = 'Futures',
		issue = s.issue,
		volume = s.volume,
		publisher = 'Nature Publishing Group'
	)
	if hasattr(s, 'pageViews'):
		p.pageViews = s.pageViews
	if hasattr(s, 'facebook'):
		p.fbShares = s.facebook
	if hasattr(s, 'twitter'):
		p.tweets = s.twitter
	if hasattr(s, 'altmetricScore'):
		p.altScore = s.altmetricScore		
	if hasattr(s, 'altmetricContext'):
		p.altInfo = s.altmetricContext
	
	story.category = 'fiction'
	story.genre = 'sci-fi'
	story.language = 'english'
	story.title=s.title 
	story.subtitle=s.subtitle
	story.creator = [s.author]
	story.text = s.storyText.replace('<p>JACEY</p>','')
	story.wordCount = s.wordCount
	story.firstPub = p
	r.out.write('processed<br/>')
	return story
	

def importStream(userId, r, limit=400, skip=0, overwrite=False):
	print "importing stream"

	q = db.User.query(db.User.gId == userId)
	userKey = q.fetch(keys_only=True)[0]
	if not userKey:
		r.out.write('failed to get user! Exiting without importing stream')
		return

	stream = UserRatings.Query.all().limit(limit).skip(skip)
	i = 0
	importList = []
	for s in stream:
		i += 1
		node = processStream(userKey, s, r)
		if node:
			importList.append(node)
		print str(i) + ". stream entry processed"
	if i>0:
		ndb.put_multi(importList)
	r.out.write('end of importStream<br/>')
	
def processStream(userKey, stream, r):
	#Get the same story in the data store
	q = db.Story.query(db.Story.creator == stream.story.author, 
		db.Story.title == stream.story.title)
	story = q.get()
	if not story:
		return None
	n = db.StreamNode(
		parent=userKey,
		storyKey = story.key,
		completed = True,
		createdAt = stream.createdAt,
		timeSpent = 0,
		position = 0,
		rating = int(stream.rating)
	)
	return n
	
	
	
	
	