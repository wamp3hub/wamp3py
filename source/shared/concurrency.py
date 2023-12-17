import asyncio


async def race(
    *awaitables,
    __cancel_pending=True,
):
    __awaitables = [asyncio.ensure_future(i) for i in awaitables]
    done, pending = await asyncio.wait(__awaitables, return_when=asyncio.FIRST_COMPLETED)
    if __cancel_pending:
        for task in pending:
            task.cancel()
    for task in done:
        result = task.result()
        return result

