import enum
import typing

from . import shared


class SomethingWentWrong(Exception):

    def __init__(
        self,
        message: str | None = None,
    ):
        self.message: str | None = message


class GeneratorExit(SomethingWentWrong):
    """
    """


class InvalidPayload(SomethingWentWrong):
    """
    """


class ApplicationError(SomethingWentWrong):
    """
    if you want to display error messages to user,
    you must derive your exception from this class.
    """


class MessageKinds(enum.Enum):
    Call = 127
    SubEvent = 125
    Publish = 1
    Accept = 0
    Undefined = -1
    Error = -126
    Reply = -127


class Domain(typing.TypedDict):
    ...


class eventFeatures(Domain):
    ...


class eventRoute(Domain):
    ...


class EventProto(Domain):
    ID: str


class AcceptFeatures(eventFeatures):
    sourceID: str


class AcceptEvent(EventProto):
    kind: typing.Literal[0]
    features: AcceptFeatures


def new_accept_event(
    features: AcceptFeatures,
) -> AcceptEvent:
    return {
        'ID': shared.new_id(),
        'kind': MessageKinds.Accept.value,
        'features': features,
    }


class PublishFeatures(eventFeatures):
    URI: str
    includeSubscribers: list[str]
    includeRoles: list[str]
    excludeSubscribers: list[str]
    excludeRoles: list[str]


class PublishEvent[T: typing.Any](EventProto):
    kind: typing.Literal[1]
    features: PublishFeatures
    payload: T


def new_publish_event[T: typing.Any](
    features: PublishFeatures, 
    payload: T,
) -> PublishEvent[T]:
    return {
        'ID': shared.new_id(),
        'kind': MessageKinds.Publish.value,
        'features': features,
        'payload': payload,
    }


class PublishRoute(eventRoute):
    publisherID: str
    subscriberID: str
    endpointID: str


class Publication(PublishEvent):
    route: PublishRoute


class CallFeatures(eventFeatures):
    URI: str
    timeout: int
    includeRoles: list[str]
    excludeRoles: list[str]


class CallEvent[T: typing.Any](EventProto):
    kind: typing.Literal[127]
    features: CallFeatures
    payload: T


def new_call_event[T: typing.Any](
    features: CallFeatures,
    payload: T,
) -> CallEvent[T]:
    return {
        'ID': shared.new_id(),
        'kind': MessageKinds.Call.value,
        'features': features,
        'payload': payload,
    }


class CallRoute(eventRoute):
    callerID: str
    executorID: str
    endpointID: str


class Invocation(CallEvent):
    route: CallRoute


class ReplyFeatures(eventFeatures):
    invocationID: str


class ReplyEvent[T: typing.Any](EventProto):
    kind: typing.Literal[-127]
    features: ReplyFeatures
    payload: T


def new_reply_event[T: typing.Any](
    features: ReplyFeatures,
    payload: T,
) -> ReplyEvent[T]:
    return {
        'ID': shared.new_id(),
        'kind': MessageKinds.Reply.value,
        'features': features,
        'payload': payload,
    }


class ErrorEventPayload(Domain):
    message: str


class ErrorEvent(EventProto):
    kind: typing.Literal[-126]
    features: ReplyFeatures
    payload: ErrorEventPayload


def new_error_event(
    features: ReplyFeatures,
    e: SomethingWentWrong,
) -> ErrorEvent:
    return {
        'ID': shared.new_id(),
        'kind': MessageKinds.Error.value,
        'features': features,
        'payload': {
            'message': e.__class__.__name__,
        },
    }



class SubEvent[T: typing.Any](EventProto):
    kind: typing.Literal[125]
    streamID: str
    payload: T


def new_subevent[T: typing.Any](
    streamID: str,
    payload: T,
) -> SubEvent[T]:
    return {
        'ID': shared.new_id(),
        'kind': MessageKinds.SubEvent.value,
        'streamID': streamID,
        'payload': payload,
    }


type Event = (
    AcceptEvent | PublishEvent | Publication | CallEvent | Invocation | ReplyEvent | ErrorEvent | SubEvent
)


class options(Domain):
    includeRoles: list[str]
    excludeRoles: list[str]
    route: list[str]


class RegisterOptions(options):
    ...


class SubscribeOptions(options):
    ...


class resource(Domain):
    ID: str
    URI: str
    authorID: str


class Registration(resource):
    options: RegisterOptions


class Subscription(resource):
    options: SubscribeOptions

