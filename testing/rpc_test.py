import pytest

import domain
import serializers
import transports


@pytest.fixture
async def session():
    return await transports.websocket_join(
        'localhost:8888',
        False,
        serializers.JSONSerializer(),
        None
    )


class InvalidName(domain.ApplicationError):
    """
    Invalid name
    """


async def greeting(
    call_event: domain.CallEvent,
):
    name = call_event.payload
    if len(name) > 0:
        return f"Hello, {name}!"
    raise InvalidName()



async def test_rpc(session):
    # test regsiter
    await session.register('net.example.greeting', domain.RegisterOptions(), greeting)

    # test call
    reply_event = await session.call('net.example.greeting', 'World')
    assert reply_event.payload == 'Hello, World!'

    # test error
    try:
        reply_event = await session.call('net.example.greeting', '')
    except Exception as e:
        print(e)
    else:
        raise Exception('Expected exception')

    # test cancel

    # test unregister
