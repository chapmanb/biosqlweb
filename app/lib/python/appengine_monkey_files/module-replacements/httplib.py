from StringIO import StringIO
from google.appengine.api import urlfetch
import mimetools

HTTP_PORT = 80
HTTPS_PORT = 443

_method_map = {
    'GET': urlfetch.GET,
    'POST': urlfetch.POST,
    'HEAD': urlfetch.HEAD,
    'PUT': urlfetch.PUT,
    'DELETE': urlfetch.DELETE,
    }

class HTTPConnection(object):

    protocol = 'http'
    default_port = HTTP_PORT
    allow_truncated = False

    def __init__(self, host, port=None, strict=False):
        self.host = host
        self.port = port
        self.strict = strict
        self._method = self._url = self._body = None
        self.headers = []

    def request(self, method, url, body=None, headers=None):
        self._method = method
        self._url = url
        self._body = body
        if headers is None:
            headers = []
        elif hasattr(headers, 'items'):
            headers = headers.items()
        self.headers = headers

    def putrequest(self, request, selector, skip_host=False, skip_accept_encoding=False):
        self._method = request
        self._url = selector
        # FIXME: is it okay just to ignore skip_host and skip_accept_encoding

    def putheader(self, header, *lines):
        # FIXME: there's no good way to send multiple lines
        line = ', '.join(lines)
        self.headers.append((header, line))

    def endheaders(self):
        pass

    def set_debuglevel(self, level=None):
        # FIXME: do something?
        pass

    def send(self, data):
        if self._body is None:
            self._body = data
        else:
            self._body += data

    def getresponse(self):
        if self.port and self.port != self.default_port:
            host = '%s:%s' % (self.host, self.port)
        else:
            host = self.host
        url = '%s://%s%s' % (self.protocol, host, self._url)
        headers = dict(self.headers)
        import sys
        print >> sys.stderr, (
            'Calling urlfetch.fetch(url=%r, body=%r, method=%r, headers=%r, allow_truncated=%r)'
            % (url, self._body, self._method, headers, self.allow_truncated))
        resp = urlfetch.fetch(url, self._body, _method_map[self._method], headers, self.allow_truncated)
        return HTTPResponse(resp)
    
    def close(self):
        pass

class HTTPResponse(object):

    def __init__(self, fetch_response):
        self._fetch_response = fetch_response
        self.fp = StringIO(fetch_response.content)
        self.read = self.fp.read
        self.readline = self.fp.readline
        self.close = self.fp.close
        ## FIXME: what about __iter__, next, seek, tell?

    def getheader(self, name, default=None):
        return self._fetch_response.headers.get(name, default)

    def getheaders(self):
        return self._fetch_response.headers.items()

    @property
    def msg(self):
        msg = mimetools.Message(StringIO(''))
        for name, value in self._fetch_response.headers.items():
            msg[name] = value
        return msg

    ## FIXME: this is just a guess
    version = 'HTTP/1.1'

    @property
    def status(self):
        return self._fetch_response.status_code

    @property
    def reason(self):
        return responses.get(self._fetch_response.status_code, 'Unknown')

    

class HTTPSConnection(HTTPConnection):

    protocol = 'https'
    default_port = HTTPS_PORT

    def __init__(self, host, port=None, strict=False,
                 key_file=None, cert_file=None):
        if key_file is not None or cert_file is not None:
            raise NotImplemented(
                "key_file and cert_file arguments are not implemented")
        super(HTTPSConnection, self).__init__(
            host, port=port, strict=strict)



class HTTP:
    "Compatibility class with httplib.py from 1.5."

    _http_vsn = 10
    _http_vsn_str = 'HTTP/1.0'

    debuglevel = 0

    _connection_class = HTTPConnection

    def __init__(self, host='', port=None, strict=None):
        "Provide a default host, since the superclass requires one."

        # some joker passed 0 explicitly, meaning default port
        if port == 0:
            port = None

        # Note that we may pass an empty string as the host; this will throw
        # an error when we attempt to connect. Presumably, the client code
        # will call connect before then, with a proper host.
        self._setup(self._connection_class(host, port, strict))

    def _setup(self, conn):
        self._conn = conn

        # set up delegation to flesh out interface
        self.send = conn.send
        self.putrequest = conn.putrequest
        self.endheaders = conn.endheaders
        self.set_debuglevel = conn.set_debuglevel

        conn._http_vsn = self._http_vsn
        conn._http_vsn_str = self._http_vsn_str

        self.file = None

    def connect(self, host=None, port=None):
        "Accept arguments to set the host/port, since the superclass doesn't."

        if host is not None:
            self._conn._set_hostport(host, port)
        self._conn.connect()

    def getfile(self):
        "Provide a getfile, since the superclass' does not use this concept."
        return self.file

    def putheader(self, header, *values):
        "The superclass allows only one value argument."
        self._conn.putheader(header, '\r\n\t'.join(values))

    def getreply(self):
        """Compat definition since superclass does not define it.

        Returns a tuple consisting of:
        - server status code (e.g. '200' if all goes well)
        - server "reason" corresponding to status code
        - any RFC822 headers in the response from the server
        """
        try:
            response = self._conn.getresponse()
        except BadStatusLine, e:
            ### hmm. if getresponse() ever closes the socket on a bad request,
            ### then we are going to have problems with self.sock

            ### should we keep this behavior? do people use it?
            # keep the socket open (as a file), and return it
            self.file = self._conn.sock.makefile('rb', 0)

            # close our socket -- we want to restart after any protocol error
            self.close()

            self.headers = None
            return -1, e.line, None

        self.headers = response.msg
        self.file = response.fp
        return response.status, response.reason, response.msg

    def close(self):
        self._conn.close()

        # note that self.file == response.fp, which gets closed by the
        # superclass. just clear the object ref here.
        ### hmm. messy. if status==-1, then self.file is owned by us.
        ### well... we aren't explicitly closing, but losing this ref will
        ### do it
        self.file = None


