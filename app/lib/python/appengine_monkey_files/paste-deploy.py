#!/usr/bin/env python

CONF_FILE = 'development.ini'

import sys
import os
if getattr(sys, 'real_prefix', None):
    # This is a sign that a virtualenv python is being used, and that causes problems
    print >> sys.stderr, (
        "This appears to be a virtualenv python; please start dev_appserver.py with the system python interpreter")
    sys.exit(2)
if os.environ.get('PYTHONPATH'):
    print >> sys.stderr, (
        "$PYTHONPATH is set.  This may cause import problems; it is best to unset PYTHONPATH before starting the appserver")

import site
import wsgiref.handlers

try:
    here = os.path.dirname(__file__)

    # Don't get confused with non locally installed packages
    # XXX Could become more sophisticated
    sys.path = [path for path in sys.path if "site-packages" not in path]

    # The "src" path is added to ensure to find our main app (Problems under Windows)
    sys.path.insert(0, os.path.join(here, "src", "myapp"))

    # Test for correct site-packages directory, because if developed on
    # Windows we have different paths as everywhere else. And this has also
    # to work on the Google machine too!
    site_packages = os.path.join(here, 'lib', 'python2.5', 'site-packages')
    if not os.path.isdir(site_packages):
        site_packages = os.path.join(here, 'Lib', 'site-packages')

    site.addsitedir(site_packages)

    import appengine_monkey
    ## If you want to use httplib but get socket errors, you should uncomment this line:
    #appengine_monkey.install_httplib()

    ## This portion is the "Paste Deploy" part; it loads the application from a config file using
    ## Paste Deploy (http://pythonpaste.org/deploy/).  If you want to load your application in a
    ## different way (e.g., construct it in Python code) you can change these next three lines
    ## and just make sure that `app` is your WSGI application:
    CONF_FILE = 'config:' + os.path.join(here, CONF_FILE)
    from paste.deploy import loadapp
    app = loadapp(CONF_FILE)
except:
    import traceback
    print 'Content-type: text/plain'
    print
    print 'Error loading application:'
    traceback.print_exc(file=sys.stdout)
    exc_value = sys.exc_info()[1]
    if isinstance(exc_value, ImportError):
        print
        print 'sys.path:'
        for path in sys.path:
            print ' ', path

        print
        print "pth files"
        for fn in os.listdir(site_packages):
            if fn.lower().endswith('.pth'):
                content = open(os.path.join(site_packages, fn)).read()
                print fn, '->', content.strip()
else:
    def main():
        ## FIXME: set multiprocess based on whether this is the dev/SDK server
        wsgiref.handlers.BaseCGIHandler(sys.stdin, sys.stdout, sys.stderr, os.environ,
                                        multithread=False, multiprocess=False).run(app)

    if __name__ == '__main__':
        main()
