import asyncio


async def select_first(*awaitables):
    __awaitables = [asyncio.ensure_future(i) for i in awaitables]
    done, pending = await asyncio.wait(__awaitables, return_when=asyncio.FIRST_COMPLETED)
    return {i.result() for i in done}, pending
