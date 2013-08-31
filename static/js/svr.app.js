
function SVRLoginController(kwargs) {
	console.log('SVRLoginController constructor');
	this._model = new SVRModel();
	var c = this;
	$('.login-button').bind('click', $.proxy(this.login, c));
	
	var s = $.proxy(function(e){
		var code = (e.keyCode ? e.keyCode : e.which);
 		if(code == 13) { //Enter keycode
   			this.login();
 		}
	},c);
	$('#password-input').bind('keypress',s);
	$('#username-input').bind('keypress',s);
}

SVRLoginController.prototype.login = function() {
	console.log('login button pressed');
	var username = $('#username-input').val();
	var password = $('#password-input').val();
	if(!username || !password) {
		$('#login-error').html('Please enter username and password to login.');
	} else {
		this._model.login({
			scope:this,
			username:username,
			password:password,
			success:function(user) {
				window.location.href = '/reader';
			},
			error:function(error) {
				$('#password-input').val('');
				$('#login-error').html('Incorrect username or password. Please try again.');
			}
		});
	}
}
/***************
SVR Controller
****************/
function SVRController(kwargs) {
	console.log('SVRController constructor');
	//var SVRController = this;
	this._user = null;
	this._story = null;
	this._favorite = false;
	this._rating = null;
	this._model = new SVRModel();
	this._view = new SVRWebView({model:this._model, controller:this});
	this._loadCurrentUserAndStory();
}

SVRController.prototype.loadStory = function(s) {
	console.log('loadStory',s);
	this._story = s;
	this._favorite = false;
	this._rating = null;
	this._view.setStory(s);
	this._view.setFavorite(this._favorite);
	this._view.setRating(this._rating);
	
	if(this._user) {
	
		
	
//		this._model.updateReadingHistory(this._user, s);
		
		
	this._model.getFavoriteStatus({
			scope:this,
			user:this._user,
			story: s,
			success: function(favorite) {
				console.log('SVRController loadStory setting favorite',favorite);
				this._favorite = favorite;
				this._view.setFavorite(favorite);
			}
		});
		this._model.getRating({
			scope:this,
			story:this._story,
			user:this._user,
			success:function(ratingObj) {
				console.log('SVRController loadStory got a rating',ratingObj);
				this._rating = ratingObj;
				var rating = 0;
				if(ratingObj) {
					rating = ratingObj.get('rating');
				} 
				this._view.setRating(rating);
			}
		});
		
	}
};

SVRController.prototype.loadNextStory = function(s, forceNew) {
	console.log('SVRController loadNextStory', arguments);
	this._model.getNextStory({
		scope:this,
		user:this._user,
		story:this._story,
		success:function(story) {
			console.log('SVRController loadNextStory success', this);
			this.loadStory(story);
		},
		error:function(error) {
		}
	});
}

SVRController.prototype.loadPreviousStory = function() {
	this._model.getPreviousStory({
		scope:this,
		story:this._story,
		success: function(story) {
			console.log('SVRController loadPreviousStory success: ', story);
			this.loadStory(story);
		},
		error: function(error) {
		}
	});
}

SVRController.prototype._loadCurrentUserAndStory = function() {
	this._model.getCurrentUser({
		scope: this,
		success: function(user) {
			console.log('SVRController successfully got current user', user);
			this._user = user;
			this._view.setCurrentUser(user);
			this.loadNextStory(user, null);
		},
		error: function(error) {
			console.error('SVRController: Error loading current user', error);
		}
	});
}

SVRController.prototype._onFavoriteClick = function() {
	console.log('favorite clicked', this);
	this._model.setFavorite({
		scope: this,
		user: this._user,
		story: this._story,
		favorite: !this._favorite,
		success:function(favorite) {
			this._favorite = favorite;
			this._view.setFavorite(favorite);		
		}
	});
	return;
}
SVRController.prototype._setRating = function(r) {
	this._model.setRating({
		scope:this,
		user:this._user,
		story:this._story,
		rating: r,
		success:function(ratingObj) {
			this._rating = ratingObj;
			this._view.setRating(r);
		}
	});
}
SVRController.prototype._onUpClick = function() {
	console.log('up clicked', this._rating);	
	if(!this._rating || this._rating.get('rating')!=5){
		console.log('setting rating to 5');
		this._setRating(5);
	} else {
		console.log('clearing rating');
		this._setRating(0);
	}
}

