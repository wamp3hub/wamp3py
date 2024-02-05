import logging


__super = logging.getLogger('wamp')


def debug(message, **kwargs):
    v = {'message': message, **kwargs}
    __super.debug(v)


def warn(message, **kwargs):
    v = {'message': message, **kwargs}
    __super.warning(v)


def error(message, **kwargs):
    v = {'message': message, **kwargs}
    __super.error(v)

