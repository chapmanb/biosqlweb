"""
This is experimental code to provide writable filesystem capability to
App Engine.  It can be enabled through importing, just with ``import
filesystem``.

This patches all the filesystem-related functions in the system.
Files that aren't in a Python package (under some entry in sys.path)
are handled using the :class:`Files` entity.

To start up, you have to build a basic filesystem, including
``mkdir('/')``.

File permissions are not implemented, and the atime property of files
is not implemented.  Most other things are, but practical usage is
likely to reveal flaws.

This is **very slow**.  Probably too slow to use.  This is the primary
reason why this is experimental.

Files only appear when they are closed.  Files that aren't closed
explicitly are lost, and while in the process of writing a file other
requests will not see the progress.
"""

from google.appengine.ext import db
from google.appengine.ext import gql
import site
import __main__
try:
    orig_open
except NameError:
    __main__.__builtins__['orig_open'] = open
import os
import sys
import tempfile
from datetime import datetime
import time
from google.appengine.ext import db
from appengine_monkey import patch
import logging
import itertools
from StringIO import StringIO

class Files(db.Model):
    basename = db.StringProperty()
    dir = db.StringProperty()
    path = db.StringProperty()
    content = db.BlobProperty()
    mtime_dt = db.DateTimeProperty()
    ctime_dt = db.DateTimeProperty()
    symlink = db.BooleanProperty()

    def follow_symlink(self, create=False):
        assert self.symlink
        assert self.content, (
            "Symlink from path %s is empty" % self.path)
        return self.__class__.get_file(self.content, create=create)

    @property
    def is_dir(self):
        return not self.basename

    @classmethod
    def get_file(cls, filename, create=False):
        filename = os.path.abspath(filename)
        query = cls.gql('WHERE path = :1', filename)
        files = query.fetch(1)
        if files:
            return files[0]
        if not create:
            return None
        if filename != '/':
            dir = cls.get_file(os.path.dirname(filename))
            if dir is None:
                raise IOError(2, 'No such file or directory: %r' % filename) # FIXME: better error message?
        file = cls(
            basename=os.path.basename(filename),
            dir=os.path.dirname(filename),
            path=filename,
            content='',
            mtime_dt=datetime.now(),
            ctime_dt=datetime.now(),
            symlink=False)
        return file

    @classmethod
    def listdir(cls, dir):
        dir = os.path.abspath(dir)
        files = cls.gql('WHERE dir = :1', dir)
        results = [file.basename for file in files]
        if not results:
            # Directory does not exist
            raise OSError(2, 'No such file or directory: %r' % dir)
        results.remove('') # remove the directory entry
        return results

    @classmethod
    def mkdir(cls, dir, recursive=False):
        dir = os.path.abspath(dir)
        f = cls.get_file(dir)
        if f is not None:
            raise OSError(17, 'File exists: %r' % dir)
        if dir != '/':
            parent = cls.get_file(os.path.dirname(dir))
            if parent is None:
                if recursive:
                    cls.mkdir(parent, recursive=True)
                else:
                    raise OSError(2, 'No such file or directory: %r' % dir)
        obj = cls.get_file(dir, create=True)
        obj.dir = dir
        obj.basename = ''
        obj.content = None
        obj.put()

    @classmethod
    def readlink(cls, path):
        path = os.path.abspath(path)
        obj = cls.get_file(path)
        if obj is None:
            raise OSError(2, 'No such file or directory: %r' % path)
        if not obj.symlink:
            raise OSError(22, 'Invalid argument: %r' % path)
        return obj.content

    @classmethod
    def remove(cls, path):
        path = os.path.abspath(path)
        obj = cls.get_file(path)
        if obj is None:
            raise OSError(2, 'No such file or directory: %r' % path)
        if obj.is_dir:
            raise OSError(21, 'Is a directory: %r' % path)
        db.delete(obj)

    @classmethod
    def rename(cls, src, dest):
        src = os.path.abspath(src)
        dest = os.path.abspath(dest)
        obj = cls.get_file(src)
        if obj is None:
            raise OSError(2, 'No such file or directory: %r' % src)
        dest_obj = cls.get_file(dest)
        if dest_obj is not None:
            if dest_obj.is_dir:
                raise OSError(16, 'Dest is a directory: %r' % dest)
            else:
                cls.remove(dest)
        obj.path = dest
        if obj.is_dir:
            obj.dir = dest
            obj.basename = ''
        else:
            obj.dir = os.path.dirname(dest)
            obj.basename = os.path.basename(dest)
        obj.put()

    @classmethod
    def rmdir(cls, path):
        path = os.path.abspath(path)
        obj = cls.get_file(path)
        if not obj.is_dir:
            raise OSError(20, 'Not a directory: %r' % path)
        if cls.listdir(path):
            raise OSError(16, 'Directory not empty: %r' % path)
        db.delete(obj)

    @classmethod
    def stat(cls, path):
        path = os.path.abspath(path)
        obj = cls.get_file(path)
        if obj is None:
            raise OSError(2, 'No such file or directory: %r' % path)
        return os.stat_result((
            0, # mode
            0, # inode
            0, # device
            1, # hard links
            0, # owner uid
            0, # gid
            len(obj.content or ''), # size
            0, # atime
            obj.mtime, # mtime
            obj.ctime, # ctime
            ))

    @classmethod
    def make_symlink(cls, src, dest):
        src = os.path.abspath(src)
        dest = os.path.abspath(dest)
        # FIXME: fail is src exists?
        obj = cls.get_file(src)
        if obj is None:
            return
        obj = cls.get_file(src, create=True)
        obj.symlink = True
        obj.content = dest
        obj.put()

    @classmethod
    def dump(cls):
        """Returns all the files in a text description
        """
        objs = list(cls.all())
        objs.sort(key=lambda obj: obj.path)
        lines = []
        for obj in objs:
            if obj.is_dir:
                lines.append('Dir:  %s' % obj.path)
            else:
                lines.append('File: %s  (%i bytes)' % (obj.path, len(obj.content or '')))
        return '\n'.join(lines)

    def mtime__get(self):
        return dt_to_timestamp(self.mtime_dt)

    def mtime__set(self, value):
        assert isinstance(value, (float, int)), (
            "Bad value for mtime: %r" % value)
        self.mtime_dt = datetime.fromtimestamp(float(value))

    mtime = property(mtime__get, mtime__set)

    def ctime__get(self):
        return dt_to_timestamp(self.ctime_dt)

    def ctime__set(self, value):
        assert isinstance(value, (float, int)), (
            "Bad value for ctime: %r" % value)
        self.ctime_dt = datetime.fromtimestamp(float(value))

    ctime = property(ctime__get, ctime__set)

