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
    async def execute(publish_event: domain.Publication):
        try:
            await procedure(
                publish_event['payload'],
                event_id=publish_event['ID'],
                event_features=publish_event['features'],
                event_route=publish_event['route'],
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
    async def execute(call_event: domain.Invocation) -> domain.ReplyEvent | domain.ErrorEvent:
        reply_features: domain.ReplyFeatures = {'invocationID': call_event['ID']}
        try:
            payload = await procedure(
                call_event['payload'],
                event_id=call_event['ID'],
                event_features=call_event['features'],
                event_route=call_event['route'],
            )
            return domain.new_reply_event(reply_features, payload)
        except domain.ApplicationError as e:
            return domain.new_error_event(reply_features, e)
        except Exception as e:
            logger.error('during execute call event endpoint', exception=repr(e))
            return domain.new_error_event(reply_features, domain.ApplicationError())

    return execute


class PieceByPiece:

    @property
    def active(self) -> bool:
        return not self._done

    def __init__(
        self,
        generator
    ):
        self.ID = shared.new_id()
        self._done = False
        self._generator: typing.AsyncGenerator = generator

    async def next(
        self,
        next_event: domain.NextEvent,
    ) -> domain.YieldEvent | domain.ErrorEvent:
        self._done = True
        reply_features: domain.ReplyFeatures = {'invocationID': next_event['ID']}
        try:
            payload = await anext(self._generator)
            self._done = False
            return domain.new_yield_event(reply_features, payload)
        except (StopIteration, StopAsyncIteration):
            logger.debug('generator done')
            return domain.new_error_event(reply_features, domain.GeneratorExit())
        except domain.ApplicationError as e:
            return domain.new_error_event(reply_features, e)
        except Exception as e:
            logger.error('during execute call event endpoint', exception=repr(e))
            return domain.new_error_event(reply_features, domain.ApplicationError())

    async def stop(
        self,
        __type: typing.Any = None,
        __value: typing.Any = None,
        __traceback: typing.Any = None
    ):
        if not self._done:
            self._done = True
            await self._generator.athrow(__type, __value, __traceback)


def PieceByPieceEndpoint(procedure: ProcedureToRegister):
    def execute(call_event: domain.Invocation) -> PieceByPiece:
        generator = procedure(
            call_event['payload'],
            event_id=call_event['ID'],
            event_features=call_event['features'],
            event_route=call_event['route'],
        )
        return PieceByPiece(generator)

    return execute
