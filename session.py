import asyncio
import typing
from uuid import uuid4

import domain
import peer


class NewResourcePayload:
    id: str
    uri: str
    options: domain.RegisterOptions


class Session:
    """
    """

    def __init__(
        self,
        peer: peer.Peer,
    ):
        self._peer = peer
        self._peer.incoming_publish_events.consume(self._on_publish)
        self._peer.incoming_call_events.consume(self._on_call)
        self._subscriptions = {}
        self._registrations = {}

    async def _on_publish(
        self,
        publishEvent: domain.PublishEvent,
    ):
        """
        """
        procedure = self._subscriptions.get(publishEvent.route.endpointID)
        await procedure(publishEvent)

    async def _on_call(
        self,
        callEvent: domain.CallEvent,
    ):
        """
        """
        procedure = self._registrations.get(callEvent.route.endpointID)
        replyEvent = await procedure(callEvent)
        await self._peer.send(replyEvent)

    async def publish(
        self,
        uri: str,
        payload: typing.Any,
    ) -> domain.PublishEvent:
        """
        """
        publish_event = domain.PublishEvent()
        publish_event.id = uuid4()
        publish_event.payload = payload
        publish_event.features = domain.PublishFeatures()
        publish_event.features.uri = uri
        await self._peer.send(publish_event)

    async def call(
        self,
        uri: str,
        payload: typing.Any,
    ) -> domain.ReplyEvent:
        """
        """
        call_event = domain.CallEvent()
        call_event.id = uuid4()
        call_event.payload = payload
        call_event.features = domain.CallFeatures()
        call_event.features.uri = uri

        pending_reply_event = asyncio.Future()
        self._peer.pending_reply_events[call_event.id] = pending_reply_event
        await self._peer.send(call_event)

        reply_event = await pending_reply_event

        if isinstance(reply_event, domain.ErrorEvent):
            raise Exception(reply_event.payload.code)

        return reply_event

    async def register(
        self,
        uri: str,
        options: domain.RegisterOptions,
        procedure: domain.CallProcedure,
    ) -> domain.Registration:
        """
        """
        payload = NewResourcePayload()
        payload.id = uuid4()
        payload.uri = uri
        payload.options = options
        replyEvent = await self.call("wamp.router.register", payload)
        self._registrations[replyEvent.payload.id] = procedure
        return replyEvent.payload

    async def subscribe(
        self,
        uri: str,
        options: domain.SubscribeOptions,
        procedure: domain.PublishProcedure,
    ) -> domain.Subscription:
        """
        """
        payload = NewResourcePayload()
        payload.id = uuid4()
        payload.uri = uri
        payload.options = options
        replyEvent = await self.call("wamp.router.subscribe", payload)
        self._subscriptions[replyEvent.payload.id] = procedure
        return replyEvent.payload

    async def unregister(
        self,
        registration_id: str,
    ):
        """
        """
        await self.call("wamp.router.unregister", registration_id)
        self._registrations.pop(registration_id)

    async def unsubscribe(
        self,
        subscription_id: str,
    ):
        """
        """
        await self.call("wamp.router.unsubscribe", subscription_id)
        self._registrations.pop(subscription_id)

    async def leave(
        self,
        reason: str,
    ):
        """
        """
