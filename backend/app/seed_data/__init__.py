"""seed 包导出（ADR 000 §5：seed/ 归数据 owner）"""
from app.seed_data.seed_demo import seed_demo, clear_demo

__all__ = ["seed_demo", "clear_demo"]
