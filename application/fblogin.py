from pyfacebook import pyfacebook as facebook

fb = None

def connect():
	# Initialize the Facebook Object.
	api_key = '540268512708656'
	secret_key = '4f165ccf0a05ab738e2d19ffc2ff828f'
	fb = facebook.Facebook(api_key, secret_key)
	return fb

def login(controller):
	
	if not fb:
		return False
	controller.response.out.write(fb)
	# Checks to make sure that the user is logged into Facebook.
	if this.fb.check_session(controller.request):
		pass
	else:
		# If not redirect them to your application add page.
		controller.response.out.write(url)
		url = this.fb.get_add_url()
		#controller.response.out.write('<fb:redirect url="' + url + '" />')
		return False
	
	# Checks to make sure the user has added your application.
	if this.fb.added:
		pass
	else:
		# If not redirect them to your application add page.
		url = this.fb.get_add_url()
		controller.response.out.write(url)
		#controller.response.out.write('<fb:redirect url="' + url + '" />')
		return False
	return True