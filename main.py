import asyncio
import threading
from wechatbot import WeChatBot
from maim_message import *
import logging
import base64
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

WEBSOCKET_URL = "ws://localhost:8010/ws"

route_config = RouteConfig(
    route_config={
        "wx": TargetConfig(
            url=WEBSOCKET_URL,
            token=None,
        )
    }
)

async def handle(msg):
    logger.info(msg)
    try:
        await bot.send(msg['message_info']['user_info']['user_id'], msg['message_segment']['data'])
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
    pass

router = Router(route_config, logger)
router.register_class_handler(handle)

router_thread = threading.Thread(target=lambda: asyncio.run(router.run()), daemon=True)
router_thread.start()

format_info = FormatInfo(
            content_format=["text", "image", "emoji", "voice"],
            accept_format=["text","image","emoji","reply","voice","command","voiceurl","music","videourl","file","imageurl","forward","video",],
        ) 

bot = WeChatBot()


@bot.on_message
async def handle(msg):
    print(f"[{msg.type}] {msg.user_id}: {msg.text}")

    base_message_info = BaseMessageInfo(
        platform="wx",
        message_id=msg.raw.get("message_id"),
        time=msg.timestamp.timestamp(),
        user_info=UserInfo("wx", msg.user_id, msg.user_id),
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
        submit_seg = Seg(
                type="image",
                data=base64.b64encode(bot.download(msg).data)
        )

    msg_send = MessageBase(
        message_info=base_message_info,
        message_segment=submit_seg
    )

    logger.info(msg_send)

    await router.send_message(msg_send)

    logger.info("发送成功")

bot.run()