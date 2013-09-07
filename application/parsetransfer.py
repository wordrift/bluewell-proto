import config
from parse_rest.connection import register
from parse_rest.datatypes import Object
import dbORM as db

register(config.APPLICATION_ID, config.REST_API_KEY)

class Story(Object):
	pass

class UserRatings(Object):
	pass

def rebuildDB():
	db.Base.metadata.drop_all(db.engine)
	db.Base.metadata.create_all(db.engine)
	print 'database rebuilt'

		
def setupDefaults():
	db.session.add_all([
		db.Publication('Nature Magazine', 'Nature Publishing Group', 'permissions@nature.com'),
		db.User('biren','biren@birenshah.com','passwd12','g3MVPfPu5u'),
		db.Creator('Biren Shah','biren@birenshah.com'),
		db.Enum('english','languages')
	])
	
	db.session.commit()
	
def importStories():
	storyList = Story.Query.all().order_by('title').limit(400)
	
	i = 0
	for s in storyList:
		i += 1
		transferStory(s)
		print str(i) + ". " + s.title + "...transferred"


def transferStory(s):

	#for x in db.session.query(db.Story).filter(db.Story.parseId == s.objectId):
		#db.session.delete(x)
		#db.session.commit()

	creatorId = 0
	for c in db.session.query(db.Creator).filter(db.Creator.name == s.author):
		creatorId = c.id

	if creatorId == 0:
		creatorId = 0
		# insert new creator here
		creator = db.Creator(s.author, None)
		db.session.add(creator)
		db.session.commit()
		creatorId = creator.id
		
	storyText = s.storyText.replace('<p>JACEY</p>','')
	publicationId = 1
		
	ns = db.Story(s.title, s.subtitle, creatorId, None, 'languages-english', 
		storyText, publicationId, s.publicationDate, s.objectId)
	db.session.add(ns)
	db.session.commit()
	
	pageViews = None
	fbShares = None
	tweets = None
	altmetricScore = None
	altmetricContext = None
	
	if hasattr(s, 'pageViews'):
		pageViews = s.pageViews
	if hasattr(s, 'facebook'):
		fbShares = s.facebook
	if hasattr(s, 'twitter'):
		tweets = s.twitter
	if hasattr(s, 'altmetricScore'):
		altmetricScore = s.altmetricScore		
	if hasattr(s, 'altmetricContext'):
		altmetricContext = s.altmetricContext
	
	details = db.PubDetails(ns.id, s.url, s.section, s.issue, s.volume, s.doi, 
		pageViews, fbShares, tweets, altmetricScore, altmetricContext)
	db.session.add(details)
	db.session.commit()

def importStream():
	print "importing stream"
	stream = UserRatings.Query.all().limit(400)
	
	i = 0
	for s in stream:
		i += 1
		transferStream(s)
		print str(i) + ". stream entry transferred"
	
def transferStream(stream):
	
	for u in db.session.query(db.User).filter(db.User.parseId == stream.user.objectId):
		userId = u.id
	
	for s in db.session.query(db.Story).filter(db.Story.parseId == stream.story.objectId):
		storyId = s.id
	
	ns = db.Stream(userId, storyId)
	ns.createdAt = stream.createdAt
	ns.updatedAt = stream.updatedAt
	ns.rating = stream.rating
	
	db.session.add(ns)
	db.session.commit()

	

		