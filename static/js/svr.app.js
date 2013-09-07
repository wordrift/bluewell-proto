/***************
SVR Controller
****************/
function SVRController(kwargs) {
	console.log('SVRController constructor');
	if(!kwargs.userKey) {
		//TODO make this redirect to a login page, once that's setup
		window.location.replace('/');
	}
	this._userKey = kwargs.userKey; //Stored for conversion to google data store
	this._logins = kwargs.logins;
	this._story = null;
	this._favorite = false;
	this._rating = null;
	kwargs.controller = this;
	this._model = new SVRModel(kwargs);
	this._view = new SVRWebView({model:this._model, controller:this});
	this.loadNextStory();
}

SVRController.prototype.displayStory = function(s) {
	console.log('SVRController displayStory', this, s);
	this._story = s;
	this._view.setStory(s);
	
	if(s.userHistory) {
		h = s.userHistory;
		if(h.favorite) {
			this._favorite = h.favorite;
		} else {
			this._favorite = false;
		}
		this._view.setFavorite(this._favorite);
		
		if(h.rating) {
			this._rating = h.rating*1;
		} else {
			this._rating = null;
		}
		this._view.setRating(this._rating);
	}	
	this._model.updateStream({
		scope: this,
		userKey: this._userKey,
		data: {
			title: s.title,
			storyKey: s.key, 
			updatedAt: new Date()
		},
		success: function(results) {console.log('SVRController displayStory callback', results);},
		error: function(error) {}
	});

};

SVRController.prototype.loadNextStory = function(s, forceNew) {
	console.log('SVRController loadNextStory', arguments);
	//TODO Move all this logic into model, the controller should just be able to
	//ask for the next story and pass in: user/userKey, anchor story
	var includeAnchor = s ? false : true;
	anchorKey = s ? s.key : null;
	this._model.getNextStory({
		scope:this,
		data: {userKey: this._userKey, anchorKey:anchorKey, fullText:true},
		success:function(stories) {
			console.log('SVRController loadNextStory success', this);
			this.displayStory(stories[0]);
		},
		error:function(error) {
		}
	});
}

//Make this just ask the model for the previous story, moving all logic to model
SVRController.prototype.loadPreviousStory = function(s, forceNew) {
	anchorKey = s ? s.key : null;
	this._model.getPreviousStory({
		scope:this,
		data: {anchorKey:anchorKey, userKey:this._userKey, fullText:true},
		success: function(stories) {
			console.log('SVRController loadPreviousStory success: ', stories);
			this.displayStory(stories[0]);
		},
		error: function(error) {
		}
	});
}

SVRController.prototype._onFavoriteClick = function() {
	console.log('favorite clicked', this);
	s = this._story;
	this._favorite = !this._favorite;
	this._model.updateStream({
		scope: this,
		userKey: this._userKey,
		data: {
			title: s.title,
			storyKey: s.key, 
			updatedAt: new Date(),
			favorite: this._favorite
		},
		success: function(results) {
			console.log('SVRController displayStory callback', results);
			this._view.setFavorite(this._favorite);
		},
		error: function(error) {}
	});

	return;
}
SVRController.prototype._setRating = function(r) {
	s = this._story;
	this._rating = r;
	this._model.updateStream({
		scope: this,
		userKey: this._userKey,
		data: {
			title: s.title,
			storyKey: s.key, 
			updatedAt: new Date(),
			rating: this._rating
		},
		success: function(results) {
			console.log('SVRController displayStory callback', results);
			this._view.setRating(this._rating);
		},
		error: function(error) {}
	});
}
SVRController.prototype._onUpClick = function() {
	console.log('up clicked', this._rating);	
	if(!this._rating || this._rating!=5){
		console.log('setting rating to 5');
		this._setRating(5);
	} else {
		console.log('clearing rating');
		this._setRating(0);
	}
}

