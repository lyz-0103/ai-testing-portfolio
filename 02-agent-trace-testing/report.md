# Agent 评测报告（工具调用轨迹 / 迭代护栏 / 错误恢复）

- 评测时间：2026-10-04 20:43
- 被测对象：agent.py 的规则型 Agent（工具注册表 5 个工具）
- 用例总数：15，整体通过率：**93.3%**（14/15）
- 有效用例（不含缺陷探针 1 条）：14 条，通过 **14/14（100.0%）**；缺陷探针：B001（刻意植入，预期失败，作为评估器回归哨兵）

## 逐例轨迹

| ID | 类别 | 类型 | 步数 | 终态 | 工具调用序列 | 判定 |
|----|------|------|------|------|--------------|------|
| A001 | 正常 | 单工具 | 2 | 结论 | get_schedule | 通过 |
| A002 | 正常 | 多工具组合 | 3 | 结论 | get_grade → notify_advisor | 通过 |
| A003 | 正常 | 依赖参数 | 3 | 结论 | get_schedule → book_room | 通过 |
| A004 | 正常 | 单工具 | 2 | 结论 | get_library | 通过 |
| A005 | 正常 | 三步链路 | 4 | 结论 | get_grade → notify_advisor → get_schedule | 通过 |
| A006 | 正常 | 类型约束 | 2 | 结论 | book_room | 通过 |
| A007 | 正常 | 容错恢复 | 3 | 结论 | get_library → get_library | 通过 |
| A008 | 正常 | 护栏生效 | 4 | 中止 | get_schedule → get_schedule → get_schedule | 通过 |
| B001 | 护栏 | 死循环（硬上限） | 13 | 中止 | get_schedule → get_schedule → get_schedule → get_schedule → get_schedule → get_schedule → get_schedule → get_schedule → get_schedule → get_schedule → get_schedule → get_schedule | 失败（缺陷探针·预期失败） |
| B002 | 护栏 | 无进展中止 | 4 | 中止 | get_schedule → get_schedule → get_schedule | 通过 |
| B003 | 护栏 | 工具连续失败 | 3 | 中止 | book_room → book_room | 通过 |
| C001 | 错误恢复 | 参数缺失 | 1 | 中止 | （无） | 通过 |
| C002 | 错误恢复 | 幻觉工具 | 1 | 中止 | （无） | 通过 |
| C003 | 错误恢复 | 类型错误 | 1 | 中止 | （无） | 通过 |
| C004 | 错误恢复 | 应中止却给结论 | 2 | 中止 | notify_advisor | 通过 |

## 护栏统计

- 平均步数：3.20
- 突破迭代上限（疑似死循环）：1 例
- 无进展提前中止生效：2 例
- 工具连续失败转人工：1 例

## Badcase（1 条）

| ID | 类别 | 失败原因 | 中止原因/最终结论 |
|----|------|----------|------------------|
| B001 | 护栏 | 突破迭代上限：实际用了 13 步 > 期望上限 4 步（疑似死循环） | ITERATION_LIMIT: 达到硬上限 12 步仍未收敛 |
