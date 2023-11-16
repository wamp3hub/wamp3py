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
    pending_accept_events: typing.MutableMapping[str, asyncio.Future]
    pending_reply_events: typing.MutableMapping[str, asyncio.Future]

    def __init__(
        self,
        transport: Transport,
    ):
        self.transport = transport
        self.incoming_publish_events = shared.Stream()
        self.incoming_call_events = shared.Stream()
        self.pending_accept_events = {}
        self.pending_reply_events = {}

    async def _safe_send(
        self,
        event: domain.Event,
    ):
        await self.transport.write(event)

    async def send(
        self,
        event: domain.Event,
    ):
        pending_accept_event = asyncio.Future()
        self.pending_accept_events[event.ID] = pending_accept_event
        await self._safe_send(event)
        await pending_accept_event

    async def _acknowledge(
        self,
        source: domain.Event,
    ):
        accept_features = domain.AcceptFeatures(sourceID=source.ID)
        accept_event = domain.AcceptEvent(ID=shared.new_id(), features=accept_features)
        await self._safe_send(accept_event)

    async def _listen(
        self,
    ):
        while True:
            event = await self.transport.read()
            if isinstance(event, domain.AcceptEvent):
                await self._acknowledge(event)
                pending_accept_event = self.pending_accept_events.get(event.features.sourceID)
                if pending_accept_event is None:
                    print('pending accept event not found')
                else:
                    pending_accept_event.set_result(event)
            elif isinstance(event, domain.ReplyEvent):
                await self._acknowledge(event)
                pending_reply_event = self.pending_reply_events.get(event.features.invocationID)
                if pending_reply_event is None:
                    print('pending reply event not found')
                else:
                    pending_reply_event.set_result(event)
            elif isinstance(event, domain.PublishEvent):
                await self._acknowledge(event)
                await self.incoming_publish_events.produce(event)
            elif isinstance(event, domain.CallEvent):
                await self._acknowledge(event)
                await self.incoming_call_events.produce(event)
            else:
                print('invalid event')

    def listen(
        self,
    ):
        asyncio.create_task(self._listen())
        return asyncio.sleep(0)

    async def close(
        self,
    ):
        await self.transport.close()