SVRController.prototype._onDownClick = function() {
	console.log('down clicked', this._rating);
	if(!this._rating || this._rating.get('rating')!=1){
		this._setRating(1);
	} else {
		this._setRating(0);
	}
}

SVRController.prototype._onPreviousClick = function() {
	console.log('previous clicked');
	this.loadPreviousStory(this._story);
}

SVRController.prototype._onNextClick = function() {
	console.log('next clicked');
	this.loadNextStory(this._story);
}

SVRController.prototype._onLogoutClick = function() {
	this._model.logout({
		scope: this,
		success: function() {
			this._reset();
			window.location.href = '/';
		}
	});
	
}

SVRController.prototype._onIncreaseFontClick = function() {
	this._view.increaseFontSize();
}

SVRController.prototype._onDecreaseFontClick = function() {
	this._view.decreaseFontSize();
}

SVRController.prototype._onLightClick = function() {
	console.log('SVRController _onLightClick()');
	this._view.setTheme('light');
}

SVRController.prototype._onDarkClick = function() {
	console.log('SVRController _onDarkClick()');
	this._view.setTheme('dark');
}


SVRController.prototype._reset = function() {
	this._user = null;
	this._story = null;
	this._rating = null;
	this._favorite = false;
}
SVRController.prototype.isMobile = function detectmob() { 
	if( navigator.userAgent.match(/Android/i)
			|| navigator.userAgent.match(/webOS/i)
			|| navigator.userAgent.match(/iPhone/i)
			|| navigator.userAgent.match(/iPad/i)
			|| navigator.userAgent.match(/iPod/i)
			|| navigator.userAgent.match(/BlackBerry/i)
			|| navigator.userAgent.match(/Windows Phone/i)) {
		return true;
		} else {
    	return false;
  	}
}
/***********
STORY MODEL
***********/
function SVRModel(kwargs) {
	console.log('SVRModel constructor');
	Parse.initialize('arVFof1gZO9kqxJl5GboE5UEb93JQ0Fmc9lifegC','QKKQManFWBNgFE2RUyYpI80MD5SlVjcfEziEdBIL');
	Story = Parse.Object.extend("Story");
	Rating = Parse.Object.extend("UserRatings");
	return this;
}

SVRModel.prototype.login = function(kwargs) {
	Parse.User.logIn(kwargs.username, kwargs.password, {
		success: function(user) {
			console.log('SVRModel login successful', kwargs,user);
			kwargs.success.call(kwargs.scope, user);
		},
		error: function(error) {
			kwargs.error.call(kwargs.scope, error);
		}
	});
}

SVRModel.prototype.getCurrentUser = function(kwargs) {
	var user = Parse.User.current();
	if(user !=null) {user.fetch();}
	console.log('SVRModel getCurrentUser', user);
	if(!user || user.get('username')==undefined) {
		console.warn('SVRModel user not logged in');
		window.location.href = '/';
	} else {
		console.log('SVRModel user already logged in');
		kwargs.success.call(kwargs.scope, user);
	}
	return user;
}

SVRModel.prototype.get= function(object, property) {
	return object.get(property);
}

SVRModel.prototype._getStoryQuery = function(direction) {
	var query = new Parse.Query(Story);
	switch(direction){
	case 'next':
		query.descending('createdAt');
		query.descending('altmetricScore');
		break;
	case 'previous':
		query.descending('createdAt');
		query.ascending('altmetricScore');
	}
	return query;
}

SVRModel.prototype._getFirstStory = function(kwargs) {
	var q = this._getStoryQuery('next');
	q.limit(1);
	q.find({
		scope: this,
		success: $.proxy(function(results) {
			console.log('SVRController loadNextStory success loading first story!');
			this.loadStory(results[0]);
		},kwargs.scope),
		error: function(error) {alert('SVRModel error loading first story!' + error);}
	});
}

SVRModel.prototype.getCurrentlyReadingStory = function(kwargs){
	console.log('SVRModel getCurrentlyReadingStory', kwargs);
	if(kwargs.user && kwargs.user.get('currentlyReading')!=undefined) {
		kwargs.user.get('currentlyReading').fetch({
			success: function(story) {
				console.log('SVRController loadNextStory success loading currentlyReading!');
				kwargs.success.call(kwargs.scope, story);
			},
			error: function(error) {
				console.error('SVRModel error fetching currentlyReadingStory', error);
			}
		});
	} else {
		this._getFirstStory(kwargs);
	}
}

