from __future__ import with_statement
from contextlib import closing
from datetime import datetime
from fb import *
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

DEBUG = True
FB_URL = 'https://graph.facebook.com/%s'
FQL_URL = 'https://api.facebook.com/method/fql.query?%s'
FBAPI_APP_ID = os.environ.get('FACEBOOK_APP_ID', '236467589732605')
FBAPI_APP_URI = os.environ.get('FACEBOOK_SECRET', 'fbb1c9f9335789cebc03ad654425d2d9')

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('EXAMPLEAPP_SETTINGS', silent=True)

@app.route('/')
def index():
    if request.args.get('code', None):
        return_val = fbapi_auth(request.args.get('code'))
        
        url = FB_URL % ('me?access_token=%s' % return_val[0])
        me = json.loads(urllib2.urlopen(url).read())
        
        url = FB_URL % ('%s?access_token=%s' % (FBAPI_APP_ID,return_val[0]))
        app = json.loads(urllib2.urlopen(url).read())
        
        url = FB_URL % ('me/likes?access_token=%s&limit=11' % return_val[0])
        likes = json.loads(urllib2.urlopen(url).read())
        
        url = FB_URL % ('me/friends?access_token=%s&limit=3' % return_val[0])
        friends = json.loads(urllib2.urlopen(url).read())
        
        url = FB_URL % ('me/photos?access_token=%s&limit=11' % return_val[0])
        photos  = json.loads(urllib2.urlopen(url).read())
        
        #POST_TO_WALL = "https://www.facebook.com/dialog/feed?redirect_uri=$redirect_url&display=popup&app_id=%s" % FBAPI_APP_ID 
        
        #QUERY = "query=%s&token=%s" % ("SELECT uid, name, is_app_user, pic_square FROM user WHERE uid in (SELECT uid2 FROM friend WHERE uid1 = me()) AND is_app_user = 1", return_val[0])
        #url = FQL_URL % QUERY
        
        return render_template('index.html', appId=FBAPI_APP_ID, token=return_val[0], likes=likes, friends=friends, photos=photos, app=app, me=me)
    else:
        print 'redirect to: ' + 'http://' + request.host
        return redirect(oauth_login_url(next_url='http://' + request.host))
         


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
