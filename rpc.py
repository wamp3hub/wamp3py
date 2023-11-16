import asyncio

import domain
import serializers
import transports


async def main():
    session = await transports.websocket_join(
        '0.0.0.0:8888',
        False,
        serializers.JSONSerializer(),
        {'username': 'test', 'password': 'secret'},
    )

    async def procedure(callEvent: domain.CallEvent):
        print('call', callEvent.payload)
        return domain.ReplyEvent(
            ID='test',
            features=domain.ReplyFeatures(invocationID=callEvent.ID),
            payload=callEvent.payload,
        )

    registration = await session.register(
        'net.example.echo',
        domain.RegisterOptions(),
        procedure,
    )
    print(registration)

    replyEvent = await session.call('net.example.echo', 'Hello, WAMP!')
    print('reply', replyEvent.payload)


if __name__ == '__main__':
    asyncio.run(main())
