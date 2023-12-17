import typing

from . import domain
from . import logger
from . import shared


class ProcedureToSubscribe[I](typing.Protocol):
    async def __call__(
        self,
        payload: I,
        /,
        event_id: str,
        event_features: domain.PublishFeatures,
        event_route: domain.PublishRoute,
    ) -> None:
        ...


def PublishEventEndpoint(procedure: ProcedureToSubscribe):
    async def execute(publish_event: domain.PublishEvent):
        try:
            await procedure(
                publish_event.payload,
                event_id=publish_event.ID,
                event_features=publish_event.features,
                event_route=publish_event.route,
            )
        except Exception as e:
            logger.error('during execute publish event endpoint', exception=repr(e))

    return execute


class ProcedureToRegister[I, O](typing.Protocol):
    async def __call__(
        self,
        payload: I,
        /,
        event_id: str,
        event_features: domain.CallFeatures,
        event_route: domain.CallRoute,
    ) -> O:
        ...


def CallEventEndpoint(procedure: ProcedureToRegister):
    async def execute(call_event: domain.CallEvent) -> domain.ReplyEvent | domain.ErrorEvent:
        reply_features = domain.ReplyFeatures(invocationID=call_event.ID)
        try:
            payload = await procedure(
                call_event.payload,
                event_id=call_event.ID,
                event_features=call_event.features,
                event_route=call_event.route,
            )
            return domain.ReplyEvent(features=reply_features, payload=payload)
        except domain.ApplicationError as e:
            return domain.ErrorEvent(
                features=reply_features, payload=domain.ErrorEventPayload(message=e.message),
            )
        except Exception as e:
            logger.error('during execute call event endpoint', exception=repr(e))
            return domain.ErrorEvent(
                features=reply_features, payload=domain.ErrorEventPayload(message=repr(e)),
            )

    return execute


class PieceByPiece:

    ID: str

    @property
    def active(self) -> bool:
        return not self._done

    def __init__(
        self,
        generator
    ):
        self.ID = shared.new_id()
        self._done = False
        self._generator = generator

    async def next(
        self,
        next_event: domain.NextEvent,
    ) -> domain.YieldEvent | domain.ErrorEvent:
        reply_features = domain.ReplyFeatures(invocationID=next_event.ID)
        self._done = True
        try:
            payload = await anext(self._generator)
            self._done = False
            return domain.YieldEvent(features=reply_features, payload=payload)
        except (StopIteration, StopAsyncIteration):
            logger.debug('generator done')
            return domain.ErrorEvent(
                features=reply_features, payload=domain.ErrorEventPayload(message='GeneratorExit'),
            )
        except domain.ApplicationError as e:
            return domain.ErrorEvent(
                features=reply_features, payload=domain.ErrorEventPayload(message=e.message),
            )
        except Exception as e:
            logger.error('during next', exception=repr(e))
            return domain.ErrorEvent(
                features=reply_features, payload=domain.ErrorEventPayload(message=repr(e)),
            )

    async def stop(self):
        raise NotImplemented()


def PieceByPieceEndpoint(procedure: ProcedureToRegister):
    async def execute(call_event: domain.CallEvent) -> PieceByPiece:
        generator = procedure(
            call_event.payload,
            event_id=call_event.ID,
            event_features=call_event.features,
            event_route=call_event.route,
        )
        return PieceByPiece(generator)

    return execute