def dt_to_timestamp(dt):
    if dt is None:
        return None
    return time.mktime(dt.timetuple())

def is_system_filename(filename):
    """True if this is a filename that exists on the system itself, like a file pointing to the uploaded code"""
    filename = os.path.abspath(filename)
    if filename.startswith('/usr'):
        # FIXME: I have to hack around this for some reason
        return True
    for path in sys.path:
        if filename.startswith(path):
            return True
    return False

def open(filename, mode='r', buffering=0):
    ## FIXME: totally ignore buffering?
    filename = os.path.abspath(filename)
    if is_system_filename(filename):
        return open.orig_function(filename, mode)
    create = mode.startswith('w') or mode.startswith('rw') or mode.startswith('a')
    fileobj = Files.get_file(filename, create=create)
    if fileobj is None:
        raise OSError(2, 'No such file or directory: %r' % filename)
    if fileobj.symlink:
        seen = [fileobj.path]
        while fileobj.symlink:
            fileobj = fileobj.follow_symlink(create=create)
            seen.append(fileobj.path)
            if fileobj.path in seen:
                raise IOError(
                    "Circular symlinks: %s" % '->'.join(seen))
    if fileobj.is_dir:
        raise OSError(21, 'Is a directory')
    return FileWrapper(fileobj, mode=mode)

open.orig_function = orig_open

def install_open():
    __main__.__builtins__['open'] = open

install_open()

@patch(os)
def listdir(dir):
    if is_system_filename(dir):
        return listdir.orig_function(dir)
    return Files.listdir(dir)

@patch(os)
def access(path, mode):
    if is_system_filename(path):
        if not access.orig_function:
            logging.warning("For some reason os.access wasn't present")
            if mode & os.W_OK:
                return False
            if mode & os.F_OK:
                if not os.path.exists(path):
                    return False
            ## FIXME: X_OK?
            return True
        return access.orig_function(path)
    return True

@patch(os)
def chmod(path, mode):
    if is_system_filename(path):
        return chmod.orig_function(path, mode)
    ## FIXME: this is kind of lame not to do anything...

@patch(os)
def chown(path, mode):
    if is_system_filename(filename):
        return chown.orig_function(path, mode)
    ## FIXME: also lame...

