import os
import imp
import sys

interactive = os.environ.get('SERVER_SOFTWARE') == 'Development/interactive'

class Missing(object):
    def __init__(self, name):
        self.name = name
    def __call__(self, *args, **kw):
        raise NotImplemented('%s is not implemented' % self.name)
    def __repr__(self):
        return '<Missing function %s>' % self.name
    @classmethod
    def patch(cls, module, name):
        if not hasattr(module, name):
            setattr(module, name, cls(module.__name__ + '.' + name))

def patch(module):
    def decorate(func):
        if interactive:
            # Shortcut patching for this case
            return func
        old_func = getattr(module, func.func_name, None)
        if getattr(old_func, 'patched', False):
            # This is a sign something is being re-patched
            return old_func
        setattr(module, func.func_name, func)
        func.orig_function = old_func
        func.patched = True
        return func
    return decorate

Missing.patch(os, 'utime')
Missing.patch(os, 'rename')
Missing.patch(os, 'unlink')
Missing.patch(os, 'open')

def can_access(path):
    try:
        if os.path.isdir(path):
            os.listdir(path)
            return True
        elif os.path.exists(path):
            return True
    except OSError:
        return False

sys.path = [p for p in sys.path if can_access(p)]

@patch(imp)
def acquire_lock():
    pass

@patch(imp)
def release_lock():
    pass

@patch(imp)
def load_module(fullname, fp, filename, etc):
    pass

@patch(imp)
def find_module(subname, path):
    for p in path:
        full_py = os.path.join(p, subname + '.py')
        full_dir = os.path.join(p, subname, '__init__.py')
        for full in full_py, full_dir:
            if os.path.exists(full):
                return open(full), full, None
    return None, '', None

@patch(imp)
def get_magic():
   return '\xb3\xf2\r\n'

@patch(imp)
def load_dynamic(name, pathname, file=None):
    # On GAE you can't load .so files, so this always just fails
    raise ImportError('You cannot import a dynamic library')

@patch(os)
def readlink(path):
    return path

# This is for the Mac pkg_resources when run in the SDK:
@patch(os)
def popen(*args, **kw):
    if not kw and args == ('/usr/bin/sw_vers',):
        # This is what pkg_resources uses to detect the version
        from StringIO import StringIO
        ## FIXME: somewhat lamely, all systems become 10.5.2
        return StringIO('ProductName:	Mac OS X\nProductVersion:	10.5.2\nBuildVersion:	000000')
    else:
        raise NotImplemented("os.open is not implemented")

# Again for Mac and pkg_resources:
@patch(os)
def uname():
    return ('AppEngine', 'appengine-host', '0.0.0', '#1', 'i386')

try:
    import pkg_resources
except ImportError:
    pass
else:
    if hasattr(os, '__loader__'):
        # This only seems to apply to the SDK
        pkg_resources.register_loader_type(type(os.__loader__), pkg_resources.DefaultProvider)

def get_file_dir(*parts):
    file_dir = os.path.dirname(__file__)
    if os.path.exists(os.path.join(file_dir, 'appengine_monkey_files')):
        file_dir = os.path.join(file_dir, 'appengine_monkey_files')
    if parts:
        file_dir = os.path.join(file_dir, *parts)
    return file_dir

def patch_modules():
    """
    Adds the module-replacements/ directory to the start of sys.path, and removes any modules that
    have already been loaded that instead should be loaded from module-replacements/

    (does not seem to work reliably for httplib -- see install_httplib())
    """
    if interactive:
        return
    repl_dir = get_file_dir('module-replacements')
    if repl_dir not in sys.path:
        sys.path.insert(0, repl_dir)
    for module in ['httplib', 'subprocess', 'cookielib', 'urllib', 'urllib2']:
        if (module in sys.modules
            and 'module-replacements' not in (getattr(sys.modules[module], '__file__', None) or '')):
            del sys.modules[module]

patch_modules()

def install_httplib():
    """
    Imports and patches the system httplib.

    Unlike patch_modules(), this imports the existing httplib and patches it in place.  This
    seems to be more reliable than modifying sys.path
    """
    if interactive:
        return
    # make extra sure some modules get the updated objects:
    for module in ['cookielib', 'urllib', 'urllib2']:
        if (module in sys.modules
            and 'module-replacements' not in (getattr(sys.modules[module], '__file__', None) or '')):
            del sys.modules[module]
    path_to_patched_httplib = get_file_dir('module-replacements', 'httplib.py')
    import httplib
    execfile(path_to_patched_httplib, httplib.__dict__)

if not interactive:
    import socket

    class SocketError(Exception):
        pass
    socket.error = SocketError

    @patch(socket)
    def _fileobject(socket_obj, mode='rb', bufsize=-1, close=False):
        ## FIXME: this is a fix for urllib2:1096, where for some reason it does this
        ## Why?  No idea.
        return socket_obj

if not interactive:
    import zipimport

    class ZipDirectoryCache(object):
        ## This is purely for setuptools/pkg_resources
        def __getitem__(self, path):
            # This must return something, but its contents will only be
            # inspected when pkg_resources tries to extract a resource
            # (e.g., when using resource_filename), which can't happen on
            # GAE.
            return {}

    zipimport._zip_directory_cache = ZipDirectoryCache()
