# AI 测试作品集

面向 AI/LLM 测试方向的个人作品集。目前包含一个核心项目，后续按计划补齐 RAG 应用测试和 Prompt 注入专项。

![eval](https://github.com/lyz-0103/ai-testing-portfolio/actions/workflows/eval.yml/badge.svg)

## 项目

**[01-llm-eval-harness](./01-llm-eval-harness/)** —— 校园问答助手 LLM 评测集

60 条用例（正常/边界/恶意）+ 零依赖评测脚本 + 评测报告 + CI 门禁。设计文档见项目内 `docs/评测方案设计.md`，包含用例分类依据、判定规则取舍和已知局限。

在写的过程中（计划中）：

- **02-rag-eval**：文档问答 RAG 应用测试，覆盖检索命中率和回答忠实度
- **03-prompt-injection**：Prompt 注入专项用例集，从评测项目里拆出来加深

## 关于这个仓库

- 每个项目目录自带可运行的脚本和最近一次跑测的 `report.md`，clone 下来就能复现
- push 时 GitHub Actions 会自动跑一遍离线自检，保证仓库里的代码始终是能跑的状态
- 迭代记录写在各项目 README 里，包括踩过的坑和改法
