import asyncio
import typing

from . import domain
from . import logger
from . import shared


class SerializationFail(Exception):
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
        self.incoming_publish_events = shared.Observable()
        self.incoming_call_events = shared.Observable()
        self.pending_accept_events = shared.PendingMap()
        self.pending_reply_events = shared.PendingMap()
        self.pending_next_events = shared.PendingMap()
        self.pending_cancel_events = shared.PendingMap()
        self._loop = asyncio.get_running_loop()
        self._logger = logger

    async def _safe_send(
        self,
        event: domain.Event,
    ):
        try:
            await self.transport.write(event)
        except Exception as e:
            self._logger.error('send', exception=repr(e))
            raise e

    async def send(
        self,
        event: domain.Event,
    ):
        pending_accept_event = self.pending_accept_events.new(event.ID)
        await self._safe_send(event)
        await pending_accept_event
        self._logger.debug('sent', event=event)

    async def _acknowledge(
        self,
        source: domain.Event,
    ):
        accept_event = domain.AcceptEvent(
            ID=shared.new_id(),
            features=domain.AcceptFeatures(sourceID=source.ID),
        )
        await self._safe_send(accept_event)

    async def _listen(
        self,
    ):
        self._logger.debug('listening begin')
        while True:
            event = await self.transport.read()
            self._logger.debug('new', event=event)
            if isinstance(event, domain.AcceptEvent):
                try:
                    self.pending_accept_events.complete(event.features.sourceID, event)
                except shared.PendingNotFound:
                    self._logger.error('pending accept event not found', event=event)
            elif isinstance(event, domain.ReplyEvent):
                await self._acknowledge(event)
                try:
                    self.pending_reply_events.complete(event.features.invocationID, event)
                except shared.PendingNotFound:
                    self._logger.error('pending reply event not found', event=event)
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
                    self._logger.error('pending next event not found', event=event)
            elif isinstance(event, domain.CancelEvent):
                await self._acknowledge(event)
                try:
                    self.pending_cancel_events.complete(event.features.invocationID, event)
                except shared.PendingNotFound:
                    self._logger.error('pending cancel event not found', event=event)
            else:
                self._logger.error('invalid event', event=event)
        self._logger.debug('listening end')

    def listen(
        self,
    ):
        self._loop.create_task(
            self._listen()
        )
        return asyncio.sleep(0)

    async def close(
        self,
    ):
        await self.transport.close()
