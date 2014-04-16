import os
import cgi
import webapp2
import jinja2
import re
import json
from datetime import datetime, timedelta
import math

from google.appengine.api import users
from google.appengine.ext import db
from handler import Handler

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

def user_key(group = 'default'):
    return db.Key.from_path('users', group)

class Page(db.Model):
    page_id = db.TextProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    
class EditPage(Handler):
    def get(self, page_id):
        version = int(float(self.request.get('v')))
        page_key = db.Key.from_path(page_id, 'history')
        user_cookie = self.read_secure_cookie('user_id')
        pages = db.GqlQuery("SELECT * "
                            "FROM Page "
                            "WHERE ANCESTOR IS :1 "
                            "ORDER BY created DESC",
                            page_key)
        pages = list(pages)

        if pages:
            content = pages[int(version)].content
        else:
            content = ""
            
        if user_cookie:
            key = db.Key.from_path('User', int(user_cookie), parent=user_key())
            user = db.get(key)
            if user:
                self.render("edit2.html", page = page_id, content = content)
            else:
                self.redirect("/login")
        else:
            self.redirect("/login")

    def post(self, page_id):
        page_key = db.Key.from_path(page_id, 'history')
        content = self.request.get('content')

        if not content:
            content = ""

        p = Page(parent = page_key, page_id = page_id, content = content)
        p.put()
        self.redirect(page_id)

class WikiPage(Handler):
    def get(self, page_id):
        version = self.request.get('v')
        if not version:
            version = 0
        page_key = db.Key.from_path(page_id, 'history')
        user_cookie = self.read_secure_cookie('user_id')
        pages = db.GqlQuery("SELECT * "
                            "FROM Page "
                            "WHERE ANCESTOR IS :1 "
                            "ORDER BY created DESC",
                            page_key)
        pages = list(pages)
        
        if pages:
            content = pages[int(version)].content
        else:
            content = ""

        if user_cookie:
            key = db.Key.from_path('User', int(user_cookie), parent=user_key())
            user = db.get(key)
            if user:
                if not pages:
                    self.redirect("/_edit" + page_id)
                else:
                    self.render("userwiki.html", page = page_id, content = content)
            else:
                if not pages:
                    self.redirect("/login")
                else:
                    self.render("anonwiki.html", page = page_id, content = content)
        elif not pages:
            self.redirect("/login")
        else:
            self.render("anonwiki.html", page = page_id, content = content)

class HistoryPage(Handler):
    def get(self, page_id):
        page_key = db.Key.from_path(page_id, 'history')
        user_cookie = self.read_secure_cookie('user_id')
        pages = db.GqlQuery("SELECT * "
                            "FROM Page "
                            "WHERE ANCESTOR IS :1 "
                            "ORDER BY created DESC",
                            page_key)
        pages = list(pages)

        if user_cookie:
            key = db.Key.from_path('User', int(user_cookie), parent=user_key())
            user = db.get(key)
            if user:
                if not pages:
                    self.redirect("/_edit" + page_id)
                else:
                    self.render("userhistory.html", source = page_id, pages = pages)
            else:
                if not pages:
                    self.redirect("/login")
                else:
                    self.render("anonhistory.html", source = page_id, pages = pages)
        elif not pages:
            self.redirect("/login")
        else:
            self.render("anonhistory.html", source = page_id, pages = pages)
