import cgi
import os, sys
lib_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lib')
sys.path.insert(0, lib_path)

from google.appengine.ext.webapp import template
from google.appengine.api import users
from application import adminmodel as model
import webapp2
from application import common
import re
import logging

tpath = os.path.join(os.path.dirname(__file__), 'static/templates/')

class Home(webapp2.RequestHandler):
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

class Preview(webapp2.RequestHandler):
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
				self.response.out.write("Title: {0}<br/>".format(model.encodeString(story.title)))
				if story.creator and story.creator[0]:
					self.response.out.write("Author: {0}<br/>".format(story.creator[0]))		
				if story.wordCount:		
					self.response.out.write("Word Count: {0}<br/>".format(story.wordCount))
				self.response.out.write("Publication: {0}<br/>".format(story.firstPub.publication))
				if story.firstPub.date:
					self.response.out.write("Publication Date: {0}</br>".format(story.firstPub.date))
				self.response.out.write("URL: <a target='_blank' href='{0}'>{0}</a><br/>".format(story.firstPub.url))
				social = ['fbShares','tweets','comments','altScore']
				for s in social:
					if hasattr(story.firstPub, s):
						self.response.out.write('{0}: {1}<br/>'.format(s, getattr(story.firstPub,s)))
				
				if story.text:
					self.response.out.write(model.encodeString(story.text))
				if story.creatorInfo:
					self.response.out.write("<hr/>{0}".format(model.encodeString(story.creatorInfo)))
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
		sourceKey = common.getValidatedParam(self.request, self.response, 'sourceKey', None, None)
		storyKey = common.getValidatedParam(self.request, self.response, 'storyKey', None, None)

		if storyKey:
			logging.info('attempting to reimport story')
			from application import adminmodel as model
			model.setup(self.request, self.response)
			model.reimportStory(storyKey)
			self.response.out.write('<a href="/admin">Return to Admin Home</a>')
		elif sourceKey:
			first = common.getValidatedParam(self.request, self.response, 'first', None, 'number')
			reimport = common.getValidatedParam(self.request, self.response, 'reimport', False, 'bool')
			last = common.getValidatedParam(self.request, self.response, 'last', 0, 'number')
			model.importStories(sourceKey, first, last, reimport)
			self.response.out.write('<a href="/admin">Return to Admin Home</a>')
		else:
			self.response.out.write('No storyKey provided. Could not reimport story <br/> requestUri: {0}'.format(self.request.url))
	
class Recount(webapp2.RequestHandler):
	def get(self):
		model.setup(self.request, self.response)
		model.sourceRecount()

class UpdateSources(webapp2.RequestHandler):
	def get(self):
		model.updateSources()

class Delete(webapp2.RequestHandler):
	def get(self):
		urlSafeSourceKey = common.getValidatedParam(self.request, self.response, 'sourceKey',None, None)
		if urlSafeSourceKey:
			source = model.ndb.Key(urlsafe=urlSafeSourceKey).get()
			if source:
				s = "<!DOCTYPE html><html><body><form action='/admin/delete' method='POST'>"
				s += "You are about to delete all stories imported from {0}<br/>".format(source.title)
				s += "To proceed, enter 'DELETE' (all caps) below and submit<br/>"
				s +="<input type='text' name='confirm' autocomplete='off'/><input type='submit'/><input name='sourceKey' type='hidden' value='{0}'/>".format(urlSafeSourceKey)
				s +="</form></body</html>"
				self.response.out.write(s)
			else:
				response.out.write('Invalid source key passed in.<br/>')
		else:
			self.response.out.write('No source key passed in.<br/>')
		self.response.out.write('<a href="/admin">Return to Admin Home</a>')
		
	def post(self):
		urlSafeSourceKey = common.getValidatedParam(self.request, self.response, 'sourceKey',None, None)
		confirm = common.getValidatedParam(self.request, self.response, 'confirm', None, None)
		if confirm and confirm == 'DELETE':
			if urlSafeSourceKey:
				sourceKey = model.ndb.Key(urlsafe=urlSafeSourceKey)
				source = sourceKey.get()
				if source:
					model.clearDataStore('Story', source.title)
					source.storyCount = 0
					source.wordCount = 0
					source.put()
					self.response.out.write('Deleted all stories from: {0}</br>'.format(source.title))
				else:
					self.response.out.write('Invalid source key recieved.')
			else:
				self.response.out.write('No source key passed in.<br/>')
		else:
			self.response.out.write('Invalid confirm string. Delete aborted.<br/>')	
		self.response.out.write('<a href="/admin">Return to Admin Home</a>')

app = webapp2.WSGIApplication([
	('/admin',Home),
	('/admin/preview', Preview),
	('/admin/import',ImportStories),
#	('/admin/reset',ResetDataStore),
	('/admin/delete', Delete),	
	('/admin/recount',Recount),
	('/admin/buildrecs',BuildRecommendations),
	('/admin/updatesources', UpdateSources)
], debug=True)
			
def main():
	logging.info('strong again, like me')
	app.run()

if __name__ == "__main__":
	logging.info('all monkeys are french')
	main()


    	