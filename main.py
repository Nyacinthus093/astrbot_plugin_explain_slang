import re
import aiohttp

from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Plain
from astrbot.api import logger

API_URL = "https://lab.magiconch.com/api/nbnhhsh/guess"


@register(
    "astrbot_plugin_explain_slang",
    "Nyacinthus093",
    "黑话/缩写解释器，调用“能不能好好说话(nbnhhsh)”接口解释网络首字母缩写",
    "v1.0.0",
    "https://github.com/Nyacinthus093/astrbot_plugin_explain_slang"
)
class ExplainSlang(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("解释", alias=["nbnhhsh"])
    async def explain_slang(self, event, text: str = ""):
        """解释网络缩写黑话。用法：/解释 查询的缩写或文本"""
        raw = text.strip() if text else event.message_str.replace("/解释", "", 1).strip()
        if not raw:
            yield event.plain_result("用法：/解释 <缩写或文本>，例如 /解释 yyds")
            return

        result = await self._guess(raw)
        if result is None:
            yield event.plain_result("查询失败，请稍后再试。")
            return
        if not result:
            yield event.plain_result(f"没有找到“{raw}”对应的释义。")
            return

        yield event.plain_result(self._format(result))

    async def _guess(self, raw: str):
        tokens = re.findall(r"[a-zA-Z0-9]{2,}", raw)
        payload = {"text": ",".join(tokens) if tokens else raw}
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    API_URL,
                    json=payload,
                    headers={
                        "content-type": "application/json",
                        "User-Agent": "Mozilla/5.0",
                    },
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"nbnhhsh API 返回状态码 {resp.status}")
                        return None
                    return await resp.json()
        except Exception as e:
            logger.error(f"请求 nbnhhsh API 失败: {e}")
            return None

    @staticmethod
    def _format(data) -> str:
        lines = []
        for item in data:
            name = item.get("name", "")
            trans = item.get("trans")
            if trans:
                lines.append(f"{name}: {' / '.join(trans)}")
            elif item.get("inputting"):
                lines.append(f"{name}: 无对应释义，有可能是 {' / '.join(item['inputting'])}")
            else:
                lines.append(f"{name}: 尚未录入释义")
        return "\n".join(lines)

    async def terminate(self):
        pass
