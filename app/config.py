APP_NAME = 'biosqlweb.config.middleware:make_app'
APP_ARGS = ({},)
APP_KWARGS = dict(
        biosql_biodb_name="gae_testing")
# You can overwrite these separately for different dev/live settings:
DEV_APP_ARGS = APP_ARGS
DEV_APP_KWARGS = APP_KWARGS
REMOVE_SYSTEM_LIBRARIES = ['webob']
