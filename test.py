from pyfacebook import pyfacebook as facebook
		# Initialize the Facebook Object.
		api_key = '540268512708656'
		secret_key = '4f165ccf0a05ab738e2d19ffc2ff828f'
		self.facebookapi = facebook.Facebook(api_key, secret_key)
		
		# Checks to make sure that the user is logged into Facebook.
		if self.facebookapi.check_session(self.request):
			self.response.out.write('fb session success')
			pass
		else:
			# If not redirect them to your application add page.
			self.response.out.write('fb session fail')
			url = self.facebookapi.get_add_url()
			self.response.out.write(url)
			self.response.out.write('<fb:redirect url="' + url + '" />')
			return
		
		# Checks to make sure the user has added your application.
		if self.facebookapi.added:
			self.response.out.write('fb permission success')
			pass
		else:
			self.response.out.write('fb permission fail')
			# If not redirect them to your application add page.
			url = self.facebookapi.get_add_url()
			self.response.out.write('<fb:redirect url="' + url + '" />')
			return
		
		#self.response.out.write(l)
		#self.response.out.write(fb.uid)
		
		# Get the information about the user.
		#user = fb.users.getInfo( [fb.uid], ['uid', 'name', 'birthday', 'relationship_status'])[0]
		# Display a welcome message to the user along with all the greetings.
		#self.response.out.write("<html> <body>")
		#self.response.out.write('Hello %s,<br>' % user['name'])
		#self.response.out.write("</html> </body>")
	