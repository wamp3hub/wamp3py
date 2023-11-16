import asyncio
import typing

from pydantic.dataclasses import dataclass

import domain
import peer
import shared


Domain = dataclass(kw_only=True, slots=True)


@Domain
class NewResourcePayload:
    ID: str
    URI: str
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
        URI: str,
        payload: typing.Any,
    ) -> domain.PublishEvent:
        """
        """
        publish_event = domain.PublishEvent(
            ID=shared.new_id(),
            payload=payload,
            features=domain.PublishFeatures(
                URI=URI
            ),
        )
        await self._peer.send(publish_event)

    async def call(
        self,
        URI: str,
        payload: typing.Any,
    ) -> domain.ReplyEvent:
        """
        """
        call_event = domain.CallEvent(
            ID=shared.new_id(),
            payload=payload,
            features=domain.CallFeatures(
                URI=URI,
                timeout=100,
            ),
        )

        pending_reply_event = asyncio.Future()
        self._peer.pending_reply_events[call_event.ID] = pending_reply_event
        await self._peer.send(call_event)

        reply_event = await pending_reply_event

        if isinstance(reply_event, domain.ErrorEvent):
            raise Exception(reply_event.payload.code)

        return reply_event

    async def register(
        self,
        URI: str,
        options: domain.RegisterOptions,
        procedure: domain.CallProcedure,
    ) -> domain.Registration:
        """
        """
        payload = NewResourcePayload(
            ID=shared.new_id(),
            URI=URI,
            options=options,
        )
        replyEvent = await self.call("wamp.router.register", payload)
        registration = domain.Registration(**replyEvent.payload)
        self._registrations[registration.ID] = procedure
        return registration

    async def subscribe(
        self,
        URI: str,
        options: domain.SubscribeOptions,
        procedure: domain.PublishProcedure,
    ) -> domain.Subscription:
        """
        """
        payload = NewResourcePayload(
            ID=shared.new_id(),
            URI=URI,
            options=options,
        )
        replyEvent = await self.call("wamp.router.subscribe", payload)
        subscription = domain.Subscription(replyEvent.payload)
        self._subscriptions[subscription.ID] = procedure
        return subscription

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