SVRController.prototype._onDownClick = function() {
	console.log('down clicked', this._rating);
	if(!this._rating || this._rating!=1){
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
	console.log('next clicked', this._story);
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
	return this;
}

SVRModel.prototype.get = function(object, property) {
	//console.log('SVR Model get ', property , object);
	var v = null;
	switch(property){
	case 'publication':
	case 'publisher':
		v = object['firstPub'][property];
		break;
	case 'publicationDate':
		v = object.firstPub.date;
		break;
	default:
		v = object[property];
		break;	
	}
	return v;
}

SVRModel.prototype.set = function(object, property, value) {
	switch(property){
	case 'publication':
	case 'publisher':
		object['firstPub'][property]  = value;
		break;
	case 'publicationDate':
		object.firstPub.date = value;
		break;
	default:
		object[property] = value;	
	}
	return object;
}

SVRModel.prototype._processStoryResults = function(results) {
	console.log('SVRModel _processStoryResults', results.length);
	var output = [];
	for (i in results) {
		console.log('SVRModel _processStoryResults', i, results[i], this.get(results[i], 'publicationDate'));
		var d = this._dateStringToObject(this.get(results[i],'publicationDate'));
		this.set(results[i], 'publicationDate', d);
		
		if(results[i]['userHistory']) {
			for (x in results[i]['userHistory']) {
				if(results[i]['userHistory'][x] == 'None'){
					results[i]['userHistory'][x] = null;
				}
			}
		}
		
	}
	return results;
}

SVRModel.prototype._dateStringToObject = function(s) {
	var bits = s.split(/\D/);
	var date = new Date(bits[0], --bits[1], bits[2]); //Decrement month since 0 = jan
	console.log('_dateStringToObject ', s, bits, date);
	return date;
}

SVRModel.prototype.getNextStory = function(kwargs) {
	console.log('SVRModel getNextStory', kwargs);
	//This is where you overwrite to return cached results
	//Since results caching is not implemented yet, just pass on the request
	if(kwargs.data.anchorKey) {
		kwargs.data.numPrevious = 0;
		kwargs.data.numAfter = 1;
		kwargs.data.includeAnchor = false;
	} else {
		kwargs.data.numPrevious = 0;
		kwargs.data.numAfter = 0;
		kwargs.data.includeAnchor = true;

	}
	this._loadStories(kwargs);
}

SVRModel.prototype.getPreviousStory = function(kwargs) {
	//TODO First check if we already have the previous story in our local store
	
	//Get stories from server by calling _loadStories(kwargs)
	kwargs.data.numPrevious = 1;
	kwargs.data.numAfter = 0;
	kwargs.data.includeAnchor = false;
	this._loadStories(kwargs);
}

SVRModel.prototype._loadStories = function(kwargs) {

	/*  Gets stories from the server
	data params:
		anchor - the story to use as a reference
		includeAnchor = whether the server should send the anchor story too
		fullText = do we return full text or not
		numPrevious = number to get before the anchor
		numAfter = number to get after the anchor
	*/
	

	console.log('SVRModel _loadStories', kwargs);
	$.ajax({
		type: 'GET',
		url:'/service/stream',
		data: kwargs.data,
		context: this,
		settings: {contentType:'application/json'}
	}).done(function(results) {
			console.log('_loadStories callback ', this);
			var stories = this._processStoryResults(results);
			kwargs.success.call(kwargs.scope, stories);
	});
	

	
}

SVRModel.prototype.updateStream = function(kwargs) {
	console.log('SVRModel updateStream', kwargs);
	url = '/service/stream';
	
	//TODO update local cache so updates can be batched
	//Right now, we just forward the requests on.
	d = JSON.stringify([kwargs.data]);

	$.ajax({
		type: "POST",
		url:url, 
		settings: {contentType:'application/json'},
		context: kwargs.scope,
		data: {userKey:kwargs.userKey, s:d}
	}).done(kwargs.success);
}

SVRModel.prototype.logout = function(kwargs) {
	console.log('SVRModel logout',kwargs);
	Parse.User.logOut();
	kwargs.success.call(kwargs.scope);
}

/***************** ***************** ***************** ***************** ***************** 
STORY VIEW 
*************** ***************** ***************** ***************** ***************** */
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
	//$('.logout').click($.proxy(this._controller._onLogoutClick, this._controller));
	
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
		
		$('#story-text').css({
			'width':'100%',
			'padding':'0'
		});			
		$('#site-logo, #user-info-wrapper, #settings-wrapper').css('display','none');
		$('#story-text, #previous-button, #next-button').css('font-size','2em');
		$('story-info').removeClass('left-tag').css({
			'font-size':'2em',
			'position':'fixed',
			'top':0,
			'left':0,
			'z-index':100
		});
		
		
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
	//$('#user-info').html(username);
}

SVRWebView.prototype._formatDate = function(d) {
	console.log('SVRWebView _formatDate',d);
	var monthNames = [ "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December" ];
	var ds = monthNames[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
	return ds;
}

SVRWebView.prototype.setStory = function(s){
	console.log('SVRWebView setStory', s);
	var m = this._model;
	var title = m.get(s, 'title');
	var author = m.get(s, 'creator'); //TODO Support multiple authors
	$('#header-title').html(title);
	
	var t = title.length > 30 ? title.substring(title, 30) + "..." : title;	
	//var a = author.length > 10? author.substring(author, 10) + '...' : author;

	
	$('#info-title').html(t);
	$('#header-author').html(author);
	$('#story-text').html(m.get(s, 'text'));
	$('#header-subtitle').html(m.get(s,'subtitle'));
	var publisher = m.get(s, 'publication');
	var publicationDate = m.get(s, 'publicationDate');
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
		console.log('rating does not match');
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

