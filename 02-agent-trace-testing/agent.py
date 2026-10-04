#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一个最小可运行的 Agent（被测对象）：工具注册 + 迭代循环 + 轨迹记录。
零第三方依赖，行为确定（planner 是规则实现，不用 LLM），方便在 CI 里稳定复现。

- 工具调用：按 plan 逐步调用；工具可能返回失败（可注入）
- 迭代上限：runtime 硬上限 max_iterations，超过则强制中止
- 护栏：同一步骤连续 no_progress_window 次无进展（工具+参数完全重复且结果不变），提前中止
- 输出：steps 轨迹、最终回答或中止原因
- 终态兜底（v0.2）：轨迹耗尽后既没结论也没中止时，必须显式 abort，不允许静默挂起
"""

# PEP 604 的 `dict | None` 注解在 3.10 才支持，3.9 上会在 import 时直接 TypeError。
# 本地开发是 3.13、CI 是 3.11，都发现不了，本地 3.9 才会炸。
from __future__ import annotations

TOOLS = {
    "get_schedule": {"params": ["student", "week"], "desc": "查询某学生某周课表"},
    "get_grade": {"params": ["student", "course"], "desc": "查询某学生某门课成绩"},
    "book_room": {"params": ["room_id", "start", "duration_min"], "desc": "预订会议室"},
    "get_library": {"params": ["book_title"], "desc": "查图书馆馆藏"},
    "notify_advisor": {"params": ["student", "message"], "desc": "通知辅导员"},
}

# 工具故障注入表：key = 用例 id，value = {工具名: 失败次数}
FAIL_INJECT = {}


def execute_tool(name: str, args: dict) -> dict:
    """模拟工具执行。参数不全或工具不存在会返回结构化错误。"""
    if name not in TOOLS:
        return {"ok": False, "error": f"UNKNOWN_TOOL: {name}"}
    missing = [p for p in TOOLS[name]["params"] if p not in args]
    if missing:
        return {"ok": False, "error": f"MISSING_PARAM: {','.join(missing)}"}
    if not isinstance(args.get("duration_min", 1), int):
        return {"ok": False, "error": "TYPE_ERROR: duration_min must be int"}
    return {"ok": True, "data": f"{name}({args}) 返回：模拟数据"}


class AgentRuntime:
    """被测 Agent：按 plan 逐步调用工具，受迭代上限与无进展护栏约束。"""

    def __init__(self, max_iterations: int = 8, max_retry_per_tool: int = 2,
                 no_progress_window: int = 3):
        self.max_iterations = max_iterations
        self.max_retry_per_tool = max_retry_per_tool
        self.no_progress_window = no_progress_window

    def run(self, case: dict, fail_inject: dict | None = None) -> dict:
        fail_inject = fail_inject or {}
        steps = []
        tool_errors = {}          # 工具名 -> 已失败次数
        abort_reason = None
        final = None

        for step_idx, action in enumerate(case["plan"]):
            if len(steps) >= self.max_iterations:
                abort_reason = f"ITERATION_LIMIT: 达到硬上限 {self.max_iterations} 步仍未收敛"
                steps.append({"step": len(steps) + 1, "type": "abort", "content": abort_reason})
                break

            if "final" in action:
                # 兜底 3（v0.2 把位置从「工具调用分支」挪到这里）：
                # 上游工具没成功就不许给出结论。放错位置会误杀合法重试（A007），
                # 放在调用分支时「失败→重试」会被直接掐断。
                if steps and steps[-1].get("result", {}).get("ok") is False:
                    abort_reason = ("UPSTREAM_FAILED: 上游工具未成功，不允许给出结论"
                                    "（v0.1 曾出现『通知失败却说已通知』）")
                    steps.append({"step": len(steps) + 1, "type": "abort", "content": abort_reason})
                    break
                final = action["final"]
                steps.append({"step": len(steps) + 1, "type": "final", "content": final})
                break

            if "abort" in action:
                abort_reason = action["abort"]
                steps.append({"step": len(steps) + 1, "type": "abort", "content": abort_reason})
                break

            name, args = action["tool"], action.get("args", {})

            # 兜底 1：工具幻觉 —— 调用前先校验工具是否在注册表中
            if name not in TOOLS:
                steps.append({"step": len(steps) + 1, "type": "abort",
                              "content": f"HALLUCINATION: 工具『{name}』不在注册表中"})
                abort_reason = f"HALLUCINATION: 工具『{name}』不在注册表中"
                break

            # 兜底 2：参数 schema 前置校验，非法参数不进入工具调用
            missing = [p for p in TOOLS[name]["params"] if p not in args]
            type_bad = name == "book_room" and not isinstance(args.get("duration_min"), int)
            if missing or type_bad:
                why = f"MISSING_PARAM:{missing}" if missing else "TYPE_ERROR:duration_min"
                steps.append({"step": len(steps) + 1, "type": "abort", "content": f"INVALID_ARGS: {why}"})
                abort_reason = f"INVALID_ARGS: {why}"
                break

            signature = (name, tuple(sorted(args.items())))

            # 无进展护栏：最近 N 步签名完全重复且工具无进展 -> 提前中止
            if len(steps) >= self.no_progress_window:
                recent = [s for s in steps[-self.no_progress_window:] if s["type"] == "call"]
                if len(recent) == self.no_progress_window and all(
                        (s["tool"], tuple(sorted(s["args"].items()))) == signature for s in recent):
                    abort_reason = "NO_PROGRESS: 连续 %d 步工具与参数完全重复，提前中止" % self.no_progress_window
                    steps.append({"step": len(steps) + 1, "type": "abort", "content": abort_reason})
                    break

            # 同一工具持续失败超过重试上限 -> 中止，避免无效重试
            if tool_errors.get(name, 0) >= self.max_retry_per_tool:
                abort_reason = f"TOOL_GIVEUP: {name} 连续失败 {tool_errors[name]} 次，转人工"
                steps.append({"step": len(steps) + 1, "type": "abort", "content": abort_reason})
                break

            steps.append({"step": len(steps) + 1, "type": "call", "tool": name, "args": args})

            # 故障注入：前 N 次调用该工具强制失败（v0.2 修正——v0.1 只在工具本身
            # 已经报错时才减计数，合法参数的情况下注入形同虚设）
            inject_n = fail_inject.get(name, 0)
            if inject_n > 0:
                fail_inject[name] = inject_n - 1
                result = {"ok": False, "error": f"TRANSIENT: {name} 临时故障（故障注入 {inject_n} 次）"}
            else:
                result = execute_tool(name, args)
                if not result["ok"]:
                    result["error"] += "（真实工具报错）"

            tool_errors[name] = tool_errors.get(name, 0) + 1 if not result["ok"] else tool_errors.get(name, 0)
            steps[-1]["result"] = result

        # 终态兜底（v0.2）：轨迹跑完既没结论也没中止 = 静默挂起，必须显式 abort
        if abort_reason is None and final is None:
            abort_reason = "PLAN_EXHAUSTED: 轨迹耗尽且既未给出结论也未中止（静默挂起）"
            steps.append({"step": len(steps) + 1, "type": "abort", "content": abort_reason})

        return {"steps": steps, "final": final, "abort_reason": abort_reason,
                "steps_used": len(steps)}
