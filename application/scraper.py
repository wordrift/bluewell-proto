from google.appengine.ext import ndb
from collections import defaultdict
import requests
import re
from dateutil import parser
from bs4 import BeautifulSoup
import models as m
import html5lib
import logging

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

def _updateStorySource(title, storyCount, wordCount):
	q = m.StorySource.query().filter(m.StorySource.title == title)
	source = q.get()
	if not source:
		source = m.StorySource(title = title, storyCount = 0, wordCount = 0)
	source.storyCount += storyCount
	source.wordCount += wordCount
	return source

#get list of articles
def importStories(request, response, source, limit=None, offset=0, resetSource=False):
	if source == 'ae':
		if(resetSource):
			clearDataStore('Story','AE - The Canadian Science Fiction Review')
		_importStoriesFromAE(request, response, limit, offset)



def _importStoriesFromAE(request, response, limit, pageOffset=0, overwrite=False):
	pageSize = 9
	publication = 'AE - The Canadian Science Fiction Review'
	#Get links to all the stories we're going to import
	for i in range(pageOffset,8):
		if limit and (pageSize * i - pageSize*pageOffset) < limit:
			n = i * pageSize
			r = requests.get("http://aescifi.ca/index.php/fiction?start="+str(n))
			indexSoup = BeautifulSoup(r.text)		
			stories = indexSoup.find_all('a',class_='contentpagetitle')

	response.out.write('got story list <br/>')

	#Cycle through all the story links we got and import the stories		
	storyList = []
	storyCount = 0
	wordCount = 0
	urlBase = 'http://aescifi.ca'
	for s in stories:
		if storyCount < limit:
			storyEntity = _importStoryFromAE(request, response, urlBase+str(s['href']), publication, overwrite)
			if storyEntity:
				storyCount += 1
				wordCount += storyEntity.wordCount
				storyList.append(storyEntity)
				response.out.write('{0}. got story: {1} <br/>'.format(storyCount, storyEntity.title))


	if storyCount > 0:
		storySource = _updateStorySource(publication, storyCount, wordCount)
		storyList.append(storySource)
		ndb.put_multi(storyList)
		response.out.write('import complete: {0} stories / {1} words / {2} ave words / story'.format(storyCount, wordCount, wordCount / storyCount))		
	else:
		response.out.write('no stories imported')	



				
def _importStoryFromAE(request, response, url, publication, overwrite=False):
	logging.info('trying to get story from: {0}'.format(url))
	
	r1 = requests.get(url)
	r1.encoding = 'UTF-8'
	soup = BeautifulSoup(r1.text, "html5lib")

	title = soup.find('title').get_text().strip()
	creator = [soup.find("span",class_="author").get_text().strip()]

	s = None
	q = m.Story.query().filter(m.Story.title == title, m.Story.firstPub.publication == publication)
	existingStory = q.get()
	
	if not existingStory or overwrite:
		#TODO - filter out image and separate out author info (last p, after hr)
		storyText =''
		textContainer = soup.find('td', class_='mainarticle')
		
		for t in textContainer.find_all(['p','h1','h2','h3','center','<blockquote>']):
			storyText += t
		
		wordCount = len(storyText.replace('<p>','').replace('</p>','').split(None))	
		
		firstPub = m.FirstPub (
			 url = url
			, publication = publication
			, comments = 0
		)
		s = m.Story(
			category = 'fiction'
			, genre = 'sci-fi'
			, language = 'english'
			, title = title
			, creator = creator
			, text = storyText
			, wordCount = wordCount			
			, firstPub = firstPub
		)
	else:
		response.out.write('skipping story, already exists: {0} - {1} <br/>'.format(title, publication))
	return s	

	

	
	
		
	

	
	
	
	
	
	
	
	
	
	
