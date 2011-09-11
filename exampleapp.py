from flask import Flask, request, redirect, render_template
import base64, hashlib, hmac
import simplejson as json
import urllib, urllib2
import os, os.path

FB_URL = 'https://graph.facebook.com/%s'
FQL_URL = 'https://api.facebook.com/method/fql.query?format=json&%s'
FBAPI_APP_ID = os.environ.get('FACEBOOK_APP_ID')

def oauth_login_url(preserve_path=True, next_url=None):
    fb_login_uri = "https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s" % (app.config['FBAPI_APP_ID'], request.url_root)
    if app.config['FBAPI_SCOPE']:
        fb_login_uri += "&scope=%s" % ",".join(app.config['FBAPI_SCOPE'])
    return fb_login_uri

def simple_dict_serialisation(params):
    return "&".join(map(lambda k: "%s=%s" % (k, params[k]), params.keys()))

def base64_url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip('=')

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
    result = urllib2.urlopen(url).read()
    
    return result

def fbapi_auth(code):
    
    params = {'client_id':app.config['FBAPI_APP_ID'],
              'redirect_uri':request.url_root,
              'client_secret':app.config['FBAPI_APP_SECRET'],
              'code':code}
    
    result = fbapi_get_string(path=u"/oauth/access_token?", params=params, encode_func=simple_dict_serialisation)
    pairs = result.split("&", 1)
    result_dict = {}
    for pair in pairs:
        (key, value) = pair.split("=")
        result_dict[key] = value
    return (result_dict["access_token"], result_dict["expires"])


def fbapi_get_application_access_token(id):
    token = fbapi_get_string(path=u"/oauth/access_token", params=dict(grant_type=u'client_credentials', client_id=id, client_secret=app.config['FB_APP_SECRET']), domain=u'graph')
    token = token.split('=')[-1]
    if not str(id) in token:
        current_app.logger.error('Token mismatch: %s not in %s', id, token)
    return token

def fql(fql, token, args=None):
    if not args: args = {}
    args["query"], args["format"], args["access_token"] = fql, "json", token
    return json.loads(urllib2.urlopen("https://api.facebook.com/method/fql.query?" + urllib.urlencode(args)).read())

def fb_call(call, args=None):
    return json.loads(urllib2.urlopen("https://graph.facebook.com/" + call + '?' + urllib.urlencode(args)).read())


app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_object('conf.Config')

@app.route('/')
def index():
    if request.args.get('code', None):
        return_val = fbapi_auth(request.args.get('code'))
        
        me = fb_call('me', args={'access_token': return_val[0]})
        app=fb_call(FBAPI_APP_ID, args={'access_token': return_val[0]})
        likes=fb_call('me/likes', args={'access_token': return_val[0], 'limit': 11})
        friends=fb_call('me/friends', args={'access_token': return_val[0], 'limit': 3})
        photos=fb_call('me/photos', args={'access_token': return_val[0], 'limit': 11})
        
        redir = request.url_root + 'close/'
        POST_TO_WALL = "https://www.facebook.com/dialog/feed?redirect_uri=%s&display=popup&app_id=%s" % (redir, FBAPI_APP_ID)
        
        app_friends = fql("SELECT uid, name, is_app_user, pic_square FROM user WHERE uid in (SELECT uid2 FROM friend WHERE uid1 = me()) AND is_app_user = 1", return_val[0])

        SEND_TO = 'https://www.facebook.com/dialog/send?redirect_uri=%s&display=popup&app_id=%s&link=%s' % (redir, FBAPI_APP_ID, request.url_root)

        return render_template('index.html', appId=FBAPI_APP_ID, token=return_val[0], likes=likes, friends=friends, photos=photos, app_friends=app_friends, app=app, me=me, POST_TO_WALL=POST_TO_WALL, SEND_TO=SEND_TO)
    else:
        return redirect(oauth_login_url(next_url=request.url_root))
    
@app.route('/close/')
def close():
    return render_template('close.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    if app.config.get('FBAPI_APP_ID') and app.config.get('FBAPI_APP_SECRET'):
        app.run(host='0.0.0.0', port=port)
    else:
        print 'Cannot start application without Facebook App Id and Secret set'
