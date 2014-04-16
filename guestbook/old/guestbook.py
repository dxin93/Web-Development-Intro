import os
import re
import sys
import cgi
import webapp2
import jinja2
import hashlib
import string
import random
import hmac
import urllib2
import json
from xml.dom import minidom

from google.appengine.api import memcache
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

art_key = db.Key.from_path('ASCIIChan', 'arts')
SECRET = 'imsosecret'

def console(s):
    sys.stderr.write('%s\n' % s)
    
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    return hashlib.sha256(name + pw + salt).hexdigest() + "," + salt

def valid_pw(name, pw, h):
    salt = h[::-1].split(',', 1)[0][::-1]
    return h == make_pw_hash(name, pw, salt)

def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    val = h[::-1].split('|',1)
    if len(val) == 2:
        val = val[1][::-1]
    else:
        return None
    if h == make_secure_val(val):
        return val

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class Art(db.Model):
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    coords = db.GeoPtProperty()
    
class MainPage(Handler):        
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        visits = 0
        visit_cookie_str = self.request.cookies.get('visits')
        if visit_cookie_str:
            cookie_val = check_secure_val(visit_cookie_str)
            if cookie_val:
                visits = int(cookie_val)

        visits += 1

        new_cookie_val = make_secure_val(str(visits))

        self.response.headers.add_header('Set-Cookie', 'visits=%s' % new_cookie_val)
        if visits > 12:
            self.write("You are the best ever!")
        else:
            self.write("You've been here %s times!" % visits)

class URLHandler(Handler):
    def get(self):
        self.write(json.dumps({"blah":["one", 2, 'th"r"ee']}))

IP_URL = "http://api.hostip.info/?ip="
def get_coords(ip):
    ip = "23.24.209.141"
    url = IP_URL + ip
    content = None
    try:
        content = urllib2.urlopen(url).read()
    except URLError:
        return

    if content:
        x = minidom.parseString(content)
        coords = x.getElementsByTagName('gml:coordinates')
        if coords and coords[0].childNodes[0].nodeValue:
            lan, lat = coords[0].childNodes[0].nodeValue.split(",")
            return db.GeoPt(lat, lan)
        
GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"

def gmaps_img(points):
    ###Your code here
    markers = '&'.join('markers=%s,%s' % (p.lat, p.lon) for p in points)
    return GMAPS_URL + markers

def top_arts(update = False):
    key = 'top'
    arts = memcache.get(key)
    if arts is None or update:
        arts = db.GqlQuery("SELECT * "
                           "FROM Art "
                           "WHERE ANCESTOR IS :1 "
                           "ORDER BY created DESC "
                           "LIMIT 10",
                           art_key)
        arts = list(arts)
        memcache.set(key, arts)
    return arts

class ASCIIHandler(Handler):
    def render_front(self, error = '', title = '', art = ''):
        arts = top_arts()
        
        points = filter(None, (a.coords for a in arts))
        img_url = None
        if points:
            img_url = gmaps_img(points)
        self.render('front.html', title = title, art = art,
                    error = error, arts = arts, img_url = img_url)

    def get(self):
        return self.render_front()

    def post(self):
        title = self.request.get('title')
        art = self.request.get('art')
        
        if title and art:
            p = Art(parent = art_key, title = title, art = art)
            coords = get_coords(self.request.remote_addr)
            if coords:
                p.coords = coords
                
            p.put()
            top_arts(True)

            self.redirect('/ascii')
        else:
            error = "we need both a title and some artwork!"
            self.render_front(error = error, title = title, art = art)
            
application = webapp2.WSGIApplication([('/', MainPage),
                                       ('/url', URLHandler),
                                       ('/ascii', ASCIIHandler)],
                                        debug=True)
