#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 评测脚本（零第三方依赖）：工具调用轨迹测试 + 迭代上限护栏 + 错误恢复策略
- 读取 eval_cases.json，驱动 agent.py 的 AgentRuntime
- 按 5 个维度判定：幻觉工具 / 参数合法性 / 必需工具覆盖 / 迭代上限 / 终态是否符合预期
- 产出 report.md（轨迹 + 护栏统计 + badcase）与 results/latest.json

用法：
    python3 eval_agent.py
"""

import datetime
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CASES_FILE = os.path.join(BASE_DIR, "eval_cases.json")
REPORT_FILE = os.path.join(BASE_DIR, "report.md")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

from agent import AgentRuntime, TOOLS  # noqa: E402


def judge(case: dict, run: dict) -> list:
    """返回失败原因列表（空列表 = 通过）。"""
    reasons = []
    steps = run["steps"]
    called = [s for s in steps if s["type"] == "call"]

    # 1) 幻觉工具：调用了注册表里不存在的工具
    for s in called:
        if s["tool"] not in TOOLS:
            reasons.append(f"幻觉工具：调用了不存在的工具『{s['tool']}』")

    # 2) 参数合法性（静态检查，比工具返回的报错更早拦截）
    for s in called:
        if s["tool"] not in TOOLS:
            continue
        missing = [p for p in TOOLS[s["tool"]]["params"] if p not in s.get("args", {})]
        if missing:
            reasons.append(f"参数缺失：{s['tool']} 缺少 {missing}")
        if s["tool"] == "book_room" and not isinstance(s.get("args", {}).get("duration_min"), int):
            reasons.append("参数类型错误：book_room.duration_min 应为 int")

    # 3) 必需工具覆盖
    # v0.2 修正：只对「预期收敛并给出结论」的用例校验。
    # 中止类用例允许「参数预检就拦下、一次工具都没调」（C001/C003），
    # v0.1 无差别校验，把这两个用例误判成 FAIL。
    if case.get("expected", "final") == "final":
        for must in case.get("required_calls", []):
            if not any(c["tool"] == must for c in called):
                reasons.append(f"漏调必需工具：『{must}』未出现在轨迹中")

    # 4) 迭代上限（死循环护栏）
    cap = case.get("max_iterations", 8)
    if run["steps_used"] > cap:
        reasons.append(f"突破迭代上限：实际用了 {run['steps_used']} 步 > 期望上限 {cap} 步（疑似死循环）")

    # 5) 结论与轨迹一致性：最后一步是失败的工具调用却仍给出结论（v0.1 的典型缺陷）
    last = steps[-1] if steps else None
    if run["final"] and last and last.get("type") == "call" \
            and last.get("result", {}).get("ok") is False:
        reasons.append("结论与轨迹不一致：最后一步工具调用失败，却仍然给出了结论（掩盖失败）")

    # 6) 终态是否符合预期
    expected = case.get("expected", "final")
    aborted = run["abort_reason"] is not None
    if expected == "final" and aborted:
        reasons.append(f"任务未收敛：预期给出结论，实际中止（{run['abort_reason']}）")
    if expected == "abort" and not aborted:
        reasons.append("终态错误：预期应中止，实际却给出了结论（掩盖了失败）")

    return reasons


def run_all() -> list:
    with open(CASES_FILE, encoding="utf-8") as f:
        cases = json.load(f)["cases"]

    results = []
    for case in cases:
        runtime = AgentRuntime(max_iterations=case.get("runtime_cap", 8))
        fail_inject = dict(case.get("fail_inject", {}))
        run = runtime.run(case, fail_inject=fail_inject)
        reasons = judge(case, run)
        results.append({
            **case, "run": run, "pass": len(reasons) == 0, "reason": reasons,
            "steps_used": run["steps_used"],
            "outcome": "中止" if run["abort_reason"] else "结论",
        })
        flag = "PASS" if not reasons else "FAIL"
        print(f"[{flag}] {case['id']} ({case['category']}/{case['type']}) "
              f"步数={run['steps_used']} 终态={results[-1]['outcome']}")
        if reasons:
            for r in reasons:
                print(f"        - {r}")
    return results


def write_report(results: list) -> None:
    total = len(results)
    passed = sum(r["pass"] for r in results)
    # 缺陷探针：刻意植入、预期应当 FAIL 的用例。它不进通过率分母，
    # 而是一个「评估器回归哨兵」——哪天它 PASS 了，说明护栏被改坏了。
    probes = [r["id"] for r in results if r.get("known_defect")]
    eff_total = total - len(probes)
    eff_passed = sum(1 for r in results if r["pass"] and not r.get("known_defect"))
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Agent 评测报告（工具调用轨迹 / 迭代护栏 / 错误恢复）",
        "",
        f"- 评测时间：{now}",
        f"- 被测对象：agent.py 的规则型 Agent（工具注册表 {len(TOOLS)} 个工具）",
        f"- 用例总数：{total}，整体通过率：**{passed / total:.1%}**（{passed}/{total}）",
        f"- 有效用例（不含缺陷探针 {len(probes)} 条）：{eff_total} 条，"
        f"通过 **{eff_passed}/{eff_total}（{eff_passed / eff_total:.1%}）**"
        + (f"；缺陷探针：{','.join(probes)}（刻意植入，预期失败，作为评估器回归哨兵）" if probes else ""),
        "",
        "## 逐例轨迹",
        "",
        "| ID | 类别 | 类型 | 步数 | 终态 | 工具调用序列 | 判定 |",
        "|----|------|------|------|------|--------------|------|",
    ]
    for r in results:
        calls = " → ".join(
            s["tool"] for s in r["run"]["steps"] if s["type"] == "call") or "（无）"
        verdict = "通过" if r["pass"] else "失败"
        if r.get("known_defect"):
            verdict += "（缺陷探针·预期失败）"
        lines.append(f"| {r['id']} | {r['category']} | {r['type']} | {r['steps_used']} | "
                     f"{r['outcome']} | {calls} | {verdict} |")

    # 护栏统计
    caps = sum(1 for r in results if "突破迭代上限" in "".join(r["reason"]))
    no_progress = sum(1 for r in results
                      if any("NO_PROGRESS" in (r["run"]["abort_reason"] or "") for _ in [0]))
    giveup = sum(1 for r in results
                 if any("TOOL_GIVEUP" in (r["run"]["abort_reason"] or "") for _ in [0]))
    avg_steps = sum(r["steps_used"] for r in results) / total
    lines += ["", "## 护栏统计", "",
              f"- 平均步数：{avg_steps:.2f}",
              f"- 突破迭代上限（疑似死循环）：{caps} 例",
              f"- 无进展提前中止生效：{no_progress} 例",
              f"- 工具连续失败转人工：{giveup} 例"]

    bad = [r for r in results if not r["pass"]]
    lines += ["", f"## Badcase（{len(bad)} 条）", ""]
    if bad:
        lines += ["| ID | 类别 | 失败原因 | 中止原因/最终结论 |",
                  "|----|------|----------|------------------|"]
        for r in bad:
            reason = "；".join(r["reason"])
            tail = r["run"]["abort_reason"] or r["run"]["final"] or "—"
            lines.append(f"| {r['id']} | {r['category']} | {reason} | {tail} |")
    else:
        lines.append("本批次无失败用例。")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "latest.json"), "w", encoding="utf-8") as f:
        json.dump({"time": now,
                   "summary": {"total": total, "passed": passed,
                               "effective_total": eff_total, "effective_passed": eff_passed,
                               "probes": probes},
                   "results": results},
                  f, ensure_ascii=False, indent=2)

    print(f"\n报告已生成：{REPORT_FILE}")


if __name__ == "__main__":
    write_report(run_all())