SVRModel.prototype._processStoryResults = function(results) {
	console.log('SVRModel _processStoryResults', results);
}

SVRModel.prototype.getNextStory= function(kwargs) {
	var url = '/service/stories';
	console.log('SVRModel getNextStory, url:', url);
	//TOTD First check if we already have the next story in our local store
	
	//TODO ask server for the next story
	/*var p = $.proxy(function(data) {this._processStoryResults(data);}, this);
	//If not, ask the server
	$.get(url, {
		u: kwargs.user ? kwargs.user.id : 0,
		s: kwargs.story ? kwargs.user.id: 0
	}, p, 'json');*/


	if(kwargs.story==null) {
		this.getCurrentlyReadingStory(kwargs);
	} else {
		var s = kwargs.story;
		var q = this._getStoryQuery('next');
		q.descending('altmetricScore');
		console.log('looking for the next lower score', s.get('altmetricScore'));
		q.lessThanOrEqualTo('altmetricScore',s.get('altmetricScore'));
		q.limit(15);
		q.find({
			success: $.proxy(function(results) {
				console.log('SVRController loadNextStory success loading next story!');
				var storyToLoad = null;
				var currentScore = s.get('altmetricScore');
				var createdAt = s.createdAt;
				for (i in results) {
					if(results[i].get('altmetricScore')==currentScore) {
						if(results[i].createdAt<createdAt) {
							storyToLoad = results[i];
							break;
						}
					} else {
						storyToLoad = results[i];
						break;
					}
				}
				console.log('story to load: ', storyToLoad);
				kwargs.success.call(kwargs.scope, storyToLoad);
			},this),
			error:function(error) {console.error('SVRModel error loading next story' + error);}
		});
	}
}

SVRModel.prototype.getPreviousStory = function(kwargs) {
	var q = this._getStoryQuery('previous');
	q.limit(15);
	
	console.log('looking for the next higher score', kwargs.story.get('altmetricScore'));
	q.greaterThanOrEqualTo('altmetricScore',kwargs.story.get('altmetricScore'));
	q.find({
		success:function(results) {
			console.log('StoryMode getPreviousStory: Success getting previous story');
			var previousStory = null;
			var currentScore = kwargs.story.get('altmetricScore');
			var currentStoryId = kwargs.story.get('objectId');
			var createdAt = kwargs.story.get('createdAt');
			for (i in results) {
				if(results[i].get('altmetricScore')==currentScore) {
					if(results[i].createdAt<createdAt && results[i].get('objectId') != currentStoryId) {
						previousStory = results[i];
						break;
					}
				} else {
					previousStory = results[i];
					break;
				}
			}
			console.log('story to load: ', previousStory);
			kwargs.success.call(kwargs.scope, previousStory);
		},
		error:function(error) {
			console.error('Error fetching previous story!' + error);
			kwargs.error.call(kwargs.scope, error);
		}
	});
}

SVRModel.prototype.setCurrentlyReading = function(user, s) {
	//Save the story as the user's last story read
	if(user) {
		console.log('setting currentlyReading story');
		user.set('currentlyReading', s);
//		user.set('currentlyReadingTimestamp') = new Date();
		user.save();
	} else {
		console.error('Cannot save currently reading story without user');
	}
}

SVRModel.prototype.setFavorite = function(kwargs) {
	if(!kwargs.user || !kwargs.story) {
		console.error('SVRModel cannot change favorite status without story and user');
		kwargs.error.call(kwargs.scope, null);
	} else {
		var relation = kwargs.user.relation('favorites');
		if(kwargs.favorite) {
			relation.add(kwargs.story);	
		} else {
			relation.remove(kwargs.story);
		}
		kwargs.user.save();
		kwargs.success.call(kwargs.scope,kwargs.favorite);
	}
}

SVRModel.prototype.getRating = function(kwargs) {
	if(!kwargs.user || !kwargs.story) {
		console.error('SVRModel cannot get ratings status without story and user');
		kwargs.error.call(kwargs.scope, null);
	} else {
		var q = new Parse.Query(Rating);
		q.equalTo('user',kwargs.user);
		q.equalTo('story',kwargs.story);
		q.find({
			success:function(results) {
				console.log('SVRModel getRating success', results);
				kwargs.success.call(kwargs.scope,results[0]);
			}
		});
	}
}

