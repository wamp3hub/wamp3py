import enum
import typing

import shared


class MessageKinds(enum.auto):
    Call = 127
    Cancel = 126
    Next = 125
    Publish = 1
    Accept = 0
    Yield = -125
    Error = -126
    Reply = -127


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
    ID: str = shared.field(default_factory=shared.new_id)


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
class CancelEvent(Event):
    kind: int = MessageKinds.Cancel
    features: ReplyFeatures


@shared.Domain
class ReplyEvent(Event):
    kind: int = MessageKinds.Reply
    features: ReplyFeatures
    payload: typing.Any


@shared.Domain
class ErrorEventPayload:
    message: str


@shared.Domain
class ErrorEvent(ReplyEvent):
    kind: int = MessageKinds.Error
    payload: ErrorEventPayload


@shared.Domain
class YieldEvent(ReplyEvent):
    kind: int = MessageKinds.Yield


@shared.Domain
class NextFeatures(eventFeatures):
    yieldID: str
    timeout: int


@shared.Domain
class NextEvent(Event):
    kind: int = MessageKinds.Next
    features: NextFeatures


StopEvent = CancelEvent


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


@shared.Domain
class NewResourcePayload:
    ID: str = shared.field(default_factory=shared.new_id)
    URI: str
    options: RegisterOptions | SubscribeOptions


@shared.Domain
class NewGeneratorPayload:
    ID: str
