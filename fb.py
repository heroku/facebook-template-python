from flask import request, current_app
import base64, hashlib, hmac
import simplejson as json
import urllib, urllib2
import os, os.path

def oauth_login_url(preserve_path=True, next_url=None):
    FBAPI_SCOPE = ['publish_actions','user_likes','user_photos','user_photo_video_tags']
    FBAPI_APP_ID = os.environ.get('FACEBOOK_APP_ID', '236467589732605')
    FBAPI_APP_URI = os.environ.get('FACEBOOK_SECRET', 'fbb1c9f9335789cebc03ad654425d2d9')
    
    if next_url:
        redirect_uri = next_url
    else:
        if preserve_path:
            #as the user is redirected through _top we need an url within facebook domain
            redirect_uri = FBAPI_APP_URI + request.path[1:] 
        else:
            redirect_uri = FBAPI_APP_URI
    
    fb_login_uri = "https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s" % (FBAPI_APP_ID, redirect_uri)
    if FBAPI_SCOPE:
        fb_login_uri += "&scope=%s" % ",".join(FBAPI_SCOPE)
    return fb_login_uri


def base64_url_decode(data):
    data = data.encode(u'ascii')
    data += '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data)


def base64_url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip('=')


def simple_dict_serialisation(params):
    return "&".join(map(lambda k: "%s=%s" % (k, params[k]), params.keys()))

def fbapi_get_string(path, domain=u'graph', params=None, access_token=None, encode_func=urllib.urlencode):
    """Make an API call"""
    if not params:
        params = {}
    params[u'method'] = u'GET'
    if access_token:
        params[u'access_token'] = access_token

    for k, v in params.iteritems():
        if hasattr(v, 'encode'):
            params[k] = v.encode('utf-8')

    url = u'https://' + domain + u'.facebook.com' + path
    params_encoded = encode_func(params)
    url = url + params_encoded
    current_app.logger.debug("FBAPI request: %s" % url)
    result = urllib2.urlopen(url).read()
    current_app.logger.debug("FBAPI response: %s" % result)
    
    return result

def fbapi_get_fql_multiquery(params=None, access_token=None, encode_func=urllib.urlencode, format="json"):
    """Make a multiquery FQL API call"""
    result = fbapi_get_json(path=u"/method/fql.multiquery?", domain=u"api", params=params, access_token=access_token, encode_func=encode_func)

    return result

def fbapi_auth(code):
    """
    returns (access_token, expires)
    """
    print 'redirect to: ' + 'http://' + request.host
    FBAPI_APP_URI = 'http://' + request.host
    FBAPI_APP_ID = os.environ.get('FACEBOOK_APP_ID', '236467589732605')
    FBAPI_APP_SECRET = os.environ.get('FACEBOOK_SECRET', 'fbb1c9f9335789cebc03ad654425d2d9')
    
    params = {'client_id':FBAPI_APP_ID,
              'redirect_uri':FBAPI_APP_URI,
              'client_secret':FBAPI_APP_SECRET,
              'code':code}
    
    result = fbapi_get_string(path=u"/oauth/access_token?", params=params, encode_func=simple_dict_serialisation)
    pairs = result.split("&", 1)
    result_dict = {}
    for pair in pairs:
        (key, value) = pair.split("=")
        result_dict[key] = value
    return (result_dict["access_token"], result_dict["expires"])


def fbapi_get_application_access_token(id):
    FB_APP_SECRET = os.environ.get('FB_APP_SECRET','fbb1c9f9335789cebc03ad654425d2d9')
    token = fbapi_get_string(path=u"/oauth/access_token", params=dict(grant_type=u'client_credentials', client_id=id, client_secret=FB_APP_SECRET), domain=u'graph')
    token = token.split('=')[-1]
    if not str(id) in token:
        current_app.logger.error('Token mismatch: %s not in %s', id, token)
    return token