SVRModel.prototype.setRating = function(kwargs) {
	if(!kwargs.user || !kwargs.story || kwargs.rating==undefined) {
		console.error('Cannot create a rating without user, story, and rating');
		kwargs.error.call(kwargs.scope);
	} else {
		//See if there's existing rating
		this.getRating({
			scope:this,
			user:kwargs.user,
			story:kwargs.story,
			success:function(ratingObj) {
				console.log('SVRModel setRating got an existing rating', ratingObj);
				if(ratingObj==undefined) {
					ratingObj = new Rating();
					ratingObj.set('user', kwargs.user);
					ratingObj.set('story',kwargs.story);
					ratingObj.set('rating',kwargs.rating);
					ratingObj.save();
				} else if (kwargs.rating != ratingObj.get('rating')) {
					ratingObj.set('rating', kwargs.rating);
					ratingObj.save();
				} else {
					console.log('rating already equal to target value');
				}
				kwargs.success.call(kwargs.scope, ratingObj);
			}
		});
	}	
}

SVRModel.prototype.getFavoriteStatus = function(kwargs) {
	var relation = kwargs.user.relation('favorites');
	var query = relation.query();
	console.log('checking for a story in the favorites relation: ', kwargs.story.id, kwargs.story.get('objectId'));
	query.get(kwargs.story.id, {
		success: function(list) {
			kwargs.success.call(kwargs.scope,true);
		}
	});

}

SVRModel.prototype.logout = function(kwargs) {
	console.log('SVRModel logout',kwargs);
	Parse.User.logOut();
	kwargs.success.call(kwargs.scope);
}

/***************** 
STORY VIEW 
***************/
function SVRWebView(kwargs) {
	console.log('SVRWebView constructor');
	this._model = kwargs.model;
	this._controller = kwargs.controller;
	this._navVisible = true;
	this._navIds = '#social-wrapper, #previous-button, #next-button, #user-info-wrapper, #site-logo, #story-info';
	this._fontSize = 1;
	this._scheme = 'light';
	
	$('#favorite-button').click($.proxy(this._controller._onFavoriteClick, this._controller));
	$('#up-button').click($.proxy(this._controller._onUpClick, this._controller));
	$('#down-button').click($.proxy(this._controller._onDownClick, this._controller));
	
	var p = $.proxy(this._controller._onPreviousClick, this._controller);
	var n = $.proxy(this._controller._onNextClick, this._controller);
	$('#previous-button').click(p);
	$('#next-button').click(n);
	$('#increase-font-button').click($.proxy(this._controller._onIncreaseFontClick, this._controller));
	$('#decrease-font-button').click($.proxy(this._controller._onDecreaseFontClick, this._controller));
	$('#light-button').click($.proxy(this._controller._onLightClick, this._controller));
	$('#dark-button').click($.proxy(this._controller._onDarkClick, this._controller));
	$('.logout').click($.proxy(this._controller._onLogoutClick, this._controller));
	
	$('#page-wrapper, #story-text p, header.h1, header.h2').swipe({
		//swipeRight: n,
		//swipeLeft: p,
		tap: $.proxy(this.toggleNav, this)
		//allowPageScroll: 'auto',
		//threshold: 250
	});
	
	if(this._controller.isMobile()) {
		$('body').css('width','550px');
		$('#page-wrapper, #story-text').css('margin','0');
		$('#page-wrapper').css('width','96%');
		$('#page-wrapper').css('padding','100px 2% 50px 2%');
		$('#story-text').css('width','100%');
		$('#story-text').css('padding','0');
		$('#story-text, #previous-button, #next-button').css('font-size','2em');
		$('#story-info').css('font-size','2em');
		//$('body').bind('touchmove', function(event) { event.preventDefault() }); //turn off zoom
		var s = '#social-wrapper, #previous-button, #next-button, #user-info-wrapper, #site-logo, #story-info, #settings-wrapper';
	//	$(s).css('font-size','2em');
	}
		
	return this;
}

SVRWebView.prototype.toggleNav = function() {
	console.log('SVRWebView toggling nav, target:', !this._navVisible, this, arguments);
	this._navVisible = !this._navVisible;
	var s = '#social-wrapper, #previous-button, #next-button, #user-info-wrapper, #site-logo, #story-info, #settings-wrapper';
	if(this._navVisible) {
		$(s).fadeIn();
	} else {
		$(s).fadeOut();	
	}
}

