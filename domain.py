import enum
import typing

import shared


class MessageKinds(enum.auto):
    Call = 127
    Cancel = 126
    Next = 125
    Stop = 124
    Publish = 1
    Accept = 0
    Yield = -125
    Error = -126
    Reply = -127


CallProcedure = typing.Callable

PublishProcedure = typing.Callable


@shared.Domain
class eventFeatures:
    """
    """


@shared.Domain
class eventRoute:
    """
    """


@shared.Domain
class Event:
    ID: str


@shared.Domain
class AcceptFeatures(eventFeatures):
    sourceID: str


@shared.Domain
class AcceptEvent(Event):
    kind: int = MessageKinds.Accept
    features: AcceptFeatures


@shared.Domain
class PublishFeatures(eventFeatures):
    URI: str
    include: list[str] = shared.field(default_factory=list)
    exclude: list[str] = shared.field(default_factory=list)


@shared.Domain
class PublishRoute(eventRoute):
    publisherID: str
    subscriberID: str
    endpointID: str
    visitedRouters: list[str] = shared.field(default_factory=list)


@shared.Domain
class PublishEvent(Event):
    kind: int = MessageKinds.Publish
    features: PublishFeatures
    payload: typing.Any
    route: PublishRoute | None = None


@shared.Domain
class CallFeatures(eventFeatures):
    URI: str
    timeout: int


@shared.Domain
class CallRoute(eventRoute):
    callerID: str
    executorID: str
    endpointID: str
    visitedRouters: list[str] = shared.field(default_factory=list)


@shared.Domain
class CallEvent(Event):
    kind: int = MessageKinds.Call
    features: CallFeatures
    payload: typing.Any
    route: CallRoute | None = None


@shared.Domain
class ReplyFeatures(eventFeatures):
    invocationID: str


@shared.Domain
class ReplyEvent(Event):
    kind: int = MessageKinds.Reply
    features: ReplyFeatures
    payload: typing.Any


@shared.Domain
class ErrorEventPayload:
    code: str


@shared.Domain
class ErrorEvent(ReplyEvent):
    kind: int = MessageKinds.Error
    payload: ErrorEventPayload


@shared.Domain
class options:
    route: list[str] = shared.field(default_factory=list)


@shared.Domain
class RegisterOptions(options):
    ...


@shared.Domain
class SubscribeOptions(options):
    ...


@shared.Domain
class resource:
    ID: str
    URI: str
    authorID: str


@shared.Domain
class Registration(resource):
    options: RegisterOptions


@shared.Domain
class Subscription(resource):
    options: SubscribeOptions
