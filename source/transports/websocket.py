import typing

import websockets

import domain
import peer
import session
import transports.interview


class WSTransport:

    connection: websockets.WebSocketClientProtocol
    serializer: peer.Serializer

    async def write(
        self,
        event: domain.Event
    ):
        message = self.serializer.encode(event)
        await self.connection.send(message)

    async def read(self) -> domain.Event:
        message = await self.connection.recv()
        event = self.serializer.decode(message)
        return event

    async def close(self):
        await self.connection.close()


async def websocket_connect(
    address: str,
    secure: bool,
    ticket: str,
    serializer: peer.Serializer,
) -> WSTransport:
    protocol = 'ws'
    if secure:
        protocol = 'wss'
    url = f'{protocol}://{address}/wamp/v1/websocket?ticket={ticket}'
    connection = await websockets.connect(url)
    transport = WSTransport()
    transport.connection = connection
    transport.serializer = serializer
    return transport


async def websocket_join(
    address: str,
    secure: bool,
    serializer: peer.Serializer,
    credentials: typing.Any,
) -> session.Session:
    payload = await transports.interview.http2interview(address, secure, credentials)
    transport = await websocket_connect(address, secure, payload.ticket, serializer)
    router = peer.Peer(transport)
    __session = session.Session(router)
    await router.listen()
    return __session
