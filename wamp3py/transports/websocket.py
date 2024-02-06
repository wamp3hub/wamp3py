from functools import partial
import typing

import websockets

from .. import domain
from .. import logger
from .. import peer
from .. import session
from .. import serializers
from .. import shared
from . import interview
from . import reconnectable


class WSTransport(peer.Transport):

    connection: websockets.WebSocketClientProtocol
    serializer: peer.Serializer

    async def write(
        self,
        event: domain.Event
    ) -> None:
        message = self.serializer.encode(event)
        await self.connection.send(message)

    async def read(self) -> domain.Event:
        try:
            message = await self.connection.recv()
        except websockets.ConnectionClosedOK:
            raise peer.ConnectionClosed()
        except Exception:
            raise reconnectable.BadConnection()

        event = self.serializer.decode(message)
        return event

    async def close(self) -> None:
        await self.connection.close()


async def __connect(
    url: str,
    serializer: peer.Serializer,
) -> WSTransport:
    connection = await websockets.connect(url)
    transport = WSTransport()
    transport.connection = connection
    transport.serializer = serializer
    return transport


async def websocket_connect(
    address: str,
    ticket: str,
    secure: bool = False,
    serializer: peer.Serializer = serializers.DefaultSerializer,
    reconnection_strategy: shared.RetryStrategy = shared.DefaultRetryStrategy,
) -> reconnectable.ReconnectableTransport:
    protocol = 'ws'
    if secure:
        protocol = 'wss'

    url = f'{protocol}://{address}/wamp/v1/websocket?ticket={ticket}'

    instance = reconnectable.ReconnectableTransport(
        connect=partial(__connect, url=url, serializer=serializer),
        strategy=reconnection_strategy,
    )
    try:
        await instance.reconnect()
    except Exception as e:
        logger.error('during connect', exception=repr(e))
        raise peer.ConnectionClosed()

    return instance


async def websocket_join(
    address: str,
    /,
    credentials: typing.Any,
    secure: bool = False,
    serializer: peer.Serializer = serializers.DefaultSerializer,
    reconnection_strategy: shared.RetryStrategy = shared.DefaultRetryStrategy,
) -> session.Session:
    payload = await interview.http2interview(
        address=address, 
        secure=secure,
        credentials=credentials,
    )
    transport = await websocket_connect(
        address=address,
        secure=secure,
        ticket=payload['ticket'],
        serializer=serializer,
        reconnection_strategy=reconnection_strategy,
    )
    router = peer.Peer(payload['yourID'], transport)
    import asyncio
    await asyncio.sleep(0)
    instance = session.Session(router)
    return instance
