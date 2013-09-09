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

class Test(webapp2.RequestHandler):
	def get(self):
		self.response.out.write('main Test')
		
app = webapp2.WSGIApplication([
    ('/', Home),
    ('/reader',Reader),
	('/service/stream',Stream),
	('/admin/updatesources',Test)
], debug=True)

def main():
    app.run()

if __name__ == "__main__":
    main()
    
