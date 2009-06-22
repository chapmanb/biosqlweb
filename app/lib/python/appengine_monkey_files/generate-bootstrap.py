"""
Call this like ``python generate-bootstrap.py``; it will
refresh the appengine-boot.py script
"""
import os
import subprocess
import re

here = os.path.dirname(os.path.abspath(__file__))
script_name = os.path.join(here, 'appengine-boot.py')
gae_script_name = os.path.join(here, 'appengine-homedir.py')

import virtualenv

## FIXME: should remove option --unzip-setuptools, --no-site-packages

EXTRA_TEXT = """
import shutil
import re

if sys.version[:3] != '2.5':
    print 'ERROR: you must run this script with python2.5'
    sys.exit(5)

def extend_parser(parser):
    parser.add_option(
        '--paste-deploy',
        dest='paste_deploy',
        action='store_true',
        help='Put into place the structure for a Paste Deploy (e.g., Pylons) application')
    parser.add_option(
        '--app-name',
        dest='app_name',
        metavar='APP_NAME',
        help='The application name (for app.yaml); defaults to the name of DEST_DIR')
    parser.add_option(
        '--app-yaml',
        dest='app_yaml',
        metavar='FILENAME',
        default=os.path.join(os.path.dirname(__file__), 'app.yaml.template'),
        help='File to use as the basis for app.yaml')
    parser.add_option(
        '--app-script',
        dest='app_script',
        metavar='SCRIPT',
        help='Script to run to run the application')
    parser.add_option(
        '--easy-install',
        dest='easy_install',
        metavar='PACKAGE',
        action='append',
        help='Install this package with easy_install immediately (can use more than once)')

def adjust_options(options, args):
    if not args:
        return # caller will raise error
    if not options.app_name:
        options.app_name = os.path.basename(args[0]).lower()
    options.unzip_setuptools = True
    if not options.easy_install:
        options.easy_install = []
    if options.paste_deploy:
        options.easy_install.extend(['PasteDeploy', 'PasteScript'])
        if not options.app_script:
            options.app_script = 'paste-deploy.py'
    elif not options.app_script:
        options.app_script = 'main.py'

def after_install(options, home_dir):
    src_dir = join(home_dir, 'src')
    mkdir(src_dir)
    logger.indent += 2
    fixup_distutils_cfg(options, home_dir)
    try:
        if sys.platform=="win32":
            script_dir = "Scripts"
        else:
            script_dir = "bin"
        packages = [os.path.dirname(os.path.abspath(__file__))] + list(options.easy_install)
        call_subprocess([os.path.abspath(join(home_dir, script_dir, 'easy_install'))] + packages,
                        cwd=home_dir,
                        filter_stdout=filter_python_develop,
                        show_stdout=False)
    finally:
        logger.indent -= 2
    install_app_yaml(options, home_dir)
    if options.paste_deploy:
        install_paste_deploy(options, home_dir)
    logger.notify('\\nRun "%s -m pth_relpath_fixup" before deploying'
                  % join(home_dir, 'bin', 'python'))
    logger.notify('Run "%s Package" to install new packages'
                  % join(home_dir, 'bin', 'easy_install'))

def fixup_distutils_cfg(options, home_dir):
    if sys.platform=="win32":
        distutils_path = os.path.join(home_dir, 'lib', 'distutils')
    else:
        distutils_path = os.path.join(home_dir, 'lib', 'python%s' % sys.version[:3], 'distutils')
    distutils_cfg = os.path.join(distutils_path, 'distutils.cfg')
    if os.path.exists(distutils_cfg):
        f = open(distutils_cfg)
        c = f.read()
        f.close()
    else:
        c = ''
    if 'zip_ok' in c:
        logger.notify('distutils.cfg already has zip_ok set')
        return
    f = open(distutils_cfg, 'a')
    f.write('\\n[easy_install]\\nzip_ok = False\\n')
    f.close()
    logger.info('Set zip_ok = False in distutils.cfg')

def install_app_yaml(options, home_dir):
    f = open(options.app_yaml, 'rb')
    c = f.read()
    f.close()
    c = c.replace('__APP_NAME__', options.app_name)
    c = c.replace('__APP_SCRIPT__', options.app_script)
    dest = os.path.join(home_dir, 'app.yaml')
    if os.path.exists(dest):
        logger.warn('Warning: overwriting %s' % dest)
    f = open(dest, 'wb')
    f.write(c)
    f.close()

def install_paste_deploy(options, home_dir):
    shutil.copyfile(os.path.join(os.path.dirname(__file__), 'paste-deploy.py'),
                    os.path.join(home_dir, 'paste-deploy.py'))
    dest = os.path.join(home_dir, 'development.ini')
    msg = 'Wrote paste-deploy.py'
    if os.path.exists(dest):
        logger.notify('Not overwriting development.ini')
    else:
        shutil.copyfile(os.path.join(os.path.dirname(__file__), 'development.ini.template'),
                        dest)
        msg += ' and development.ini'
    logger.notify(msg)

def filter_python_develop(line):
    if not line.strip():
        return Logger.DEBUG
    for prefix in ['Searching for', 'Reading ', 'Best match: ', 'Processing ',
                   'Moving ', 'Adding ', 'running ', 'writing ', 'Creating ',
                   'creating ', 'Copying ']:
        if line.startswith(prefix):
            return Logger.DEBUG
    return Logger.NOTIFY
"""

