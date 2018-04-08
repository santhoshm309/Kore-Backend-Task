import logging
from pyramid.config import Configurator
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.events import NewRequest, subscriber, NewResponse
from waitress.utilities import logger
from webob.exc import HTTPBadRequest



def upload_size(event):
    log = logging.getLogger(__name__)
    r = event.request
    # Restrict upload size to 2 mb
    if r.content_length and  r.content_length > 1024*1024*3:
        raise HTTPBadRequest("Payload too large")

def log(event):
    log = logging.getLogger(__name__)
    r = event.response
    log.info(r.status)

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    config.include('kore_task.cors.cors')
    config.add_cors_preflight_handler()

    config.add_subscriber(upload_size, NewRequest)
    config.add_subscriber(log,NewResponse)

    config.include('.models')
    config.include('.routes.routes')
    
    config.scan()
    return config.make_wsgi_app()
