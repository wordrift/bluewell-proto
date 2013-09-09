from google.appengine.ext import ndb
from application import models as m
import common
import logging
from dateutil import parser
from collections import defaultdict
import requests
import re
from bs4 import BeautifulSoup
import html5lib

request = None
response = None

def setup(req, res):
	global request
	global response
	request = req
	response = res

def setupSources():
	sources = [
		{
			'title':'Nature',
			'listUrl':'http://www.nature.com/nature/focus/arts/futures/',
			'exclusions':[]		
		},
		{
			'title': 'AE - The Canadian Science Fiction Review',
			'listUrl':'http://aescifi.ca/index.php/fiction',
			'exclusions': ['AE Micro 2013', 'The Experiment']
		}
	]
	
	updateList = []
	for s in sources:
		q = m.StorySource.query(m.StorySource.title == s['title'])
		existingSource = q.get()
		
		if not existingSource:
			source = m.StorySource()
		else:
			source = existingSource
			
		source.populate(
			title = s['title']
			, listUrl = s['listUrl']
			, exclusions = s['exclusions']
			, storyCount = 0
			, wordCount = 0
		)
		updateList.append(source)
		logging.info('creating source: {0}'.format(s['title']))

	if len(updateList) > 0:
		ndb.put_multi(updateList)	

def getSources():
	q = m.StorySource.query()
	sources = q.fetch()
	return sources

def sourceRecount():
	sourceQ = m.StorySource.query()
	updateList = []
	for source in sourceQ.fetch():
		wordCount = 0
		storyCount = 0
		q = m.Story.query(m.Story.firstPub.publication == source.title)
		for s in q.fetch():
			if s.title not in source.exclusions:
				storyCount +=1
				wordCount += s.wordCount
		source.storyCount = storyCount
		source.wordCount = wordCount
		updateList.append(source)
	ndb.put_multi(updateList)
		
def clearDataStore(kind):
	q = ndb.Query(kind=kind)
	stories = q.fetch(keys_only=True)
	ndb.delete_multi(stories)

def _getStoryProperty(p):
	negate = False
	if p[0] == '-':
		negate = True
		p = p[1:]
		
	if p == 'publication' or p == 'publicationDate':
		prop = getattr(m.Story.firstPub, p)
	else:
		prop = getattr(m.Story, p)
	
	if negate:	
		return -prop
	else:
		return prop

def _filterMap(f):
	if f == 'ae':
		return 'AE - The Canadian Science Fiction Review'
	else:
		return f

def getStories(filters, order, pageSize, offset):
	q = m.Story.query()
	
	logging.info('adminmodel getStories. Filters: {0}'.format(filters))
	logging.info('adminmodel getStories. order: {0}'.format(order))
	
	if filters:
		for key in filters:
			filterValue = _filterMap(filters[key])
			q = q.filter(_getStoryProperty(key) == filterValue)
	
	if order:
		for key in order:	
			q = q.order(_getStoryProperty(key))
	
	return q.fetch(pageSize, offset = pageSize*offset)
	
#define the key mapping
def futures_name_map(old_name):
	m = defaultdict(lambda:False)
	m['DC.title']='title'
	m['dc.title']='title'
	m['DC.creator']='author'
	m['dc.creator']='author'
	m['description']='subtitle'
	m['DC.language']='language'
	m['dc.language']='language'
	m['DC.identifier']='doi'
	m['dc.identifier']='doi'
	m['prism.publicationDate']='publicationDate'
	m['prism.volume']='volume'
	m['prism.issue']='issue'
	m['prism.number']='issue'
	m['prism.section']='section'
	m['prism.publicationName']='publication'
	m['citation_publisher']='publisher'
	m['prism.issn']='issn'
	m['prims.eIssn']='eIssn'
	m['prism.rightsAgent']='publicationRightsAgent'
	return m[old_name]

def clearDataStore(kind, publication):
	q = ndb.Query(kind=kind)
	q = q.filter(m.Story.firstPub.publication == publication)
	stories = q.fetch(keys_only=True)
	ndb.delete_multi(stories)

