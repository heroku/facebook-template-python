import os, os.path
import urlparse

class Config(object):
    DEBUG = True
    TESTING = False
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')

    FBAPI_SCOPE = ['publish_actions','user_likes','user_photos','user_photo_video_tags']
    FBAPI_APP_ID = os.environ.get('FACEBOOK_APP_ID', '148166728607324')
    FBAPI_APP_SECRET = os.environ.get('FACEBOOK_SECRET', '597ddc11297f085822f258eb177312df')
    FBAPI_APP_URI = 'http://127.0.0.1:5000/'

