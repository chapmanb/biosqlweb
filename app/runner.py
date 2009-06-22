import os
here = os.path.dirname(__file__)
conf_file = os.path.join(here, 'config.py')
execfile(conf_file)

# This will define:
# APP_NAME, APP_ARGS, APP_KWARGS
# DEV_APP_ARGS, DEV_APP_KWARGS
# REMOVE_SYSTEM_LIBRARIES

import sys
sys.path = [path for path in sys.path if "site-packages" not in path]
import site
from google.appengine.ext.webapp.util import run_wsgi_app

for system_library in REMOVE_SYSTEM_LIBRARIES:
    _found_any = False
    for path in list(sys.path):
        if system_library in path:
            sys.path.remove(path)
            _found_any = True
    if not _found_any:
        #import logging
        #logging.warn('Could not remove system library %s from sys.path: %s'
        #             % (system_library, sys.path))
        pass
    for key in list(sys.modules):
        if key == system_library or key.startswith(system_library+'.'):
            del sys.modules[key]

cur_sys_path = list(sys.path)
site.addsitedir(os.path.join(here, 'lib', 'python'))
assert sys.path[:len(cur_sys_path)] == cur_sys_path, (
    "addsitedir() caused entries to be prepended to sys.path")
# Reverse entries so that the local libraries take precedence:
sys.path = sys.path[len(cur_sys_path):] + sys.path[:len(cur_sys_path)]
sys.path.insert(0, here)
sys_path = list(sys.path)

try:
    import appengine_monkey
except ImportError:
    pass

module_name, obj_name = APP_NAME.split(':', 1)
__import__(module_name)
module = sys.modules[module_name]
application = getattr(module, obj_name)
if os.environ['SERVER_SOFTWARE'].startswith('Development'):
    config_args = DEV_APP_ARGS
    config_kwargs = DEV_APP_KWARGS
else:
    config_args = APP_ARGS
    config_kwargs = APP_KWARGS
if config_args is not None or config_kwargs is not None:
    application = application(*(config_args or ()), **(config_kwargs or {}))
logging_ini = os.path.join(os.path.dirname(__file__), 'logging.ini')
if os.path.exists(logging_ini):
    import logging
    logging.fileConfig(logging_ini)

def main():
    sys.path[:] = sys_path
    run_wsgi_app(application)    

if __name__ == '__main__':
    main()
