import pytest

import source


@pytest.fixture
async def session():
    return await source.websocket_join(
        'localhost:8888',
        False,
        source.DefaultSerializer,
        None
    )


class InvalidName(source.ApplicationError):
    """
    Invalid name
    """


async def greeting(
    call_event: source.CallEvent,
):
    name = call_event.payload
    if len(name) > 0:
        return f"Hello, {name}!"
    raise InvalidName()



async def test_rpc(session: source.Session):
    # test regsiter
    await session.register('net.example.greeting', greeting)

    # test call
    reply_event = await session.call('net.example.greeting', 'World')
    assert reply_event.payload == 'Hello, World!'

    # test error
    try:
        reply_event = await session.call('net.example.greeting', '')
    except Exception as e:
        print(e)
    else:
        raise Exception('Expected exception InvalidName')

    # test cancel

    # test unregister
