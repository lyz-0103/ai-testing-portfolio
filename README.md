# 🧪 AI 测试作品集 · AI Testing Portfolio

> 应届生求职作品集：面向 **AI/LLM 测试方向**，核心证明「评测思维 + badcase 归因 + 自动化落地」能力，而非工具堆砌。

## 项目索引

| # | 项目 | 证明什么 | 状态 |
|---|------|----------|------|
| 1 | [LLM 评测集与自动化评测脚本](./01-llm-eval-harness/) | 评测集构建、批量跑测、badcase 分类、评测报告产出 | ✅ 核心项目 |

> 规划中：`02-rag-eval`（RAG 应用质量测试）、`03-prompt-injection`（Prompt 注入红队用例集），完成一个上线一个。

## 怎么看这个作品集

每个项目目录下的 README 都回答四个问题：

1. **测什么** —— 被测对象与场景定义
2. **怎么定义通过** —— 评测标准与用例分类逻辑
3. **结果如何** —— 跑测数据、通过率、典型 badcase
4. **踩坑复盘** —— 如果重做会怎么改进

## 复现方式

```bash
git clone https://github.com/lyz-0103/ai-testing-portfolio.git
cd ai-testing-portfolio/01-llm-eval-harness
python3 eval_runner.py --mock          # 无需 API Key，直接体验
```

---

*维护者：<你的名字> · 计算机类应届 · 求职方向：AI 测试 / 软件测试*
