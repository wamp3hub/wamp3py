import pytest_asyncio


@pytest_asyncio.fixture(scope="session")
def event_loop_policy():
    import uvloop
    return uvloop.EventLoopPolicy()
