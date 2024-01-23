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

    def encode(
        self,
        event: domain.Event,
    ) -> bytes:
        """
        """

    def decode(
        self,
        data: bytes,
    ) -> domain.Event:
        """
        """


class Transport(typing.Protocol):

    async def read(self) -> domain.Event:
        """
        """

    async def write(self, event: domain.Event):
        """
        """        

    async def close(self):
        """
        """


class Peer:

    transport: Transport
    rejoin_events: shared.Observable[bool]
    incoming_publish_events: shared.Observable[domain.PublishEvent]
    incoming_call_events: shared.Observable[domain.CallEvent]
    pending_accept_events: shared.PendingMap
    pending_reply_events: shared.PendingMap
    pending_next_events: shared.PendingMap
    pending_cancel_events: shared.PendingMap

    def __init__(
        self,
        transport: Transport,
    ):
        self.transport = transport
        self.rejoin_events = shared.Observable()
        self.incoming_publish_events = shared.Observable()
        self.incoming_call_events = shared.Observable()
        self.pending_accept_events = shared.PendingMap()
        self.pending_reply_events = shared.PendingMap()
        self.pending_next_events = shared.PendingMap()
        self.pending_cancel_events = shared.PendingMap()
        self._loop = asyncio.get_running_loop()

    async def send(
        self,
        event: domain.Event,
        resend_count: int = 3,
    ):
        if resend_count < 0:
            raise DispatchError('resend count exceeded')

        try:
            pending_accept_event = self.pending_accept_events.new(event.ID)
            await self.transport.write(event)
            await pending_accept_event
            logger.debug('sent', event=event)
        except:
            self.send(event, resend_count - 1)

    async def _acknowledge(
        self,
        source: domain.Event,
        resend_count: int = 3,
    ):
        accept_event = domain.AcceptEvent(
            ID=shared.new_id(),
            features=domain.AcceptFeatures(sourceID=source.ID),
        )
        for _ in range(resend_count):
            try:
                await self.transport.write(accept_event)
                break
            except Exception as e:
                logger.error('during acknowledge', exception=repr(e))

    async def _listen(
        self,
    ):
        logger.debug('listening begin')
        while True:
            try:
                event = await self.transport.read()
            except ConnectionRestored:
                logger.debug('connection restored')
                self.rejoin_events.next(True)
                continue
            except ConnectionClosed:
                logger.debug('connection closed')
                break

            logger.debug('new', event=event)

            if isinstance(event, domain.AcceptEvent):
                try:
                    self.pending_accept_events.complete(event.features.sourceID, event)
                except shared.PendingNotFound:
                    logger.error('pending accept event not found', event=event)
            elif isinstance(event, domain.ReplyEvent):
                await self._acknowledge(event)
                try:
                    self.pending_reply_events.complete(event.features.invocationID, event)
                except shared.PendingNotFound:
                    logger.error('pending reply event not found', event=event)
            elif isinstance(event, domain.PublishEvent):
                await self._acknowledge(event)
                self._loop.create_task(
                    self.incoming_publish_events.next(event)
                )
            elif isinstance(event, domain.CallEvent):
                await self._acknowledge(event)
                self._loop.create_task(
                    self.incoming_call_events.next(event)
                )
            elif isinstance(event, domain.NextEvent):
                await self._acknowledge(event)
                try:
                    self.pending_next_events.complete(event.features.yieldID, event)
                except shared.PendingNotFound:
                    logger.error('pending next event not found', event=event)
            elif isinstance(event, domain.CancelEvent):
                await self._acknowledge(event)
                try:
                    self.pending_cancel_events.complete(event.features.invocationID, event)
                except shared.PendingNotFound:
                    logger.error('pending cancel event not found', event=event)
            else:
                logger.error('invalid event', event=event)

        self.incoming_call_events.complete()
        self.incoming_publish_events.complete()
        self.rejoin_events.complete()
        logger.debug('listening end')

    def listen(
        self,
    ):
        self._loop.create_task(
            self._listen()
        )
        asyncio.sleep(0)

    async def close(
        self,
    ):
        await self.transport.close()
