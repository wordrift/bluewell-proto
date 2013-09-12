import datetime
from google.appengine.ext import ndb

#Intended to be used in Story class
class FirstPub(ndb.Model):
	date = ndb.DateProperty()	
	url = ndb.StringProperty(indexed=False)	
	doi = ndb.StringProperty(indexed=False)
	publication = ndb.StringProperty(required=True)
	section = ndb.StringProperty()
	issue = ndb.StringProperty()
	volume = ndb.StringProperty()
	publisher = ndb.StringProperty()
	pageViews = ndb.IntegerProperty()
	comments = ndb.IntegerProperty()	
	facebook = ndb.IntegerProperty()
	twitter = ndb.IntegerProperty()
	altScore = ndb.IntegerProperty()
	altInfo = ndb.TextProperty()

class Story(ndb.Model):
	category = ndb.StringProperty(required=True)
	genre = ndb.StringProperty(required=True)
	language = ndb.StringProperty(default='english', required=True)
	title = ndb.StringProperty(required=True)
	subtitle = ndb.StringProperty()
	creator = ndb.StringProperty(repeated=True)
	creatorInfo = ndb.TextProperty()
	text = ndb.TextProperty(required=True, default='')
	wordCount = ndb.IntegerProperty()
	firstPub = ndb.StructuredProperty(FirstPub)
	ratings = ndb.IntegerProperty(default=0, required=True)
	ratingPoints = ndb.IntegerProperty(default=0, required=True)
	score = ndb.IntegerProperty(default=0, required=True)
	rightsOwned = ndb.StringProperty()

class StorySource(ndb.Model):
	title = ndb.StringProperty(required=True)
	storyCount = ndb.IntegerProperty(required=True, default=0)
	wordCount = ndb.IntegerProperty(required=True, default=0)
	listUrl = ndb.StringProperty()
	exclusions = ndb.StringProperty(repeated=True)

class User(ndb.Model):
	email = ndb.StringProperty(required=True)
	userId = ndb.StringProperty()
	gId = ndb.StringProperty()
	createdAt = ndb.DateTimeProperty(auto_now_add=True)

#Intended to be a child of User
class StreamNode(ndb.Model):
	title = ndb.StringProperty()
	storyKey = ndb.KeyProperty(required=True, kind='Story')
	createdAt = ndb.DateTimeProperty(auto_now_add=True)
	updatedAt = ndb.DateTimeProperty(auto_now=True)
	timeSpent = ndb.IntegerProperty(required=True, default=0,indexed=False)
	position = ndb.IntegerProperty(default=0, required=True, indexed=False)
	completed = ndb.BooleanProperty(required=False)
	favorite = ndb.BooleanProperty(required=False)
	rating = ndb.IntegerProperty(required=False)	

class Rec(ndb.Model):
	storyKey = ndb.KeyProperty(required=True, kind='Story')
	title = ndb.StringProperty()
	order = ndb.IntegerProperty(required=True)
  
