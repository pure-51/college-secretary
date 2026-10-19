"""叙事化演示模式（ADR 000 §3.11/§6：demo_seeds 追踪表为 clear 唯一依据）
演示态开关由 seed/clear 管理；redaction/consent 钩子在演示态对真实敏感字段强制打码。
"""
_DEMO_ACTIVE = False


def is_demo() -> bool:
    return _DEMO_ACTIVE


def enable() -> None:
    global _DEMO_ACTIVE
    _DEMO_ACTIVE = True


def disable() -> None:
    global _DEMO_ACTIVE
    _DEMO_ACTIVE = False


def set_demo(active: bool) -> None:
    global _DEMO_ACTIVE
    _DEMO_ACTIVE = active
