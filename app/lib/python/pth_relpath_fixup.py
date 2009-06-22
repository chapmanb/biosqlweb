"""
Changes any absolute paths in .pth files to be relative.  Also changes .egg-link files
"""
import sys
import os

def main():
    for path in sys.path:
        if not path:
            path = '.'
        if not os.path.isdir(path):
            continue
        for filename in os.listdir(path):
            filename = os.path.join(path, filename)
            if filename.endswith('.pth'):
                if not os.access(filename, os.W_OK):
                    print 'Cannot write .pth file %s, skipping' % filename
                else:
                    print 'Fixing up pth file %s' % filename
                    fixup_pth_file(filename)
            if filename.endswith('.egg-link'):
                if not os.access(filename, os.W_OK):
                    print 'Cannot write .egg-link file %s, skipping' % filename
                else:
                    fixup_egg_link(filename)
            if filename.endswith('.egg') and os.path.isfile(filename):
                print 'WARNING: %s is installed as a zip file' % filename
                print '         Libraries must be installed with easy_install --always-unzip'

def fixup_pth_file(filename):
    lines = []
    f = open(filename)
    for line in f:
        line = line.strip()
        if (not line or line.startswith('#') or line.startswith('import ')
            or os.path.abspath(line) != line):
            lines.append(line)
        else:
            new_value = make_relative_path(filename, line)
            print 'Rewriting path %s as %s' % (line, new_value)
            lines.append(new_value)
    f.close()
    f = open(filename, 'w')
    f.write('\n'.join(lines) + '\n')
    f.close()

def fixup_egg_link(filename):
    f = open(filename)
    link = f.read().strip()
    f.close()
    if os.path.abspath(link) != link:
        # Relative path
        return
    new_link = make_relative_path(filename, link)
    print 'Rewriting link %s in %s as %s' % (link, filename, new_link)
    f = open(filename, 'w')
    f.write(new_link)
    f.close()

def make_relative_path(source, dest, dest_is_directory=True):
    """
    Make a filename relative, where the filename is dest, and it is
    being referred to from the filename source.

        >>> make_relative_path('/usr/share/something/a-file.pth',
        ...                    '/usr/share/another-place/src/Directory')
        '../another-place/src/Directory'
        >>> make_relative_path('/usr/share/something/a-file.pth',
        ...                    '/home/user/src/Directory')
        '../../../home/user/src/Directory'
        >>> make_relative_path('/usr/share/a-file.pth', '/usr/share/')
        './'
    """
    source = os.path.dirname(source)
    if not dest_is_directory:
        dest_filename = os.path.basename(dest)
        dest = os.path.dirname(dest)
    dest = os.path.normpath(os.path.abspath(dest))
    source = os.path.normpath(os.path.abspath(source))
    dest_parts = dest.strip(os.path.sep).split(os.path.sep)
    source_parts = source.strip(os.path.sep).split(os.path.sep)
    while dest_parts and source_parts and dest_parts[0] == source_parts[0]:
        dest_parts.pop(0)
        source_parts.pop(0)
    full_parts = ['..']*len(source_parts) + dest_parts
    if not dest_is_directory:
        full_parts.append(dest_filename)
    if not full_parts:
        # Special case for the current directory (otherwise it'd be '')
        return './'
    return os.path.sep.join(full_parts)
                

if __name__ == '__main__':
    if sys.argv[1:] == ['doctest']:
        import doctest
        doctest.testmod()
    else:
        main()
