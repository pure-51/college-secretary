"""字段级脱敏（ADR 000 §6：传输前打码、打码后落库；演示态对真实敏感字段强制）"""
import re

from app.config import settings

_PHONE = re.compile(r"(?<!\d)(1[3-9]\d)\d{4}(\d{4})(?!\d)")
_ID_CARD = re.compile(r"(?<!\d)(\d{6})\d{8}(\d{3}[\dXx])(?!\d)")


def mask_phone(text: str) -> str:
    return _PHONE.sub(r"\1****\2", text)


def mask_id_card(text: str) -> str:
    return _ID_CARD.sub(r"\1********\2", text)


_FIELD_MASKS = {
    "phone": "138****0000",
    "id_card": "************0012",
    "score": "**",
    "gpa": "**",
    "rank": "**",
    "amount": "¥***",
}


def apply(data, context: str = "display"):
    """递归脱敏：dict 中命中 SENSITIVE_FIELDS 的键打码，字符串中手机/身份证正则打码。
    context: display（展示）/ db（落库，强制）。"""
    if isinstance(data, dict):
        return {
            k: (_FIELD_MASKS.get(k, "***") if k in settings.SENSITIVE_FIELDS and v is not None else apply(v, context))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [apply(item, context) for item in data]
    if isinstance(data, str):
        return mask_phone(mask_id_card(data))
    return data
