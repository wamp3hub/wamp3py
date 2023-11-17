import asyncio
import typing

import domain
import shared.stream


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
    incoming_publish_events: shared.Stream
    incoming_call_events: shared.Stream
    pending_accept_events: shared.PendingMap
    pending_reply_events: shared.PendingMap
    pending_next_events: shared.PendingMap
    pending_cancel_events: shared.PendingMap

    def __init__(
        self,
        transport: Transport,
    ):
        self.transport = transport
        self.incoming_publish_events = shared.Stream()
        self.incoming_call_events = shared.Stream()
        self.pending_accept_events = shared.PendingMap()
        self.pending_reply_events = shared.PendingMap()
        self.pending_next_events = shared.PendingMap()
        self.pending_cancel_events = shared.PendingMap()
        self._loop = asyncio.get_running_loop()

    async def _safe_send(
        self,
        event: domain.Event,
    ):
        await self.transport.write(event)

    async def send(
        self,
        event: domain.Event,
    ):
        pending_accept_event = self.pending_accept_events.new(event.ID)
        await self._safe_send(event)
        await pending_accept_event

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
        while True:
            event = await self.transport.read()
            match event:
                case domain.AcceptEvent():
                    await self._acknowledge(event)
                    try:
                        self.pending_accept_events.complete(event.features.sourceID, event)
                    except shared.PendingNotFound:
                        print('pending accept event not found')
                case domain.ReplyEvent():
                    await self._acknowledge(event)
                    try:
                        self.pending_reply_events.complete(event.features.invocationID, event)
                    except shared.PendingNotFound:
                        print('pending reply event not found')
                case domain.PublishEvent():
                    await self._acknowledge(event)
                    self._loop.create_task(
                        self.incoming_publish_events.produce(event)
                    )
                case domain.CallEvent():
                    await self._acknowledge(event)
                    self._loop.create_task(
                        self.incoming_call_events.produce(event)
                    )
                case domain.NextEvent():
                    await self._acknowledge(event)
                    try:
                        self.pending_next_events.complete(event.features.yieldID, event)
                    except shared.PendingNotFound:
                        print('pending next event not found')
                case domain.CancelEvent():
                    await self._acknowledge(event)
                    try:
                        self.pending_cancel_events.complete(event.features.invocationID, event)
                    except shared.PendingNotFound:
                        print('pending cancel event not found')
                case _:
                    print('invalid event', event)

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