@patch(os)
def mkdir(dir, mode=None):
    if is_system_filename(dir):
        if mkdir.orig_function:
            return mkdir.orig_function(dir)
        else:
            ## FIXME: code?
            raise OSError("Permission denied to make directory %r" % dir)
    return Files.mkdir(dir)

@patch(os)
def makedirs(dir, mode=0777):
    if is_system_filename(dir):
        return makedirs.orig_function(dir)
    return Files.mkdir(dir, recursive=True)

@patch(os)
def readlink(path):
    if is_system_filename(path):
        return readlink.orig_function(path)
    return Files.readlink(path)

@patch(os)
def remove(path):
    if is_system_filename(path):
        return remove.orig_function(path)
    return Files.remove(path)

unlink = remove
os.unlink = unlink

@patch(os)
def removedirs(path):
    if is_system_filename(path):
        return removedirs.orig_function(path)
    path = os.path.abspath(path)
    rmdir(path)
    while 1:
        path = os.path.dirname(path)
        if path and path != '/':
            return
        try:
            rmdir(path)
        except OSError:
            return

@patch(os)
def rename(src, dest):
    if is_system_filename(src):
        return rename.orig_function(src, dest)
    if is_system_filename(dest):
        raise OSError('Dest %r is a system filename' % dest)
    Files.rename(src, dest)

@patch(os)
def renames(src, dest):
    if not os.path.exists(dest):
        makedirs(dest)
    rename(src, dest)

@patch(os)
def rmdir(path):
    if is_system_filename(path):
        return rmdir.orig_function(path)
    Files.rmdir(path)

@patch(os)
def stat(path):
    if is_system_filename(path):
        return stat.orig_function(path)
    return Files.stat(path)

@patch(os)
def symlink(src, dest):
    if is_system_filename(src):
        return symlink.orig_function(src, dest)
    if is_system_filename(dest):
        raise OSError('Dest %r is a system filename' % dest)
    Files.make_symlink(src, dest)

@patch(os)
def utime(path, times):
    if is_system_filename(path):
        ## FIXME: error properly
        raise OSError("Permission denied")
    fileobj = Files.get_file(path)
    if fileobj is None:
        raise OSError(2, "No file file or directory: %r" % path)
    if times is None:
        fileobj.mtime_dt = datetime.now()
        fileobj.put()
    else:
        atime, mtime = times
        fileobj.mtime = mtime
        fileobj.put()
        ## We're not tracking atime

@patch(os.path)
def exists(path):
    if is_system_filename(path):
        return exists.orig_function(path)
    obj = Files.get_file(path)
    return obj is not None

@patch(os.path)
def getmtime(path):
    if is_system_filename(path):
        return getmtime.orig_function(path)
    obj = Files.get_file(path)
    if obj is None:
        raise OSError(2, 'No such file or directory: %r' % path)
    return obj.mtime

@patch(os.path)
def getctime(path):
    if is_system_filename(path):
        return getctime.orig_function(path)
    obj = Files.get_file(path)
    if obj is None:
        raise OSError(2, 'No such file or directory: %r' % path)
    return obj.ctime

@patch(os.path)
def getsize(path):
    if is_system_filename(path):
        return getsize.orig_function(path)
    obj = Files.get_file(path)
    if obj is None:
        raise OSError(2, 'No such file or directory: %r' % path)
    return len(obj.content)

@patch(os.path)
def isdir(path):
    if is_system_filename(path):
        return isdir.orig_function(path)
    obj = Files.get_file(path)
    ## FIXME: follow symlinks?
    return obj is not None and obj.is_dir

@patch(os.path)
def isfile(path):
    if is_system_filename(path):
        return isfile.orig_function(path)
    obj = Files.get_file(path)
    ## FIXME: follow symlinks?
    return obj is not None and not obj.is_dir

@patch(os.path)
def islink(path):
    if is_system_filename(path):
        return islink.orig_function(path)
    obj = Files.get_file(path)
    return obj is not None and not obj.symlink

# These get tricky, because realpath searches above the sys.path
# paths, which causes the virtual fs operations to work, which causes
# problems.

@patch(os.path)
def realpath(filename):
    """Return the canonical path of the specified filename, eliminating any
symbolic links encountered in the path."""
    if not is_system_filename(filename):
        ## FIXME: this is bad:
        return os.path.abspath(filename)
    return _realpath(filename)

