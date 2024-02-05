from sys import path

path.append('./wamp3py')


import asyncio
import wamp3py


async def greeting(
    payload: str,
    **kwargs,
) -> str:
    return f'Hello, {payload}!'


async def main():
    session = await wamp3py.websocket_join(
        'localhost:8800',
        credentials=None,
    )
    print('wamp joined', session.ID)
    await session.register(
        'net.example.greeting',
        greeting,
    )
    reply_event = await session.call('net.example.greeting', 'aidar')
    print(reply_event['payload'])


asyncio.run(main())
