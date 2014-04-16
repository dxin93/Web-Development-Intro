import os
import cgi
import webapp2
import jinja2
import re

from google.appengine.api import users
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

from signup import Login, Logout, Signup
from wiki2 import EditPage, WikiPage, HistoryPage

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'        
application = webapp2.WSGIApplication([('/signup', Signup),
                                       ('/login', Login),
                                       ('/logout', Logout),
                                       ('/_edit' + PAGE_RE, EditPage),
                                       ('/_history' + PAGE_RE, HistoryPage),
                                       (PAGE_RE, WikiPage)],
                                      debug=True)


