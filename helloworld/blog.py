import os
import cgi
import webapp2
import jinja2
import re
import json
from datetime import datetime, timedelta
import math

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from handler import Handler

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = False)

def age_set(key, val):
    save_time = datetime.utcnow()
    memcache.set(key, (val, save_time))

def age_get(key):
    r = memcache.get(key)
    if r:
        val, save_time = r
        age = (datetime.utcnow() - save_time).total_seconds()
    else:
        val, age = None, 0

    return val, age

def add_post(post):
    post.put()
    get_posts(update = True)
    return str(post.key().id())

def blog_key(name = 'posts'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

def get_posts(update = False):
    key = 'top'
    
    posts, age = age_get(key)
    if posts is None or update:
        q = Post.all().order('-created').fetch(limit = 10)
        posts = list(q)
        age_set(key, posts)
    return posts, age

def age_str(age):
    s = 'queried %s seconds ago'
    age = int(age)
    if age == 1:
        s = s.replace('seconds', 'second')
    return s % age

class BlogMainHandler(Handler):
    def get(self):
        posts, age = get_posts()
        
        self.render("blog.html", posts = posts, age = age_str(age))

time_fmt = "%a %b %d %H:%M:%S %Y"

class BlogJsonHandler(Handler):
    def get(self):
        posts, age = get_posts()
        
        jsonlist = []
        for post in posts:
            entry = {'content': post.content,
                     'created': post.created.strftime(time_fmt),
                     'last_modified': post.last_modified.strftime(time_fmt),
                     'subject': post.subject}
            jsonlist.append(entry)
        self.render_json(jsonlist)

class PostJsonHandler(Handler):
    def get(self, post_id):
        post, age = age_get(post_id)
        if not post:
            self.error(404)
            return
        else:
            entry = {'content': post.content,
                     'created': post.created.strftime(time_fmt),
                     'last_modified': post.last_modified.strftime(time_fmt),
                     'subject': post.subject}
            self.render_json(entry)

class BlogNewpostHandler(Handler):
    def render_newpost(self, subject="", content="", error=""):
        self.render("newpost.html", subject=subject, content=content, error=error)

    def get(self):
        self.render_newpost()

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()
            top_posts(True)

            self.redirect("/blog/" + str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render_newpost(subject, content, error)

class BlogPostHandler(Handler):
    def get(self, post_id):
        post, age = age_get(post_id)
        
        if not post:
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)
            age_set(post_id, post)
            age = 0
            
        if not post:
            self.error(404)
            return
        
        self.render("post.html", post = post, age = age_str(age))

class FlushHandler(Handler):
    def get(self):
        memcache.flush_all()
        self.redirect("/blog")
