import os
import cgi
import webapp2
import jinja2
import re

from google.appengine.api import users
from google.appengine.ext import db

from handler import Handler

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)
        
def rot13fy(prerot13):
    postrot13 = ""
    for char in prerot13:
        if char.isalpha():
            if (ord(char) >= ord('a') and ord(char) <= ord('m')) or (ord(char) >= ord('A') and ord(char) <= ord('M')):
                postrot13 = postrot13 + chr(ord(char) + 13)
            else:
                postrot13 = postrot13 + chr(ord(char) - 13)
        else:
            postrot13 = postrot13 + char
            
    return postrot13

class Rot13Handler(Handler):
    def render_rot13(self, rot13input=""):
        self.render("rot13.html", rot13input = rot13input)
        
    def get(self):
        self.render_rot13()

    def post(self):
        rot13input = self.request.get('text')
        self.render_rot13(rot13fy(rot13input))
