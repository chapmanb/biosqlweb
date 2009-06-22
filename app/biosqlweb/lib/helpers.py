"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password

from routes import url_for, redirect_to
from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers.html.tags import *
