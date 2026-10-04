# AI 测试作品集

面向 AI/LLM 测试方向的个人作品集。目前包含 LLM 应用评测与 Agent 轨迹测试两个项目，后续按计划补齐 RAG 应用测试和 Prompt 注入专项。

![eval](https://github.com/lyz-0103/ai-testing-portfolio/actions/workflows/eval.yml/badge.svg)

## 项目

**[01-llm-eval-harness](./01-llm-eval-harness/)** —— 校园问答助手 LLM 评测集

60 条用例（正常/边界/恶意）+ 零依赖评测脚本 + 评测报告 + CI 门禁。当前 qwen-turbo 真实跑测 **81.7%（49/60）**，最大失败模式是超长、高风险 badcase 是一条提示词泄漏。设计文档见项目内 `docs/评测方案设计.md`。

**[02-agent-trace-testing](./02-agent-trace-testing/)** —— Agent 工具调用轨迹测试 / 迭代上限护栏

15 条用例，判的不是"回答好不好"而是**轨迹对不对**：有没有幻觉工具、会不会死循环、上游失败还敢不敢说已经办妥。零依赖、不需要 API Key，一条命令跑完。当前 **有效用例 14/14**，另设 1 条刻意植入的死循环缺陷探针作为评估器回归哨兵。设计文档见项目内 `docs/评测方案设计.md`。

两个项目的共同点：都先跑出真实 badcase，再分「修被测对象」和「修判定规则」两条线分别处理，每次改完都有可复现的新数据。

在写的过程中（计划中）：

- **03-rag-eval**：文档问答 RAG 应用测试，覆盖检索命中率和回答忠实度
- **04-prompt-injection**：Prompt 注入专项用例集，从评测项目里拆出来加深

## 关于这个仓库

- 每个项目目录自带可运行的脚本和最近一次跑测的 `report.md`，clone 下来就能复现
- push 时 GitHub Actions 会自动跑一遍离线自检，保证仓库里的代码始终是能跑的状态
- 迭代记录写在各项目 README 里，包括踩过的坑和改法
