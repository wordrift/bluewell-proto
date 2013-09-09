import cgi
import os, sys
lib_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lib')
sys.path.insert(0, lib_path)

from google.appengine.ext.webapp import template
from google.appengine.api import users
from application import model
import webapp2
from application import common
import re
import logging

tpath = os.path.join(os.path.dirname(__file__), 'static/templates/')

# Some mobile browsers which look like desktop browsers.
RE_MOBILE = re.compile(r"(iphone|ipod|blackberry|android|palm|windows\s+ce)", re.I)
RE_DESKTOP = re.compile(r"(windows|linux|os\s+[x9]|solaris|bsd)", re.I)
RE_BOT = re.compile(r"(spider|crawl|slurp|bot)", re.I)

def getUserAndSetupStream(request, response):
	gUser = users.get_current_user()
		
	if not gUser:
		common.handleError(request, response, error)
	else:		
		userId = request.get('userKey')
		if not userId:
			common.handleError(request, response, error)
		else:
			u = model.getUser(userId, 'url')
			if not u:
				handleError(request, response, error)
			model.setStream(u, 'fiction','sci-fi','english')
			return u
	return None

def isDesktop(user_agent):
  """
  Anything that looks like a phone isn't a desktop.
  Anything that looks like a desktop probably is.
  Anything that looks like a bot should default to desktop.
  
  """
  return not bool(RE_MOBILE.search(user_agent)) #and bool(RE_DESKTOP.search(user_agent)) or bool(RE_BOT.search(user_agent))

def getUserAgent(request):
  # Some mobile browsers put the User-Agent in a HTTP-X header
  #headers = ['X_OPERAMINI_PHONE_UA', 'X_SKYFIRE_PHONE', 'User-Agent']
  #TODO work on better mobile detection, distinguish between iPad and iPhone
  headers = ['User-Agent']
  for h in headers:
  	if h in headers:
  		return str(request.headers[h])
  return None

class Home(webapp2.RequestHandler):
	def get(self):
		template_values = {
			'loginUrl' : users.create_login_url('/reader')
		}
		self.response.out.write(template.render(tpath + 'index.html', template_values))

class Reader(webapp2.RequestHandler):
	def get(self):
		gUser = users.get_current_user()

		if gUser: 
			gId = gUser.user_id()
			email = gUser.email()
			user = model.getUser(gId, 'google')
			if not user:
				#TODO Check if user is on invite list
				#If not, redirect to "added to waiting list" page
				user = model.createUser(gId, email, 'google')		
			
			userAgent = getUserAgent(self.request)
			logging.info('userAgent: {0}'.format(userAgent))
			#if(isDesktop(userAgent)):
			#	template = 'reader.html'
			#else:
		#		template = 'mobileReader.html'
			template_values = {
				'userNick': gUser.email(), 
				'logoutUrl': users.create_logout_url('/'),
				'userKey': user.key.urlsafe()
			}
			self.response.out.write(template.render(tpath+'reader.html', template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))

class Stream(webapp2.RequestHandler):
	def get(self):
		user = getUserAndSetupStream(self.request, self.response)

		anchorId = common.getValidatedParam(self.request, self.response, 'anchorKey', None, None)
		if anchorId:
			anchor = model.getAnchor(anchorId, 'url')
		else:
			anchor = None
		includeAnchor = common.getValidatedParam(self.request, self.response, 'includeAnchor', True, 'bool')
		numPrevious = common.getValidatedParam(self.request, self.response, 'numPrevious', 0, 'number')
		numAfter = common.getValidatedParam(self.request, self.response, 'numAfter', 0, 'number')
		fullText = common.getValidatedParam(self.request, self.response, 'fullText', False, 'bool')
						
		stories = model.getStories(anchor, includeAnchor, numPrevious, numAfter, fullText)

		self.response.content_type = 'text/json'		
		self.response.out.write(common.json.dumps(stories))
		
	def post(self):
		user = getUserAndSetupStream(self.request, self.response)	
		stories = common.getValidatedParam(self.request, self.response, 's', None, 'json')			
		updatedStories = model.updateStream(stories)
		
		self.response.out.write(common.json.dumps(updatedStories))			

