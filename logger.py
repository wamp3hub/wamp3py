import logging


__super = logging.getLogger('wamp')


def log(message, **kwargs):
    v = {'message': message, **kwargs}
    __super.info(v)


def error(message, **kwargs):
    v = {'message': message, **kwargs}
    __super.error(v)