def _realpath(filename):
    if os.path.isabs(filename):
        bits = ['/'] + filename.split('/')[1:]
    else:
        bits = [''] + filename.split('/')

    for i in range(2, len(bits)+1):
        component = os.path.join(*bits[0:i])
        # Resolve symbolic links.
        if os.path.islink.orig_function(component):
            resolved = _resolve_link(component)
            if resolved is None:
                # Infinite loop -- return original component + rest of the path
                return os.path.abspath(os.path.join(*([component] + bits[i:])))
            else:
                newpath = os.path.join(*([resolved] + bits[i:]))
                return _realpath(newpath)

    return os.path.abspath(filename)

def _resolve_link(path):
    """Internal helper function.  Takes a path and follows symlinks
    until we either arrive at something that isn't a symlink, or
    encounter a path we've seen before (meaning that there's a loop).
    """
    paths_seen = []
    while islink(path):
        if path in paths_seen:
            # Already seen this path, so we must have a symlink loop
            return None
        paths_seen.append(path)
        # Resolve where the link points to
        resolved = os.readlink.orig_function(path)
        if not os.path.isabs(resolved):
            dir = os.path.dirname(path)
            path = os.path.normpath(os.path.join(dir, resolved))
        else:
            path = os.path.normpath(resolved)
    return path

_files_by_fileno = {}
_files_filenos = itertools.count(10000)

@patch(tempfile)
def mkstemp(suffix='', prefix='', dir='/tmp', text=False):
    fileno = _files_filenos.next()
    filename = os.path.join(dir, prefix + 'tmp-%s' % fileno + suffix)
    fileobj = Files.get_file(filename, create=True)
    fp = FileWrapper(fileobj, mode='rw')
    _files_by_fileno[fileno] = fp
    return (fileno, filename)

@patch(os)
def close(fd):
    try:
        fileobj = _files_by_fileno[fd]
    except KeyError:
        return close.orig_function(fd)
    fileobj.close()
    del _files_by_fileno[fd]

@patch(os)
def write(fd, s):
    try:
        fileobj = _files_by_fileno[fd]
    except KeyError:
        return write.orig_function(fd, s)
    fileobj.write(s)
    return len(s)

class FileWrapper(object):

    def __init__(self, fileobj, pos=0, mode='r'):
        self.fileobj = fileobj
        self.pos = pos
        mode = mode.replace('U', '').replace('t', '').replace('b', '')
        assert mode in ('r', 'w', 'rw', 'a'), (
            "Bad mode: %r" % mode)
        self.mode = mode
        if mode == 'a':
            self.pos = len(self.fileobj.content)
        self._closed = False

    def assert_state(self, mode):
        if not mode:
            pass
        elif mode == 'r':
            if self.mode != 'r' and self.mode != 'rw':
                raise AttributeError('Not a readable file (mode=%r)' % self.mode)
        elif mode == 'w':
            if self.mode != 'w' and self.mode != 'rw' and self.mode != 'a':
                raise AttributeError('Not a writable file (mode=%r)' % self.mode)
        if self._closed:
            raise ValueError(
                "I/O operation on closed file")
    
    def read(self, size=-1):
        self.assert_state('r')
        if size == -1:
            t = self.fileobj.content[self.pos:]
            self.pos = len(self.fileobj.content)
            return t
        else:
            t = self.fileobj.content[self.pos:self.pos+size]
            self.pos = min(len(self.fileobj.content), self.pos+size)
            return t

    def readline(self, size=-1):
        self.assert_state('r')
        parts = self.fileobj.content[self.pos:].split('\n', 1)
        if len(parts) == 2:
            next = parts[0] + '\n'
        else:
            next = parts[0]
        if size == -1 or size <= len(next):
            self.pos += len(next)
            return next
        else:
            self.pos += size
            return next[:size]

    def readlines(self, size=-1):
        self.assert_state('r')
        if size == -1:
            rest = self.fileobj.content[self.pos:]
            self.pos = len(self.fileobj.content)
        else:
            rest = self.fileobj.content[self.pos:self.pos+size]
            self.pos += size
        return rest.splitlines(True)

    def write(self, text):
        self.assert_state('w')
        self.fileobj.content = self.fileobj.content[:self.pos] + text + self.fileobj.content[self.pos+len(text):]
        self.pos += len(text)
        self.fileobj.mtime_dt = datetime.now()
    
    def writelines(self, lines):
        self.write(''.join(lines))

    def seek(self, pos):
        self.assert_state(None)
        self.pos = pos

    def tell(self):
        self.assert_state(None)
        return self.pos

    def close(self):
        self.fileobj.put()
        self._closed = True

    def flush(self):
        self.assert_state(None)
        self.fileobj.put()
