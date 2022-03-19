import asyncio

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.model import Friend, MiraiSession

# from graia.application import GraiaMiraiApplication, Session
from graia.broadcast import Broadcast

loop = asyncio.get_event_loop()
bcc = Broadcast(loop=loop)

# bot = GraiaMiraiApplication(
#     broadcast=bcc,
#     connect_info=Session(
#         host="http://localhost:8080",  # 填入 httpapi 服务运行的地址
#         verifyKey="SNH48Forever",  # 填入 authKey
#         account=421497163,  # 你的机器人的 qq 号
#         websocket=True,  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
#     )
# )

bot = Ariadne(MiraiSession(host="http://localhost:8080", verify_key="SNH48Forever", account=421497163))
