"""知情同意服务（ADR 000 §6；S0 骨架：演示模式默认豁免，user_consents 表随 S1 接入）"""


class ConsentRequired(Exception):
    """未获同意即触碰敏感边界，路由层转 403"""


def check(scope: str, demo_mode: bool = False) -> None:
    """校验是否已对 scope 同意；演示模式默认豁免。
    S0：未接入持久化前普通场景放行；S1 接入 user_consents 表后强制。"""
    if demo_mode:
        return
    # 骨架：暂无持久化，默认放行（S1 实现后此处读取 user_consents）
    return