SVRWebView.prototype.setTheme = function(s) {
	if(this._theme != s) {
		this._theme = s;
		var c;
		var bg;
		switch(s) {
			case 'light':
				c = '#333333';
				bg = '#FCFCFC';
				break;
			case 'dark':
				c = '#EEEEEE';
				bg = '#030303';
				break;
			default:
				return;
		}
		$('#page-wrapper, #story-text').animate({
			color: c,
			backgroundColor: bg
		},500);
	}
}

SVRWebView.prototype.increaseFontSize = function() {
	this._fontSize += .1;
	$('#page-wrapper').css('font-size',this._fontSize + 'em');
	console.log('font-size changed', $('#page-wrapper'));
}

SVRWebView.prototype.decreaseFontSize = function() {
	this._fontSize -= .1;
	$('#page-wrapper').css('font-size',this._fontSize + 'em');	
	console.log('font-size changed', $('#page-wrapper'));
}

SVRWebView.prototype.setCurrentUser = function(u) {
	var username = this._model.get(u,'username');
	console.log('SVRWebView setCurrentUser', u, username);
	$('#user-info').html(username);
}

SVRWebView.prototype._formatDate = function(d) {
	var monthNames = [ "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December" ];
	var ds = monthNames[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
	return ds;
}

SVRWebView.prototype.setStory = function(s){
	var title = s.get('title');
	var author = s.get('author');
	$('#header-title').html(title);
	
	var t = title.length > 30 ? title.substring(title, 30) + "..." : title;	
	//var a = author.length > 10? author.substring(author, 10) + '...' : author;

	
	$('#info-title').html(t);
	$('#header-author').html(author);
	$('#story-text').html(this._model.get(s,'storyText'));
	$('#header-subtitle').html(this._model.get(s,'subtitle'));
	var publisher = this._model.get(s, 'publication');
	var publicationDate = this._model.get(s, 'publicationDate');
	console.log('publication info', publisher, publicationDate);
	if(publisher && publicationDate) {
		var d = this._formatDate(publicationDate);
		$('#publication-info').html('Originally published by ' + publisher + ' on ' + d +'.');
	} else if(publisher) {
		('#publication-info').html('Originally published by ' + publisher + '.');
	} else if(publicationDate) {
		var d = this._formatDate(publicationDate);
		$('#publication-info').html('Originally published on ' + d +'.');
	}
	
	$('#next-button').removeClass('disabled');
	$('#previous-button').removeClass('disabled');
	var p = $(window).scrollTop();
	window.scrollTo(0,0);
	if(!this._navVisible) {this.toggleNav();}

}

SVRWebView.prototype.setFavorite = function(favorite) {
	console.log('SVRWebView setFavorite', favorite);
	if(favorite) {$('#favorite-button').addClass('selected');} 
	else {$('#favorite-button').removeClass('selected');} 
}

SVRWebView.prototype.setRating = function(rating) {
	console.log('SVRWebView setRating', rating);
	switch(rating){
	case 5:
		$('#up-button').addClass('selected');
		$('#down-button').removeClass('selected');
		break;
	case 1:
		$('#down-button').addClass('selected');
		$('#up-button').removeClass('selected');
		break;
	default:
		$('#up-button').removeClass('selected');
		$('#down-button').removeClass('selected');
		break;
	}
}

/*function SVRiPhoneView (kwargs) {};
SVRiPhoneView.prototype = new SVRWebView();
SVRiPhoneView.prototype._constructor = function(kwargs) {
	$('#page-wrapper, #story-text p, header.h1, header.h2').swipe({
		//swipeRight: n,
		//swipeLeft: p,
		tap: $.proxy(this.toggleNav, this)
		//allowPageScroll: 'auto',
		//threshold: 250
	});
	
	if(this._controller.isMobile() || true) {
		$('body').css('width','550px');
		$('#page-wrapper, #story-text').css('margin','0');
		$('#page-wrapper').css('width','96%');
		$('#page-wrapper').css('padding','100px 2% 50px 2%');
		$('#story-text').css('width','100%');
		$('#story-text').css('padding','0');
		$('#story-text, #previous-button, #next-button').css('font-size','2em');
		$('#story-info').css('font-size','2em');
		//$('body').bind('touchmove', function(event) { event.preventDefault() }); //turn off zoom
		var s = '#social-wrapper, #previous-button, #next-button, #user-info-wrapper, #site-logo, #story-info, #settings-wrapper';
	//	$(s).css('font-size','2em');
	}
}*/