class HTTPS(HTTP):
    """Compatibility with 1.5 httplib interface

    Python 1.5.2 did not have an HTTPS class, but it defined an
    interface for sending http requests that is also useful for
    https.
    """

    _connection_class = HTTPSConnection

    def __init__(self, host='', port=None, key_file=None, cert_file=None,
                 strict=None):
        # provide a default host, pass the X509 cert info

        # urf. compensate for bad input.
        if port == 0:
            port = None
        self._setup(self._connection_class(host, port, key_file,
                                           cert_file, strict))

        # we never actually use these for anything, but we keep them
        # here for compatibility with post-1.5.2 CVS.
        self.key_file = key_file
        self.cert_file = cert_file


class HTTPException(Exception):
    # Subclasses that define an __init__ must call Exception.__init__
    # or define self.args.  Otherwise, str() will fail.
    pass

class NotConnected(HTTPException):
    pass

class InvalidURL(HTTPException):
    pass

class UnknownProtocol(HTTPException):
    def __init__(self, version):
        self.args = version,
        self.version = version

class UnknownTransferEncoding(HTTPException):
    pass

class UnimplementedFileMode(HTTPException):
    pass

class IncompleteRead(HTTPException):
    def __init__(self, partial):
        self.args = partial,
        self.partial = partial

class ImproperConnectionState(HTTPException):
    pass

class CannotSendRequest(ImproperConnectionState):
    pass

class CannotSendHeader(ImproperConnectionState):
    pass

class ResponseNotReady(ImproperConnectionState):
    pass

class BadStatusLine(HTTPException):
    def __init__(self, line):
        self.args = line,
        self.line = line

# for backwards compatibility
error = HTTPException




CONTINUE = 100
SWITCHING_PROTOCOLS = 101
PROCESSING  = 102
OK = 200
CREATED = 201
ACCEPTED = 202
NON_AUTHORITATIVE_INFORMATION = 203
NO_CONTENT = 204
RESET_CONTENT = 205
PARTIAL_CONTENT = 206
MULTI_STATUS = 207
IM_USED = 226
MULTIPLE_CHOICES = 300
MOVED_PERMANENTLY = 301
FOUND = 302
SEE_OTHER = 303
NOT_MODIFIED = 304
USE_PROXY = 305
TEMPORARY_REDIRECT = 307
BAD_REQUEST = 400
UNAUTHORIZED = 401
PAYMENT_REQUIRED = 402
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
NOT_ACCEPTABLE = 406
PROXY_AUTHENTICATION_REQUIRED = 407
REQUEST_TIMEOUT = 408
CONFLICT = 409
GONE = 410
LENGTH_REQUIRED = 411
PRECONDITION_FAILED = 412
REQUEST_ENTITY_TOO_LARGE = 413
REQUEST_URI_TOO_LONG = 414
UNSUPPORTED_MEDIA_TYPE = 415
REQUESTED_RANGE_NOT_SATISFIABLE = 416
EXPECTATION_FAILED = 417
UNPROCESSABLE_ENTITY = 422
LOCKED = 423
FAILED_DEPENDENCY = 424
UPGRADE_REQUIRED = 426
INTERNAL_SERVER_ERROR = 500
NOT_IMPLEMENTED = 501
BAD_GATEWAY = 502
SERVICE_UNAVAILABLE = 503
GATEWAY_TIMEOUT = 504
HTTP_VERSION_NOT_SUPPORTED = 505
INSUFFICIENT_STORAGE = 507
NOT_EXTENDED = 510

responses = {
    100: 'Continue',
    101: 'Switching Protocols',

    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',

    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    306: '(Unused)',
    307: 'Temporary Redirect',

    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',

    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
}
