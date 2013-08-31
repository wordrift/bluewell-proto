import mysqlorm as db


def storyToDict(s, includeStoryText=True):
	d = {
		'id' :s.objectId,
		'title': s.title,
		'subtitle':s.subtitle,
		'author':s.author,
		'altmetricScore':s.altmetricScore,
		'publication':s.publication,
		'publicationDate':str(s.publicationDate),
		'url': s.url,
		'wordCount':s.wordCount
	}
	if includeStoryText:
		d['storyText'] = s.storyText
	return d

def val():
	print "valid"