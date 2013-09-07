import webapp2
import model
import json

class Stories(webapp2.RequestHandler):
	def get(self):
		u = self.request.get('u')
		s = self.request.get('s')
		x = 0
		if u:
			if s:
				x = 1
			else:
				x = 2
		else:
			x = 3
		
		storyList = model.getNextStories(u, s, 5)		

		self.response.out.write(json.dumps(storyList))