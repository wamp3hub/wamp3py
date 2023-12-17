import pytest

import wamp3py


@pytest.fixture
async def session():
    return await wamp3py.websocket_join(
        'localhost:8888',
        credentials=None,
    )


class InvalidName(wamp3py.ApplicationError):
    """
    Invalid name
    """


async def greeting(
    name: str,
    **kwargs,
):
    if len(name) > 0:
        return f"Hello, {name}!"
    raise InvalidName()



async def test_rpc(session: wamp3py.Session):
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
