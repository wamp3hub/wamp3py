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

    async def read(self):
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
    incoming_publish_events: shared.stream.Stream
    incoming_call_events: shared.stream.Stream
    pending_accept_events: typing.MutableMapping[str, asyncio.Future]
    pending_reply_events: typing.MutableMapping[str, asyncio.Future]

    def __init__(self):
        self.incoming_publish_events = shared.stream.Stream()
        self.incoming_call_events = shared.stream.Stream()
        self.pending_accept_events = {}
        self.pending_reply_events = {}

    async def listen(
        self,
    ):
        async for event in self.transport.read():
            if isinstance(event, domain.AcceptEvent):
                pending_accept_event = self.pending_accept_events.get(event.features.sourceID)
                pending_accept_event.set_result(event)
            elif isinstance(event, domain.ReplyEvent):
                pending_reply_event = self.pending_reply_events.get(event.features.invocationID)
                pending_reply_event.set_result(event)
            elif isinstance(event, domain.PublishEvent):
                await self.incoming_publish_events.produce(event)
            elif isinstance(event, domain.CallEvent):
                await self.incoming_call_events.produce(event)
            else:
                ...

    async def _send_safe(
        self,
        event: domain.Event,
    ):
        self.transport.write(event)

    async def send(
        self,
        event: domain.Event,
    ):
        pending_accept_event = asyncio.Future()
        self.pending_accept_events[event.id] = pending_accept_event
        self._send_safe(event)
        await pending_accept_event

    async def close(
        self,
    ):
        self.transport.close()
