import cgi
import os
import sys
from google.appengine.api import users
from google.appengine.ext.webapp import template
import webapp2
#import mysqlorm
import svr.service as service
#import MySQLdb



class Home(webapp2.RequestHandler):
	def get(self):
		path = os.path.join(os.path.dirname(__file__), 'static/templates/index.html')
		template_values = {}
		self.response.out.write(template.render(path, template_values))

class Login(webapp2.RequestHandler):
	def get(self):
		path = os.path.join(os.path.dirname(__file__), 'static/templates/login.html')
		template_values = {}
		self.response.out.write(template.render(path, template_values))

class Reader(webapp2.RequestHandler):
	def get(self):
		template_values = {}
		path = os.path.join(os.path.dirname(__file__), 'static/templates/reader.html')
		self.response.out.write(template.render(path, template_values))

app = webapp2.WSGIApplication([
    ('/', Home),
    ('/login',Login),
    ('/reader',Reader),
	('/service/stories',service.Stories)
    
], debug=True)

def main():
    app.run()

if __name__ == "__main__":
    main()