class Admin(webapp2.RequestHandler):
	def get(self):
		from application import adminmodel as model
		import urllib
		
		#model.sourceRecount()
		
		pageSize = common.getValidatedParam(self.request, self.response, 'pageSize', 20, 'number')
		offset = common.getValidatedParam(self.request, self.response, 'offset', 0, 'number')
		filters = common.getValidatedParam(self.request, self.response, 'filters', None, 'dict')
		order = common.getValidatedParam(self.request, self.response, 'order', None, 'list')
		
		logging.info(order)		
		
		storyResults = model.getStories(filters, order, pageSize, offset)
		sourceResults = model.getSources()
		
		sources = []
		for s in sourceResults:
			if s.storyCount:
				wps = s.wordCount / s.storyCount
			else:
				wps = 'N/A'
			sources.append({
				'title': s.title
				, 'storyCount' : s.storyCount
				, 'wordCount' : s.wordCount
				, 'wps': wps
				, 'urlSafeKey' : s.key.urlsafe()
				, 'urlSafeTitle':urllib.quote_plus(s.title)
			})

		stories = []
		for s in storyResults:
			stories.append({
				'title' : s.title
				, 'creator' : s.creator
				, 'publication' : s.firstPub.publication
				, 'wordCount' : s.wordCount
				, 'urlSafeKey' : s.key.urlsafe()
			})
		 
		
			 
		template_values = {'stories':stories, 
			'sources':sources, 
			'filterString':common.getParamString(self.request, self.response, 'filters'),
			'order':order,
			'orderString':common.getParamString(self.request, self.response, 'order')
		}
		logging.info('orderString: {0}'.format(template_values['orderString']))
		self.response.out.write(template.render(tpath+'admin.html', template_values))



class BuildRecommendations(webapp2.RequestHandler):
	def get(self):
		gUser = users.get_current_user()
		if gUser:			
			user = model.getUser(gUser.user_id(), 'google')
			if not user:
				handleError(request, response, error)
			model.setStream(user, 'fiction','sci-fi','english')
			model.buildRecommendations(0, 100, 0, True, self.response.out)
			self.response.out.write('build recommendations complete')
		else:
			self.response.out.write('build recommendations failed, no user logged in')

class ResetDataStore(webapp2.RequestHandler):
	def get(self):
		model.clearDataStore('Rec')
		model.clearDataStore('User')
		model.clearDataStore('StreamNode')
		model.clearDataStore('Story')

class AdminPreview(webapp2.RequestHandler):
	def get(self):
		urlSafeStoryKey = common.getValidatedParam(self.request, self.response, 'storyKey', None, None)
		
		if urlSafeStoryKey:
			storyKey = model.ndb.Key(urlsafe=urlSafeStoryKey)
			story = storyKey.get()
			if story:
				self.response.out.write("<a href='/admin'>Return to Admin Home</a>&nbsp;&nbsp;")
				self.response.out.write("<a href='/admin/import?storyKey={0}'>Reimport Story</a>".format(urlSafeStoryKey))
				self.response.out.write("<br/>")
				self.response.out.write("<!DOCTYPE html><html><head><meta charset='utf-8'/></head><body style='width:550px;border:1px solid black; padding:25px;'>")			
				self.response.out.write("Title: {0}<br/> Author: {1}<br/> Publication: {2}<br/> Word Count: {3}<br/>".format(story.title, story.creator[0], story.firstPub.publication, story.wordCount))
				self.response.out.write("URL: <a target='_blank' href='{0}'>{0}</a><br/>".format(story.firstPub.url))
				self.response.out.write(story.text)
				self.response.out.write("</body></html>")
			else:
				self.response.out.write('Invalid storyKey provided')
		else:
			self.response.out.write('No storyKey provided')	
		self.response.out.write("<a href='/admin'>Return to Admin Home</a>")
			

class ImportStories(webapp2.RequestHandler):
	def get(self):
		from application import adminmodel as model
		model.setup(self.request, self.response)
		model.setupSources()
		sourceKey = common.getValidatedParam(self.request, self.response, 'sourceKey', None, None)
		storyKey = common.getValidatedParam(self.request, self.response, 'storyKey', None, None)

		if storyKey:
			logging.info('attempting to reimport story')
			from application import adminmodel as model
			model.setup(self.request, self.response)
			model.reimportStory(storyKey)
			#self.redirect('/admin?m=ImportedStory')
		elif sourceKey:
			limit = common.getValidatedParam(self.request, self.response, 'limit', None, 'number')
			reimport = common.getValidatedParam(self.request, self.response, 'reimport', False, 'bool')
			offset = common.getValidatedParam(self.request, self.response, 'offset', 0, 'number')
			model.importStories(sourceKey, limit, offset, reimport)
		else:
			self.response.out.write('No storyKey provided. Could not reimport story <br/> requestUri: {0}'.format(self.request.url))
	
class AdminRecount(webapp2.RequestHandler):
	def get(self):
		from application import adminmodel as model
		model.setup(self.request, self.response)
		model.sourceRecount()
	
class Test(webapp2.RequestHandler):
	def get(self):
		pass
		
		
		
		
app = webapp2.WSGIApplication([
    ('/', Home),
    ('/reader',Reader),
	('/admin',Admin),
	('/admin/preview', AdminPreview),
	('/admin/import',ImportStories),
	('/admin/reset',ResetDataStore),
	('/admin/recount',AdminRecount),
	('/test',Test),
	('/service/stream',Stream),
	('/admin/buildrecs',BuildRecommendations)
    
], debug=True)

def main():
    app.run()

if __name__ == "__main__":
    main()
    
