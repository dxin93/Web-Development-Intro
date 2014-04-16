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

from main import MainPage, ThanksHandler
from rot13 import rot13fy, Rot13Handler
from signup import SignupHandler, WelcomeHandler, LoginHandler, LogoutHandler
from blog import BlogMainHandler, BlogNewpostHandler, BlogPostHandler, BlogJsonHandler, PostJsonHandler, FlushHandler

        
application = webapp2.WSGIApplication([('/', MainPage),
                                       ('/thanks', ThanksHandler),
                                       ('/rot13', Rot13Handler),
                                       ('/blog/signup', SignupHandler),
                                       ('/welcome', WelcomeHandler),
                                       ('/blog', BlogMainHandler),
                                       ('/blog/.json', BlogJsonHandler),
                                       ('/blog/newpost', BlogNewpostHandler),
                                       ('/blog/([0-9]+)', BlogPostHandler),
                                       ('/blog/([0-9]+).json', PostJsonHandler),
                                       ('/blog/login', LoginHandler),
                                       ('/blog/logout', LogoutHandler),
                                       ('/blog/flush', FlushHandler)],
                                      debug=True)


