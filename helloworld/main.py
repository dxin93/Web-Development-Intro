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

months = ['January',
          'February',
          'March',
          'April',
          'May',
          'June',
          'July',
          'August',
          'September',
          'October',
          'November',
          'December']

month_abbvs = dict((m[:3].lower(), m) for m in months)

def valid_month(month):
    if month:
        short_month = month[:3].lower()
        return month_abbvs.get(short_month)

def valid_day(day):
    if day and day.isdigit():
        day = int(day)
        if day > 0 and day <= 31:
            return day

def valid_year(year):
    if year and year.isdigit():
        year = int(year)
        if year > 1900 and year < 2020:
            return year

class MainPage(Handler):
    def render_main(self, error="", month="", day="", year=""):
        self.render("main.html", error = error, month = month, day = day, year = year)
                                
    def get(self):
        self.render_main()

    def post(self):
        user_month = self.request.get('month')
        user_day = self.request.get('day')
        user_year = self.request.get('year')

        month = valid_month(user_month)
        day = valid_day(user_day)
        year = valid_year(user_year)

        if not (month and day and year):
            self.render_main("That doesn't look valid to me, friend.", user_month, user_day, user_year)
        else:
           self.redirect("/thanks")

class ThanksHandler(Handler):
    def get(self):
        self.render("thanks.html")
    


