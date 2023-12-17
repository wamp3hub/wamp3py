import typing

import domain
import logger
import shared


type ProcedureToSubscribe = typing.Callable[[domain.PublishEvent], typing.Awaitable[None]]


def PublishEventEndpoint(procedure: ProcedureToSubscribe):
    async def execute(publish_event: domain.PublishEvent):
        try:
            await procedure(publish_event)
        except Exception as e:
            logger.error('during execute publish event endpoint', exception=repr(e))

    return execute


type ProcedureToRegister[T] = typing.Callable[[domain.PublishEvent], typing.Awaitable[T] | typing.AwaitableGenerator[T]]


def CallEventEndpoint(procedure: ProcedureToRegister):
    async def execute(call_event: domain.CallEvent) -> domain.ReplyEvent | domain.ErrorEvent:
        reply_features = domain.ReplyFeatures(invocationID=call_event.ID)
        try:
            payload = await procedure(call_event)
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
        generator = procedure(call_event)
        return PieceByPiece(generator)

    return execute

