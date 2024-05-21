import asyncio


async def say_hello():
    # This function waits for 1 second and then prints a message
    await asyncio.sleep(1)
    print("Hello")


async def say_world():
    # This function waits for 2 seconds and then prints a message
    await asyncio.sleep(2)
    return "World"
    # print("World")


async def main():
    # Create tasks for each function
    task1 = asyncio.create_task(say_hello())
    task2 = asyncio.create_task(say_world())

    # Wait until both tasks are completed
    await task1
    await task2


def some_function():
    print("Hello, world!")
    # # Get the event loop
    loop = asyncio.get_event_loop()

    # # Run the main function until it completes
    # loop.run_until_complete(main())

    loop.create_task(say_hello())

    print("Hello, world!")

    loop.run_until_complete(asyncio.sleep(0))

    # tasks = asyncio.all_tasks(loop)

    # print(tasks)

    # for task in tasks:
    #     task.cancel()


some_function()