HOMEDIR_TEXT = """
import shutil
import re

if sys.version[:3] != '2.5':
    print 'ERROR: you must run this script with python2.5'
    sys.exit(5)

def extend_parser(parser):
    parser.add_option(
        '-g', '--gae',
        dest='gae_location',
        metavar='GOOGLE_APPENGINE_DIR',
        help='The location where the GAE SDK is located')
    parser.add_option(
        '--app-name',
        dest='app_name',
        metavar='APP_NAME',
        help='The application name (for app.yaml); defaults to the name of DEST_DIR')
    parser.add_option(
        '--package',
        metavar='PACKAGE_NAME',
        help='The package name for your application')
    parser.add_option(
        '--app-yaml',
        dest='app_yaml',
        metavar='FILENAME',
        default=os.path.join(os.path.dirname(__file__), 'app.yaml.template'),
        help='File to use as the basis for app.yaml (default %default)')
    parser.remove_option('--no-site-packages')

def adjust_options(options, args):
    if not args:
        return
    if not options.app_name:
        options.app_name = os.path.basename(args[0]).lower()
    if not options.package:
        options.package = options.app_name
    options.unzip_setuptools = True
    options.no_site_packages = True
    if not options.gae_location:
        print >> sys.stderr, (
            "You must provide the --gae option")
        sys.exit(2)

def after_install(options, home_dir):
    mkdir(join(home_dir, 'app'))
    logger.notify('Installing pip')
    logger.indent += 2
    try:
        if sys.platform == 'win32':
            script_dir = 'Scripts'
        else:
            script_dir = 'bin'
        call_subprocess([os.path.abspath(join(home_dir, script_dir, 'easy_install')), 'pip'],
                        filter_stdout=filter_ez_setup)
    finally:
        logger.indent -= 2
    logger.notify('Installing appengine-monkey')
    logger.indent += 2
    try:
        cmd = [os.path.abspath(join(home_dir, script_dir, 'python')),
               'setup.py', 'install', '--single-version-externally-managed',
               '--record=/tmp/appengine-tmp-record.txt',
               '--home', os.path.abspath(os.path.join(home_dir, 'app'))]
        call_subprocess(cmd,
                        filter_stdout=filter_ez_setup,
                        cwd=os.path.dirname(os.path.abspath(__file__)))
    finally:
        logger.indent -= 2
    logger.notify('Copying pkg_resources.py')
    import glob
    filename = glob.glob(os.path.join(home_dir, 'lib/python2.5/site-packages/*/pkg_resources.py'))[0]
    shutil.copy(filename, os.path.join(home_dir, 'app', 'lib', 'python', 'pkg_resources.py'))
    logger.notify('Setting up appengine structure')
    logger.indent += 2
    try:
        fixup_distutils_cfg(options, home_dir)
        install_app_yaml(options, home_dir)
        install_runner(options, home_dir)
        install_package(options, home_dir)
        install_sitecustomize(options, home_dir)
    finally:
        logger.indent -= 2
    logger.notify('')
    logger.notify('Run "%s/bin/pip install Package" to install new packages' % home_dir)
    logger.notify('To get access to your application from the command-line:')
    logger.notify('%s/bin/python' % home_dir)
    logger.notify('>>> import runner')
    logger.notify('>>> application = runner.application')

def fixup_distutils_cfg(options, home_dir):
    if sys.platform=="win32":
        distutils_path = os.path.join(home_dir, 'lib', 'distutils')
    else:
        distutils_path = os.path.join(home_dir, 'lib', 'python%s' % sys.version[:3], 'distutils')
    distutils_cfg = os.path.join(distutils_path, 'distutils.cfg')
    f = open(distutils_cfg, 'w')
    f.write('''\
# This makes installation work properly with pip
[easy_install]
zip_ok = False

[install]
home = %s
''' % join(os.path.abspath(home_dir), 'app'))
    f.close()
    logger.info('Set home in distutils.cfg')

def install_app_yaml(options, home_dir):
    f = open(options.app_yaml, 'rb')
    c = f.read()
    f.close()
    c = c.replace('__APP_NAME__', options.app_name)
    c = c.replace('__APP_SCRIPT__', 'runner.py')
    dest = os.path.join(home_dir, 'app', 'app.yaml')
    if os.path.exists(dest):
        logger.warn('Warning: overwriting %s' % dest)
    f = open(dest, 'wb')
    f.write(c)
    f.close()
    logger.info('Wrote %s' % dest)

def install_runner(options, home_dir):
    shutil.copyfile(os.path.join(os.path.dirname(__file__), 'homedir-runner.py'),
                    os.path.join(home_dir, 'app', 'runner.py'))
    logger.info('Created standard runner.py')
    conf = os.path.join(home_dir, 'app', 'config.py')
    if not os.path.exists(conf):
        f = open(conf, 'w')
        f.write('''\
APP_NAME = '%s.wsgiapp:make_app'
APP_ARGS = ()
APP_KWARGS = dict()
# You can overwrite these separately for different dev/live settings:
DEV_APP_ARGS = APP_ARGS
DEV_APP_KWARGS = APP_KWARGS
REMOVE_SYSTEM_LIBRARIES = ['webob']
''' % options.package)
        f.close()
        logger.info('Wrote config to %s' % conf)
    else:
        logger.warn('%s already exists, not overwriting' % conf)

def install_package(options, home_dir):
    pkg_dir = join(home_dir, 'app', options.package)
    mkdir(pkg_dir)
    init = join(pkg_dir, '__init__.py')
    if not os.path.exists(init):
        f = open(init, 'w')
        f.close()
    wsgiapp = join(pkg_dir, 'wsgiapp.py')
    if not os.path.exists(wsgiapp):
        f = open(wsgiapp, 'w')
        f.write('''\
def make_app():
    def application(environ, start_response):
        start_response('200 OK', [('content-type', 'text/html')])
        return ['hello world']
    return application
''')
        f.close()
        logger.info('Created hello-world app in %s' % pkg_dir)

def install_sitecustomize(options, home_dir):
    if sys.platform == 'win32':
        pkg_dir = os.path.join(home_dir, 'Lib')
        rel_home = '../'
    else:
        pkg_dir = os.path.join(home_dir, 'lib', 'python%s' % sys.version[:3])
        rel_home = '../../'
    sitecustomize = os.path.join(pkg_dir, 'sitecustomize.py')
    f = open(sitecustomize, 'w')
    f.write('''\
import tempfile, os, site, sys
home = os.path.normpath(os.path.join(os.path.dirname(__file__), __REL_HOME__))
app_path = os.path.join(home, 'app')
if app_path not in sys.path:
    sys.path.append(app_path)
lib_path = os.path.join(app_path, 'lib', 'python')
if lib_path not in sys.path:
    site.addsitedir(lib_path)

def activate_gae(location):
    if location not in sys.path:
        sys.path.append(location)
    for path in '../lib/antlr3', '../lib/yaml/lib', '../lib/webob', '../lib/django':
        path = os.path.join(location, path)
        if path not in sys.path:
            sys.path.append(path)
    from google.appengine.tools import dev_appserver
    from google.appengine.tools.dev_appserver_main import \
        DEFAULT_ARGS, ARG_CLEAR_DATASTORE, ARG_LOG_LEVEL, \
        ARG_DATASTORE_PATH, ARG_HISTORY_PATH
    gae_opts = DEFAULT_ARGS.copy()
    gae_opts[ARG_CLEAR_DATASTORE] = False
    gae_opts[ARG_DATASTORE_PATH] = os.path.join(tempfile.gettempdir(), 'wikistorage.datastore')
    gae_opts[ARG_HISTORY_PATH] = os.path.join(tempfile.gettempdir(), 'wikistorage.history')
    config = dev_appserver.LoadAppConfig(app_path, {})[0]
    dev_appserver.SetupStubs(config.application, **gae_opts)
    if not os.environ.get('APPLICATION_ID'):
        ## FIXME: should come up with a proper name:
        os.environ['APPLICATION_ID'] = 'miscapp'
    if not os.environ.get('SERVER_SOFTWARE'):
        os.environ['SERVER_SOFTWARE'] = 'Development/interactive'
    import runner

try:
    import google
    gae_location = os.path.dirname(google.__file__)
except ImportError:
    gae_location_fn = os.path.join(home, 'gae-location.txt')
    fp = open(gae_location_fn)
    gae_location = [line for line in fp.readlines()
                    if line.strip() and not line.strip().startswith('#')]
    if gae_location:
        gae_location = gae_location[0].strip()
        gae_location = os.path.expandvars(os.path.expanduser(gae_location))
    if not gae_location or not os.path.exists(gae_location):
        print >> sys.stderr, (
            "File %s doesn't contain a valid path" % gae_location_fn)
        gae_location = None
if gae_location:
    activate_gae(gae_location)
'''.replace('__REL_HOME__', repr(rel_home)))
    logger.info('Wrote GAE initialization in %s' % sitecustomize)

    fp = open(os.path.join(home_dir, 'gae-location.txt'), 'w')
    fp.write('''\
# This file contains the path to the GAE SDK:
%s
''' % options.gae_location)
    logger.info('Wrote SDK location (%s) to gae-location.txt' % options.gae_location)

    try:
        import Image
    except ImportError:
        logger.warn('Cannot find PIL')
    else:
        pil_pth = os.path.join(pkg_dir, 'site-packages', 'pil.pth')
        f = open(pil_pth, 'w')
        f.write(os.path.dirname(Image.__file__) + '\\n')
        f.close()
        logger.info('Wrote PIL location to %s' % pil_pth)
"""

def main():
    text = virtualenv.create_bootstrap_script(EXTRA_TEXT, python_version='2.5')
    if os.path.exists(script_name):
        f = open(script_name)
        cur_text = f.read()
        f.close()
    else:
        cur_text = ''
    print 'Updating %s' % script_name
    if cur_text == text:
        print 'No update'
    else:
        print 'Script changed; updating...'
        f = open(script_name, 'w')
        f.write(text)
        f.close()
    text = virtualenv.create_bootstrap_script(HOMEDIR_TEXT, python_version='2.5')
    if os.path.exists(gae_script_name):
        f = open(gae_script_name)
        cur_text = f.read()
        f.close()
    else:
        cur_text = ''
    print 'Updating %s' % gae_script_name
    if cur_text == text:
        print 'No update'
    else:
        print 'Script changed; updating...'
        f = open(gae_script_name, 'w')
        f.write(text)
        f.close()

if __name__ == '__main__':
    main()

