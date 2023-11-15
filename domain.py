import typing

from attrs import define


Domain = define(kw_only=True)


@Domain
class eventFeatures:
    """
    """


@Domain
class eventRoute:
    """
    """


@Domain
class Event:
    __public__ = ('id', 'kind',)

    id: str


@Domain
class AcceptFeatures(eventFeatures):
    __public__ = ('sourceID',)

    sourceID: str


@Domain
class AcceptEvent(Event):
    __public__ = ('id', 'kind', 'features',)

    kind: int = 0
    features: AcceptFeatures


@Domain
class PublishFeatures(eventFeatures):
    __public__ = ('uri', 'include', 'exclude',)

    uri: str
    include: typing.List[str]
    exclude: typing.List[str]


@Domain
class PublishRoute(eventRoute):
    __public__ = ('publisherID', 'subscriberID', 'endpointID', 'visitedRouters',)

    publisherID: str
    subscriberID: str
    endpointID: str
    visitedRouters: typing.List[str]


@Domain
class PublishEvent(Event):
    __public__ = ('id', 'kind', 'features', 'payload', 'route',)

    kind = 1
    features: PublishFeatures
    payload: typing.Any
    route: PublishRoute


@Domain
class CallFeatures(eventFeatures):
    __public__ = ('uri', 'timeout',)

    uri: str
    timeout: int


@Domain
class CallRoute(eventRoute):
    __public__ = ('callerID', 'executorID', 'endpointID', 'visitedRouters',)

    callerID: str
    executorID: str
    endpointID: str
    visitedRouters: typing.List[str]


@Domain
class CallEvent(Event):
    __public__ = ('id', 'kind', 'features', 'payload', 'route',)

    kind = 127
    features: CallFeatures
    payload: typing.Any
    route: CallRoute


@Domain
class ReplyFeatures(eventFeatures):
    __public__ = ('invocationID',)

    invocationID: str


@Domain
class ReplyEvent(Event):
    __public__ = ('id', 'kind', 'features', 'payload', 'route',)

    kind = -127
    features: ReplyFeatures
    payload: typing.Any


@Domain
class ErrorEventPayload:
    __public__ = ('code',)

    code: str


@Domain
class ErrorEvent(ReplyEvent):
    __public__ = ('id', 'kind', 'features', 'payload', 'route',)

    kind = -125
    payload: ErrorEventPayload


@Domain
class options:
    __public__ = ('route',)

    route: typing.List[str]


@Domain
class RegisterOptions(options):
    ...


@Domain
class SubscribeOptions(options):
    ...


@Domain
class resource:
    id: str
    uri: str
    authorID: str


@Domain
class Registration(resource):
    __public__ = ('id', 'uri', 'authorID', 'options',)

    options: RegisterOptions


@Domain
class Subscription(resource):
    __public__ = ('id', 'uri', 'authorID', 'options',)

    options: SubscribeOptions


event = CallEvent(
    id='id',
    features={
        'uri': 'wamp.router.register',
        'timeout': 100,
    },
    payload={

    },
    route={
        'callerID': 'callerID',
        'executorID': 'executorID',
        'endpointID': 'endpointID',
        'visitedRouters': ['visitedRouters'],
    },
)
print(event)
