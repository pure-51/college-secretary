"""S0-5 门禁脚本：运行全量测试集，断言用例数 >= 15 且全部通过
用法：backend/venv/Scripts/python scripts/gate.py
退出码 0 = 通过；非 0 = 门禁未过（gate.py 自身依赖失败也算 0 之外的退出码）。
"""
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MIN_CASES = 15


def main() -> int:
    # Windows 控制台默认 GBK，测试输出含非 GBK 字符会崩溃 → 统一 UTF-8（S1-4 修复）
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--tb=short"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(result.stdout)
    if result.stderr.strip():
        print("=== stderr ===", file=sys.stderr)
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"[gate] FAIL: pytest 退出码 {result.returncode}")
        return 1

    # 统计用例数：pytest 汇总行形如 "17 passed in 1.23s"
    summary = result.stdout
    import re
    passed = 0
    for line in summary.splitlines():
        m = re.search(r"(\d+) passed", line)
        if m:
            passed = max(passed, int(m.group(1)))

    if passed < MIN_CASES:
        print(f"[gate] FAIL: 用例数 {passed} < {MIN_CASES}")
        return 2
    print(f"[gate] PASS: {passed} 条用例全部通过（>= {MIN_CASES}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
