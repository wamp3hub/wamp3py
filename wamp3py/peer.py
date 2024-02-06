import asyncio
import typing

from . import domain
from . import logger
from . import shared


class SerializationFail(Exception):
    """
    """


class ConnectionRestored(Exception):
    """
    """


class ConnectionClosed(Exception):
    """
    """


class DispatchError(Exception):
    """
    """


class Serializer(typing.Protocol):
    """
    Serializer must implement this methods
    """

    def encode(
        self,
        event: domain.Event,
    ) -> bytes:
        """
        """

    def decode(
        self,
        message: bytes | str,
    ) -> domain.Event:
        """
        """


class Transport(typing.Protocol):
    """
    Transport must implement this methods
    """

    async def read(self) -> domain.Event:
        """
        """

    async def write(self, event: domain.Event) -> None:
        """
        """        

    async def close(self) -> None:
        """
        """


class Peer:
    """
    Peer must be initialized inside running event loop!
    """

    def __init__(
        self,
        ID: str,
        transport: Transport,
    ):
        self.ID = ID
        self.transport = transport
        self.rejoin_events: shared.Observable[bool] = shared.Observable()
        self.incoming_publish_events: shared.Observable[domain.Publication] = shared.Observable()
        self.incoming_call_events: shared.Observable[domain.Invocation] = shared.Observable()
        self.pending_accept_events: shared.PendingMap[domain.AcceptEvent] = shared.PendingMap()
        self.pending_reply_events: shared.PendingMap[
            domain.ReplyEvent | domain.ErrorEvent | domain.YieldEvent
        ] = shared.PendingMap()
        self.pending_cancel_events: shared.PendingMap[domain.CancelEvent | domain.StopEvent] = shared.PendingMap()
        self.pending_next_events: shared.PendingMap[domain.NextEvent] = shared.PendingMap()
        self._loop = asyncio.get_running_loop()
        self._loop.create_task(
            self._read_incoming_events()
        )

    async def send(
        self,
        event: domain.Event,
        resend_count: int = 3,
    ):
        if resend_count < 0:
            raise DispatchError('resend count exceeded')

        try:
            pending_accept_event = self.pending_accept_events.new(event['ID'])
            await self.transport.write(event)
            logger.debug('event successfully sent', event=event)
            await pending_accept_event
            logger.debug('event successfully delivered', event=event)
        except Exception as e:
            logger.error('during send event', exception=repr(e))
            await self.send(event, resend_count - 1)

    async def _acknowledge(
        self,
        source: domain.Event,
        resend_count: int = 3,
    ):
        accept_event = domain.new_accept_event({'sourceID': source['ID']})
        for _ in range(resend_count):
            try:
                await self.transport.write(accept_event)
                break

            except Exception as e:
                logger.error('during acknowledge', exception=repr(e))

    async def _read_incoming_events(
        self,
    ):
        logger.debug('reading begin')
        while True:
            try:
                event = await self.transport.read()
            except ConnectionRestored:
                logger.debug('connection restored')
                await self.rejoin_events.next(True)
                continue
            except ConnectionClosed:
                logger.debug('connection closed')
                break

            logger.debug('new incoming event', event=event)

            try:
                if event['kind'] == domain.MessageKinds.Accept.value:
                    self.pending_accept_events.complete(event['features']['sourceID'], event)
                elif (
                    event['kind'] == domain.MessageKinds.Reply.value
                    or event['kind'] == domain.MessageKinds.Error.value
                    or event['kind'] == domain.MessageKinds.Yield.value
                ):
                    await self._acknowledge(event)
                    self.pending_reply_events.complete(event['features']['invocationID'], event)
                elif event['kind'] == domain.MessageKinds.Publish.value:
                    await self._acknowledge(event)
                    self._loop.create_task(
                        self.incoming_publish_events.next(event)
                    )
                elif event['kind'] == domain.MessageKinds.Call.value:
                    await self._acknowledge(event)
                    self._loop.create_task(
                        self.incoming_call_events.next(event)
                    )
                elif event['kind'] == domain.MessageKinds.Next.value:
                    await self._acknowledge(event)
                    self.pending_next_events.complete(event['features']['yieldID'], event)
                else:
                    logger.error('invalid event', event=event)
            except Exception as e:
                logger.error('during handle incoming event', event=event, exception=repr(e))

        await self.incoming_call_events.complete()
        await self.incoming_publish_events.complete()
        await self.rejoin_events.complete()
        logger.debug('reading end')

    async def close(
        self,
    ):
        await self.transport.close()
