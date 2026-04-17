import asyncio
from douyin import DouyinParser

async def test():
    parser = DouyinParser()
    res = await asyncio.to_thread(parser.parse, "https://v.douyin.com/raqAMsOlgIY/")
    print(res)

asyncio.run(test())
