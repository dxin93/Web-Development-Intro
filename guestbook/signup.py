import os
import cgi
import webapp2
import jinja2
import re
import hashlib
import string
import random
import hmac

from google.appengine.api import users
from google.appengine.ext import db
from handler import Handler

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def user_key(group = 'default'):
    return db.Key.from_path('users', group)
    
def valid_username(username):
    return username and USER_RE.match(username)

def valid_password(password):
    return password and PASS_RE.match(password)

def valid_email(email):
    return not email or EMAIL_RE.match(email)

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    return hashlib.sha256(name + pw + salt).hexdigest() + "|" + salt

def valid_pw(name, pw, h):
    salt = h[::-1].split('|', 1)[0][::-1]
    return h == make_pw_hash(name, pw, salt)

def exist_username(username):
    q = db.GqlQuery("SELECT * FROM User "
                    "WHERE username='%s'" % username)
    return q.get()

class User(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    email = db.StringProperty(required = False)
    created = db.DateTimeProperty(auto_now_add = True)

    @classmethod
    def by_id(cls, uid):
        return cls.get_by_id(uid, parent = user_key())

    @classmethod
    def by_name(cls, name):
        u = cls.all().filter('username =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = user_key(),
                    username = name,
                    password = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.password):
            return u
        
class Signup(Handler):
    def render_signup(self, username="", email="", nameerror="", conflicterror = "", passerror="", verifyerror="", emailerror=""):
        self.render("signup2.html", username = username, email = email, nameerror = nameerror, conflicterror = conflicterror, passerror = passerror, verifyerror = verifyerror, emailerror = emailerror)

    def get(self):
        self.render_signup()

    def post(self):
        all_valid = True   
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        nameerror = ""
        conflicterror = ""
        passerror = ""
        verifyerror = ""
        emailerror = ""
        
        if not valid_username(username):
            nameerror = "That's not a valid username."
            all_valid = False
        elif User.by_name(username):
            conflicterror = "That user already exists."
            all_valid = False
        if not valid_password(password):
            passerror = "That wasn't a valid password."
            all_valid = False
        elif verify != password:
            verifyerror = "Your passwords didn't match."
            all_valid = False
        if not valid_email(email):
            emailerror = "That's not a valid email."
            all_valid = False

        if all_valid:
            u = User.register(username, password, email)
            u.put()
            
            self.login(u)
            self.redirect("/")
        else:
            self.render_signup(username, email, nameerror, conflicterror, passerror, verifyerror, emailerror)

class Login(Handler):
    def get(self):
        self.render("login.html")

    def post(self):
        all_valid = True
        
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)

        if u:
            self.login(u)
            self.redirect('/')
        else:
            self.render("login.html", error = "Invalid login")

class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect(self.request.referer)