def importStories(sourceKey, limit=None, offset=0, reimport=False):

	source = ndb.Key(urlsafe=sourceKey).get()
	response.out.write("Starting import stories, source: {0}, limit: {1}, offset: {2}, reimport: {3} <br/>".format(source.title, limit, offset, reimport))
	if reimport:
		storyList = _getExistingStories(source, limit, offset)
	else:
		storyList = _getStoriesFromWeb(source, limit, offset)
	response.out.write('Got list of story urls. Stories: {0}<br/>'.format(len(storyList)))
	updateList = []
	storyCount = 0
	for s in storyList:
		if limit == None or storyCount < limit:
			storyEntity = _importStory(s['url'], source, reimport)
			
			if storyEntity:
				storyCount +=1
				updateList.append(storyEntity)
				response.out.write('Got a story to update: {0}<br/>'.format(encodeString(storyEntity.title)))
				if reimport:
					source.wordCount = source.wordCount - s['wordCount'] + storyEntity.wordCount
				else:
					source.storyCount += 1
					source.wordCount += storyEntity.wordCount
			else:
				response.out.write('No story entity returned <br/>')
		else:
			response.out.write('storyCount {0} greater than limit {1}<br/>'.format(storyCount, limit))

	if len(updateList) > 0:
		updateList.append(source)
		ndb.put_multi(updateList)
	response.out.write('Story import complete. Updated {0} stories.<br/>Source: {1}<br/>'.format(storyCount, source))
	response.out.write('<a href="/admin">Return to Admin Home</a>')

def reimportStory(urlSafeStoryKey):
	storyKey = ndb.Key(urlsafe=urlSafeStoryKey)
	story = storyKey.get()
	q = m.StorySources.query(m.StorySource.title == story.firstPub.publication)
	source = q.get()
	_importStory(source, story)

def _getExistingStories(source, limit, offset):
	q = m.Story.query(m.Story.firstPub.publication == source.title)
	q = q.order(m.Story.title)
	stories = q.fetch(limit, offset=offset)
	storyList = []
	for s in stories:
		storyList.append({'url':s.firstPub.url, 'wordCount':s.wordCount})
	return storyList

def _getStoriesFromWeb(source, limit, offset):
	if source.title == 'AE - The Canadian Science Fiction Review':
		return _getStoryListAE(source.listUrl, limit, offset)
	

def _importStory(url, source, overwrite):
	if source.title == 'AE - The Canadian Science Fiction Review':
		return _importStoryFromAE(url, source, overwrite)

def _getStoryListAE(url, limit, pageOffset=0):
	#Get links to all the stories we're going to import
	pageSize = 9
	stories = None
	urlBase = 'http://aescifi.ca'
	storyList = []
	for i in range(pageOffset,8):
		n = i * pageSize
		r = requests.get("http://aescifi.ca/index.php/fiction?start="+str(n))
		indexSoup = BeautifulSoup(r.text)		
		stories = indexSoup.find_all('a',class_='contentpagetitle')
		if stories:
			for s in stories:
				storyList.append({'url':urlBase+str(s['href'])})
	return storyList

def encodeString(string):
	#return string
	return unicode(string).encode('utf-8', 'xmlcharrefreplace')
				
def _importStoryFromAE(url, source, overwrite=False):
	response.out.write('trying to get story from: {0}<br/>'.format(url))

	r1 = requests.get(url)
	r1.encoding = 'UTF-8'
	soup = BeautifulSoup(r1.text, "html5lib")

	s = None
	title = soup.find('title').get_text().strip()
	if title in source.exclusions:
		response.out.write('Story: {0} is in exclusions list, skipping<br/>'.format(encodeString(title)))
	else:
		creator = [soup.find("span",class_="author").get_text().strip()]
	
		response.out.write('importing story, title: {0}<br/>'.format(encodeString(title)))
	
		q = m.Story.query().filter(m.Story.title == title, m.Story.firstPub.publication == source.title)
		existingStory = q.get()
		
		if not existingStory:
			s = m.Story()
		elif overwrite:
			s = existingStory
	
		if s:
			storyRoot = soup.find('td', class_='mainarticle')
			story = storyRoot.extract()
			
			for i in story('img'):
				i.decompose()
				
			for t in story.find_all():
				text = t.renderContents()
				if 'illustration by' in text:
					t.decompose()
			
			creatorInfo = ''
			hr = story.find('hr')			
			if hr:
				creatorInfoTag = hr.find_next('p')
				if not creatorInfoTag:
					creatorInfoTag = hr.find_next('i')
				if creatorInfoTag:
					creatorInfo = creatorInfoTag.get_text()
					creatorInfoTag.decompose()
				hr.decompose()	
			
			#response.out.write('got creatorInfo {0}'.format(unicode(creatorInfo)))
				
			storyText = unicode(story)
			wordCount = len(storyText.split(None))	
			
			firstPub = m.FirstPub (
				 url = url
				, publication = source.title
				, comments = 0
			)
			s.populate(
				category = 'fiction'
				, genre = 'sci-fi'
				, language = 'english'
				, title = title
				, creator = creator
				, creatorInfo = creatorInfo
				, text = storyText
				, wordCount = wordCount			
				, firstPub = firstPub
			)
		else:
			response.out.write('skipping story, already exists: {0} - {1} <br/>'.format(title, source.title))
	return s	

	

	
	
		
	

	
	
	
	
	
	
	
	
	
	
