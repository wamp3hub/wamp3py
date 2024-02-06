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
    Cancel = 126
    Next = 125
    Publish = 1
    Accept = 0
    Yield = -125
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
    include: list[str]
    exclude: list[str]


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
    visitedRouters: list[str]


class Publication(PublishEvent):
    route: PublishRoute


class CallFeatures(eventFeatures):
    URI: str
    timeout: int


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
    visitedRouters: list[str]


class Invocation(CallEvent):
    route: CallRoute


class ReplyFeatures(eventFeatures):
    invocationID: str


class CancelEvent(EventProto):
    kind: typing.Literal[126]
    features: ReplyFeatures


def new_cancel_event(
    features: ReplyFeatures,
) -> CancelEvent:
    return {
        'ID': shared.new_id(),
        'kind': MessageKinds.Cancel.value,
        'features': features,
    }


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


class YieldEvent[T: typing.Any](EventProto):
    kind: typing.Literal[-125]
    features: ReplyFeatures
    payload: T


def new_yield_event[T: typing.Any](
    features: ReplyFeatures,
    payload: T,
) -> YieldEvent[T]:
    return {
        'ID': shared.new_id(),
        'kind': MessageKinds.Yield.value,
        'features': features,
        'payload': payload,
    }


class NextFeatures(eventFeatures):
    yieldID: str
    timeout: int


class NextEvent(EventProto):
    kind: typing.Literal[125]
    features: NextFeatures


def new_next_event(
    features: NextFeatures,
) -> NextEvent:
    return {
        'ID': shared.new_id(),
        'kind': MessageKinds.Next.value,
        'features': features,
    }


type StopEvent = CancelEvent


new_stop_event = new_cancel_event


type Event = (
    AcceptEvent
    | PublishEvent | Publication
    | CallEvent | Invocation | ReplyEvent | CancelEvent | ErrorEvent
    | YieldEvent | NextEvent | StopEvent
)


class options(Domain):
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

