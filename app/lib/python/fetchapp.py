from google.appengine.api import urlfetch
from webob import Request
from webob.statusreasons import status_reasons

_method_map = {
    'GET': urlfetch.GET,
    'POST': urlfetch.POST,
    'HEAD': urlfetch.HEAD,
    'PUT': urlfetch.PUT,
    'DELETE': urlfetch.DELETE,
    }

def urlfetch_proxy(environ, start_response):
    req = Request(environ)
    resp = urlfetch.fetch(req.url, payload=req.body or None,
                          method=_method_map[req.method], headers=dict(req.headers))
    start_response('%s %s' % (resp.status_code, status_reasons.get(resp.status_code, 'Unknown')),
                   resp.headers.items())
    return [resp.content]


                   
