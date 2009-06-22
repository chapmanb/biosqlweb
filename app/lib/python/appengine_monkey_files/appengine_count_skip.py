#!/usr/bin/env python
import yaml
import optparse
import sys
import os
import re

parser = optparse.OptionParser(
    usage='%prog BASE_APPENGINE_DIR')
parser.add_option(
    '-c', '--csv',
    action='store_true',
    help='Output in CSV format')

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    options, args = parser.parse_args(args)
    if not args:
        parser.error('You must give a base directory argument')
    base_dir = args[0]
    app_yaml = os.path.join(base_dir, 'app.yaml')
    if not os.path.exists(app_yaml):
        print 'Error: %s does not exist' % app_yaml
        sys.exit(2)
    fp = open(app_yaml)
    parsed = yaml.load(fp)
    fp.close()
    skip_files = parsed.get('skip_files', '')
    complete_regex = re.compile(skip_files)
    lines = [line.strip().strip('|')
             for line in skip_files.splitlines()
             if line.strip()]
    summary = {}
    files = {}
    order = []
    for dirpath, dirnames, filenames in os.walk(base_dir):
        if dirpath.startswith('./'):
            dirpath = dirpath[2:]
        elif dirpath == '.':
            dirpath = ''
        for filename in filenames:
            full = os.path.join(dirpath, filename)
            order.append(full)
            for match in lines:
                if re.search(match, full):
                    files[full] = match
                    count = 0
                    break
            else:
                if complete_regex.match(full):
                    count = 0
                    files[full] = 'FULL REGEX!'
                else:
                    count = 1
                    files[full] = None
            place = os.path.dirname(full)
            while 1:
                summary[place] = summary.get(place, 0)+count
                if not place:
                    break
                place = os.path.dirname(place)
        for dirname in list(dirnames):
            full = os.path.join(dirpath, dirname)
            order.append(full)
            for match in lines:
                if re.search(match, full):
                    files[full] = match
                    dirnames.remove(dirname)
                    break
            else:
                files[full] = None
                
    order.sort(key=lambda x: x.lower().split('/'))
    for name in order:
        if options.csv:
            print '%s,%s,%s' % (name, summary.get(name, ''), files[name] or '')
        else:
            s = summary.get(name, 0)
            if s:
                s = '%3i' % s
            else:
                s = '   '
            print '%s%s%s %s' % (name, ' '*(50-len(name)), s, files[name] or '')
    

if __name__ == '__main__':
    main()
