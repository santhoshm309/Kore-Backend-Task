from pyramid.config import Configurator
from pyramid.authorization import ACLAuthorizationPolicy


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    config.include('kore_task.cors.cors')
    config.add_cors_preflight_handler()

    config.include('pyramid_jwt')
    config.set_jwt_authentication_policy('secret',expiration=360)


    config.include('.models')
    config.include('.routes.routes')
    config.set_authorization_policy(ACLAuthorizationPolicy())

    config.scan()
    return config.make_wsgi_app()
