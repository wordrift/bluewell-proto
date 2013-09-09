import json

def handleError(request, response, error):
	pass
	
def isNumber(n):
	try:
		float(n)
		return True
	except ValueError:
		return False	
		
'''
	Needs to handle: 
		- parameter not sent
		- parameter is not a valid value for the enforced format
'''

def getValidatedParam(request, response, param, default=None, enforceType=None):
	p = request.get(param)
	if p == None or p == '':
		vp = default
	else:	
		if enforceType:
			if enforceType == 'number':
				if not isNumber(p):
					handleError(request, response, error)
				else:
					vp = int(p)
			elif enforceType == 'bool':
				if p == '0' or p == 0 or p == 'false' or p == 'False':
					vp = False
				elif p == '1' or p == 1 or p == 'true' or p == 'True':
					vp = True
				else:
					handleError(request, response, error)
			elif enforceType == 'json':
				vp = json.loads(p)
			elif enforceType == 'datetime':
				vp = p
			elif enforceType == 'date':
				vp = p
			elif enforceType == 'time':
				vp = p
			elif enforceType == 'dict':
				vp = {}
				entries = unicode.split(p, ',')
				for e in entries:
					row = unicode.split(e, '=')
					vp[row[0]] = row[1]
			elif enforceType == 'list':
				vp = []
				entries = unicode.split(p, ',')
				for e in entries:
					vp.append(e)
		else:
			vp = p
	return vp	
	
def getParamString(request, response, param):
	pString = getValidatedParam(request, response, param, None, None)
	if not pString:
		pString = ''
	else:
		pString = '&{0}={1}'.format(param, pString)
	return pString