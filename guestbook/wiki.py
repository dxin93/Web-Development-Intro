import os
import os.path
import re
import random
import hashlib
import hmac
import logging
import json
from datetime import datetime, timedelta
from string import letters

import webapp2
import jinja2

from google.appengine.api import memcache
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

SECRET = 'aowejf938haowao91`00u0=0-2380ia9euijf'

DEBUG = bool(os.environ['SERVER_SOFTWARE'].startswith('Development'))
if DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(s):
    return "%s|%s" % (s, hmac.new(SECRET, s).hexdigest())

def check_secure_val(h):
    val = h[::-1].split('|',1)
    if len(val) == 2:
        val = val[1][::-1]
    else:
        return None
    if h == make_secure_val(val):
        return val

def gray_style(lst):
    for n, x in enumerate(lst):
        if n % 2 == 0:
            yield x, ''
        else:
            yield x, 'gray'

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        params['gray_style'] = gray_style
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))
        self.can_post = self.user

        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'

    def notfound(self):
        self.error(404)
        self.write('<h1>404: Not Fount</h>Sorry, this page does not exist.')

def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    return hashlib.sha256(name + pw + salt).hexdigest() + "|" + salt

def valid_pw(name, pw, h):
    salt = h[::-1].split('|', 1)[0][::-1]
    return h == make_pw_hash(name, pw, salt)

def user_key(group = 'default'):
    return db.Key.from_path('users', group)

class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = user_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('username =', name).get()
        return u

    @classmethod
    def register(cls, name, pw):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = user_key(),
                    name = name,
                    pw_hash = pw_hash)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.password):
            return u

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")

def valid_username(username):
    return username and USER_RE.match(username)

def valid_password(password):
    return password and PASS_RE.match(password)

class Signup(Handler):
    def get(self):
        next_url = self.request.headers.get('referer', '/')
        self.render("signup.html", next_url = next_url)

    def post(self):
        have_error = False

        next_url = str(self.request.get('next_url'))
        if not next_url or next_url.startswith('/login'):
            next_url = '/'

        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')

        params = dict(username = self.username)

        if not valid_username(self.username):
            params['nameerror'] = "That's not a valid username."
            have_error = True
        elif User.by_name(self.username):
            params['nameerror'] = "That user already exists."
            have_error = True

        if not valid_password(self.password):
            params['passerror'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['verifyerror'] = "Your passwords didn't match."
            have_error = True

        if have_error:
            self.render('signup.html', **params)
        else:
            u = User.register(self.username, self.password)
            u.put()

            self.login(u)
            self.redirect(next_url)

class Login(Handler):
    def get(self):
        next_url = self.request.headers.get('referer', '/')
        self.render("login.html", next_url = next_url)

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        next_url = str(self.request.get('next_url'))
        if not next_url or next_url.startswith('/login'):
            next_url = '/'
            
        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect(next_url)
        else:
            self.render("login.html", error = "Invalid login")

class Logout(Handler):
    def get(self):
        next_url = self.request.headers.get('referer', '/')
        self.logout()
        self.redirect(next_url)

class Page(db.Model):
    content = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    @staticmethod
    def parent_key(path):
        return db.Key.from_path(path, 'pages')

    @classmethod
    def by_path(cls, path):
        q = cls.all()
        q.ancestor(cls.parent_key(path))
        q.order("-created")
        return q

    @classmethod
    def by_id(cls, page_id, path):
        return cls.get_by_id(page_id, cls.parent_key(path))
    
class EditPage(Handler):
    def get(self, path):
        if not self.user:
            self.redirect('/login')

        v = self.request.get('v')
        p = None
        if v:
            if v.isdigit():
                p = Page.by_id(int(v), path)

            if not p:
                return self.notfound()
        else:
            p = Page.by_path(path).get()

        self.render("edit.html", path = path, page = p)

    def post(self, path):
        if not self.user:
            self.error(400)
            return

        content = self.request.get('content')
        old_page = Page.by_path(path).get()

        if not (old_page or content):
            return
        elif not old_page or old_page.content != content:
            p = Page(parent = Page.parent_key(path), content = content)
            p.put()

        self.redirect(path)

class WikiPage(Handler):
    def get(self, path):
        v = self.request.get('v')
        p = None
        if v:
            if v.isdigit():
                p = Page.by_id(int(v), path)

            if not p:
                return self.notfound()
        else:
            p = Page.by_path(path).get()

        if p:
            self.render("page.html", page = p, path = path)
        else:
            self.redirect("/_edit" + path)

class HistoryPage(Handler):
    def get(self, path):
        q = Page.by_path(path)
        q.fetch(limit = 100)

        posts = list(q)
        if posts:
            self.render("history.html", path = path, posts = posts)
        else:
            self.redirect("/_edit" + path)

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'        
application = webapp2.WSGIApplication([('/signup', Signup),
                                       ('/login', Login),
                                       ('/logout', Logout),
                                       ('/_edit' + PAGE_RE, EditPage),
                                       ('/_history' + PAGE_RE, HistoryPage),
                                       (PAGE_RE, WikiPage)],
                                      debug=DEBUG)
