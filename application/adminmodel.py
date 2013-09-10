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
import datetime

request = None
response = None

AE = 'AE - The Canadian Science Fiction Review'
NATURE = 'Nature'
LIGHTSPEED = 'Lightspeed Science Fiction & Fantasy'

def setup(req, res):
	global request
	global response
	request = req
	response = res

def encodeString(string):
	#return string
	return unicode(string).encode('utf-8', 'xmlcharrefreplace')
				

def updateSources():
	sources = [
		{
			'title': NATURE,
			'listUrl':'http://www.nature.com/nature/focus/arts/futures/',
			'exclusions':[]		
		},
		{
			'title': AE,
			'listUrl':'http://aescifi.ca/index.php/fiction',
			'exclusions': ['AE Micro 2013', 'The Experiment']
		},
		{
			'title':LIGHTSPEED,
			'listUrl': 'http://www.lightspeedmagazine.com/category/fiction/science-fiction/',
			'exclusions':['Beachworld']
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
	sourceRecount()

def getSources():
	q = m.StorySource.query()
	sources = q.fetch()
	return sources

def sourceRecount(source = None):
	if not source:
		sourceQ = m.StorySource.query()
		updateList = []
		for source in sourceQ.fetch():
			source = _countSourceStats(source)
			updateList.append(source)
		ndb.put_multi(updateList)
	else:
		source = _countSourceStats(source)
		source.put()

def _countSourceStats(source):
	logging.info('updating source stats for {0}'.format(encodeString(source.title)))
	wordCount = 0
	storyCount = 0
	q = m.Story.query(m.Story.firstPub.publication == source.title)
	for s in q.fetch():
		if s.title not in source.exclusions:
			storyCount +=1
			if hasattr(s, 'wordCount') and s.wordCount:
				wordCount += s.wordCount
	source.storyCount = storyCount
	source.wordCount = wordCount
	return source
		
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
	
def clearDataStore(kind, publication=None):
	q = ndb.Query(kind=kind)
	if kind == 'Story' and publication:
		q = q.filter(m.Story.firstPub.publication == publication)
	stories = q.fetch(keys_only=True)
	ndb.delete_multi(stories)

def importStories(sourceKey, first=0, last=0, reimport=False):

	source = ndb.Key(urlsafe=sourceKey).get()
	response.out.write("Starting import stories, source: {0}, first: {1}, last: {2}, reimport: {3} <br/>".format(source.title, first, last, reimport))
	if reimport:
		storyList = _getExistingStories(source, first, last)
	else:
		storyList = _getStoriesFromWeb(source, first, last)
	response.out.write('Got list of story urls. Stories: {0}<br/>'.format(len(storyList)))
	updateList = []
	storyCount = 0
	for s in storyList:
		storyEntity = _importStory(s['url'], source, reimport)
			
		if storyEntity:
			storyCount +=1
			updateList.append(storyEntity)
			response.out.write('Got a story to update: {0}<br/>'.format(encodeString(storyEntity.title)))
			if not reimport:
				source.storyCount += 1
		else:
			response.out.write('No story entity returned <br/>')

	if len(updateList) > 0:
		updateList.append(source)
		ndb.put_multi(updateList)
		sourceRecount(source)
	else:
		logging.info('_importStories: Update list was empty')
	response.out.write('Story import complete. Updated {0} stories.<br/>Source: {1}<br/>'.format(storyCount, source))

def reimportStory(urlSafeStoryKey):
	storyKey = ndb.Key(urlsafe=urlSafeStoryKey)
	story = storyKey.get()
	q = m.StorySource.query(m.StorySource.title == story.firstPub.publication)
	source = q.get()
	updatedStory = _importStory(story.firstPub.url, source, True)
	ndb.put_multi([updatedStory, source])

def _getExistingStories(source, limit, offset):
	q = m.Story.query(m.Story.firstPub.publication == source.title)
	q = q.order(-m.Story.title)
	stories = q.fetch(limit, offset=offset)
	storyList = []
	for s in stories:
		storyList.append({'url':s.firstPub.url, 'wordCount':s.wordCount})
	return storyList

def _getStoriesFromWeb(source, first=0, last=20):
	if source.title == AE:
		return _getStoryListAE(source.listUrl, first, last)
	elif source.title == LIGHTSPEED:
		return _getStoryListLightspeed(source.listUrl, first, last)
	elif source.title == NATURE:
		return _getStoryListNature(source.listUrl, first, last)

def _getStoryListAE(url, firstPage=0, lastPage=8):
	#Get links to all the stories we're going to import
	pageSize = 9
	stories = None
	urlBase = 'http://aescifi.ca'
	storyList = []
	for i in range(firstPage,lastPage):
		r = requests.get("http://aescifi.ca/index.php/fiction?start="+str(i*pageSize))
		indexSoup = BeautifulSoup(r.text)		
		stories = indexSoup.find_all('a',class_='contentpagetitle')
		if stories:
			for s in stories:
				storyList.append({'url':urlBase+str(s['href'])})
	return storyList

def _getStoryListLightspeed(url, firstPage=1, lastPage=16):
	stories = None
	storyList = []
	for i in range(firstPage, lastPage):
		if i > 1:
			r = requests.get("{0}page/{1}".format(url, i))
		else:
			r = requests.get(url)
		indexSoup = BeautifulSoup(r.text)
		for t in indexSoup.find_all('h2', class_='posttitle'):		
			s = t.find('a',rel='bookmark')
			if s:
				storyList.append({'url':str(s['href'])})
	return storyList	

def _getStoryListNature(url, first=0, last=0):
	r = requests.get(url)
	soup = BeautifulSoup(r.text)
	storyList = []
	storyCount =0
	urlBase = 'http://www.nature.com'
	for ul in soup.find_all('ul',class_='article-list'):
		for a in ul.find_all('article'):
			storyCount +=1
			if storyCount >= first and storyCount <last:
				url = a.find('a')['href']
				if 'doifinder' in url:
					storyList.append({'url':urlBase+url})
				
	return storyList

def _importStory(url, source, overwrite):
	response.out.write('trying to get story from: {0}<br/>'.format(url))
	r1 = requests.get(url)
	r1.encoding = 'UTF-8'
	soup = BeautifulSoup(r1.text, "html5lib")
	
	s = None
	title = _titleFromSoup(soup, source)
	if title:
		if title not in source.exclusions:
			q = m.Story.query().filter(m.Story.title == title, m.Story.firstPub.publication == source.title)
			existingStory = q.get()
			if not existingStory:
				s = m.Story()
			elif overwrite:
				s = existingStory
	
			if s:
				s.title = title	
				s = _storyEntityFromSoup(soup, url, source, s)
				response.out.write('imported story: {0}<br/>'.format(encodeString(title)))		
			else:
				response.out.write('skipping story, already exists: {0} - {1} <br/>'.format(encodeString(title), source.title))
		else:
			response.out.write('Story: {0} is in exclusions list, skipping<br/>'.format(encodeString(title)))
	else:
		response.out.write('Failed to get story title for {0} <br/>'.format(url))
	return s	

def _storyEntityFromSoup(soup, url, source, s):
	if source.title == AE:	
		return _parseSoupAE(soup, url, source, s)
	elif source.title == LIGHTSPEED:
		return _parseSoupLightspeed(soup, url, source, s)
	elif source.title == NATURE:
		return _parseSoupNature(soup, url, source, s)
		
def _titleFromSoup(soup, source):
	title = None
	if source.title == AE:
		title = soup.find('title').get_text().strip()
	elif source.title == LIGHTSPEED:
		title = soup.find('h1', class_='posttitle').get_text().strip()
	elif source.title == NATURE:
		titleTag = soup.find('meta', attrs={"name":re.compile("^dc.title$", re.I)})
		if titleTag:
			title = titleTag['content']
		else:
			logging.info('Error: Failed to get title from document.')
	logging.info('_titleFromSoup: {0}'.format(encodeString(title)))
	return title
		
def _parseSoupAE(soup, url, source, s):
	creator = [soup.find("span",class_="author").get_text().strip()]
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
	
	storyText = unicode(story)
	wordCount = len(storyText.split(None))	
	
	firstPub = m.FirstPub (
		 url = url
		, publication = source.title
	)
	s.populate(
		category = 'fiction'
		, genre = 'sci-fi'
		, language = 'english'
		, creator = creator
		, creatorInfo = creatorInfo
		, text = storyText
		, wordCount = wordCount			
		, firstPub = firstPub
	)
	
	#Get number of comments
	commentParent = soup.find('div',id='comments-list-0')
	if commentParent:
		numComments = 0
		for d in commentParent.find_all('div', recursive=False):
			logging.info('got comment tag: {0}'.format(d))
			numComments += 1
		s.firstPub.comments = numComments
	
	return s	

def _parseSoupLightspeed(soup, url, source, s):
	creator = [soup.find('a',class_='author').get_text()]
	logging.info('got creator: {0}<br/>'.format(creator))
	
	storyRoot = soup.find('div', class_='entry-content')
	del storyRoot['class']
	story = storyRoot.extract()

	d = story.find('div', class_='callout')
	d.decompose()
	d = story.find('iframe')
	d.decompose()
	
	for p in story.find_all('p'):
		if (p.has_attr('id') and p['id'] == 'tags') or (p.has_attr('align') and p['align']=='center') \
		or (p.has_attr('style') and 'text-align:center' in p['style']):
			p.decompose()

	storyText = unicode(story)
	wordCount = len(storyText.split(None))	
	
	#Get author info
	creatorInfo = soup.find('div', id="about_author")
	logging.info('got creator info tag')
	tags = creatorInfo.find_all(['h2', 'h3', 'ul'])
	for t in tags:
		t.decompose()
	
	#Get issue and publication date
	a = soup.find('ul', class_='buy_list').a

	href = a['href']
	logging.info(unicode(href))
	info = a['href'].split('/')[4].split('-')
	logging.info(info)

	dateString = "{0} 01 {1}".format(info[0].title(), info[1])
	logging.info(dateString)
	publicationDate = parser.parse(dateString)
	issue = info[3]	
	response.out.write('processed info: {0} / {1} <br/>'.format(publicationDate, issue))
	
	firstPub = m.FirstPub(
		url = url
		, publication = source.title
		, date = publicationDate
		, issue = issue
	)
	s.populate(
		category = 'fiction'
		, genre = 'sci-fi'
		, language = 'english'
		, creator = creator
		, creatorInfo = unicode(creatorInfo)
		, text = storyText
		, wordCount = wordCount
		, firstPub = firstPub
	)
	
	#Get number of comments
	commentsTag = soup.find('h3',id='comments')
	if commentsTag:
		commentsString = commentsTag.get_text().strip().replace('Responses','')[:1]
		numComments = int(commentsString)
		s.firstPub.comments = numComments
		response.out.write('comments string: {0} <br/>'.format(encodeString(commentsString)))
	return s
	
def _parseSoupNature(soup, url, source, s):
	if soup.find('title').get_text().strip() != 'Nature Publishing Group: Error Page':
		meta = {}
		for t in soup.find_all('meta', attrs={'name':True}):
			key = name_map_nature(t['name'])
			if key != False:
				meta[key] =  t['content']
				
		if 'doi' in meta:		
			doi = meta['doi'].replace('doi:','')
			publicationDate = parser.parse(meta['publicationDate'])			
			firstPub = m.FirstPub(
				url = url
				, publication = NATURE
				, date = publicationDate
				, doi = doi
				, volume = meta['volume']
				, issue = meta['issue']
				, section = meta['section']
			)
						
			#Get story text
			storyRootParent = soup.find('div', class_='section second no-nav no-title')
			if storyRootParent == None:
				storyRoot = soup.find('div',id='articlebody')
			else:			
				storyRoot = storyRootParent.find('div',class_='content')
							
			if storyRoot != None:
				del storyRoot['class']
				del storyRoot['id']

				for t in storyRoot.findAll('div', class_='illustration'):
					t.decompose()

				t = storyRoot.find('div', id='illus1')
				if t:
					t.decompose()
				storyText = unicode(storyRoot)
				wordCount = len(storyText.split(None))	
			else:
				storyText = 'Story text import failed.<br/>'
				wordCount = 0
		
			creatorInfoDiv = None
			creatorInfoDivParent = soup.find('div',id='author-affiliations')
			if creatorInfoDivParent:
				creatorInfoDiv = creatorInfoDivParent.find('h3')
			else:
				creatorInfoDivParent = soup.find('div', id='affiliations-notes')
				if creatorInfoDivParent:
					creatorInfoDiv = creatorInfoDivParent.find('li')
						
			if creatorInfoDiv:
				creatorInfoDiv.name = 'div'
				creatorInfo = unicode(creatorInfoDiv)
			else:
				creatorInfo = None
		
			#Get metrics data		
			articleId = doi.split('/')[1]
			metricsUrl = "http://www.nature.com/nature/journal/v"+meta['volume']+"/n"+meta['issue']+"/"+articleId+"/metrics"
			r2 = requests.get(metricsUrl)
			mSoup = BeautifulSoup(r2.text)

			donut = mSoup.find('div',class_='altmetric-donut')	
			if donut != None:
				firstPub.altScore = int(donut.find('img')['src'].split('&')[1].split('=')[1])					
				altmetricContexts = []
				context_block = mSoup.find('div',class_='altmetric-context')
				if context_block != None:
					contexts = context_block.find_all('li')
					for c in contexts:
						altmetricContexts.append(c.get_text().replace('\n','').replace('\t',''))
					firstPub.atlContext = unicode(altmetricContexts)
					
				networks = ['twitter','facebook']
				for n in networks:
					block = mSoup.find('div',class_='altmetric-'+n)
					if block != None:
						setattr(firstPub, n, int(block.find('b').get_text()))
				
				block = mSoup.find('h2',class_='metrics-header').find('span',class_='total')
				if block != None:
					setattr(firstPub, 'pageViews', int(block.get_text().replace(',','')))
				
			s.populate(
				category = 'fiction'
				, genre = 'sci-fi'
				, language = 'english'
				, title = meta['title']
				, subtitle = meta['subtitle']
				, text = storyText
				, wordCount = wordCount
				, firstPub = firstPub 
			)
			if creatorInfo:
				s.creatorInfo = creatorInfo
			if 'author' in meta:
				s.creator = [meta['author']]

		else:
			response.out.write('No DOI, skipping<br/>')
			s = None
	else:
		s = None
		response.out.write('Story link lead to Nature error page. No story imported<br/>')
	return s
	
#define the key mapping
def name_map_nature(old_name):
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
	
		
	

	
	
	
	
	
	
	
	
	
	
