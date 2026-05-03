import asyncio
import threading
from wechatbot import WeChatBot
from maim_message import *
import logging
import base64
import time
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# WebSocket 配置
WEBSOCKET_URL = "ws://localhost:8010/ws"
WEBSOCKET_TOKEN = None

# 每次运行强制扫码
FORCE_LOGIN = False

# 与Bot对话的用户（你）的昵称，ilink api获取不到真实的用户名，必填项
USER_NICKNAME = ""

# 模拟打字
SIMULATE_TYPING = True

route_config = RouteConfig(
    route_config={
        "wx": TargetConfig(
            url=WEBSOCKET_URL,
            token=WEBSOCKET_TOKEN,
        )
    }
)

async def handle(msg):
    logger.info(msg)
    try:
        text = msg['message_segment']['data']
        user_id = msg['message_info']['user_info']['user_id']
        if SIMULATE_TYPING:
            await bot.send_typing(user_id)
            time.sleep(len(text) * 0.1 + random.randint(0, len(text)) * 0.05)
        await bot.send(user_id, text)
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
    pass

router = Router(route_config, logger)
router.register_class_handler(handle)

router_thread = threading.Thread(target=lambda: asyncio.run(router.run()), daemon=True)
router_thread.start()

format_info = FormatInfo(
            content_format=["text", "image", "emoji", "voice"],
            accept_format=["text", "image", "emoji", "reply", "voice", "command", "voiceurl", "music", 
                           "videourl", "file", "imageurl", "forward", "video",],
        ) 

bot = WeChatBot()


@bot.on_message
async def handle(msg):
    logger.debug(f"[{msg.type}] {msg.user_id}: {msg.text}")

    base_message_info = BaseMessageInfo(
        platform="wx",
        message_id=msg.raw.get("message_id"),
        time=msg.timestamp.timestamp(),
        user_info=UserInfo("wx", msg.user_id, USER_NICKNAME),
        group_info=None,
        template_info=None,
        format_info=format_info,
        additional_config={"context_token": msg.raw.get("context_token")},
    )
    if msg.type == "text":
        submit_seg = Seg(
                type="text",
                data=msg.text,
        )
    elif msg.type == "image":
        image = await bot.download(msg)
        submit_seg = Seg(
                type="image",
                data=base64.b64encode(image.data).decode()
        )

    msg_send = MessageBase(
        message_info=base_message_info,
        message_segment=submit_seg
    )

    logger.info(msg_send)

    await router.send_message(msg_send)

    logger.info("发送至 MaiBot 成功")

asyncio.run(bot.login(force=FORCE_LOGIN))
bot.run()
