# GitHub 上传教程（零基础版）

> ✅ 状态更新：仓库已建好（github.com/lyz-0103/ai-testing-portfolio），Token 已配置，第一、二、三步已完成，直接从第四步开始即可。

---

## 第一步：注册 GitHub 账号

1. 打开 https://github.com/signup，用邮箱注册
2. 用户名建议用拼音（如 `lyz-dev`），它会出现在简历链接里：`github.com/lyz-dev`

## 第二步：在 GitHub 上新建仓库

1. 登录后点右上角 **+** → **New repository**
2. 填写：
   - Repository name：`ai-testing-portfolio`
   - Description：`AI 测试作品集：LLM 评测集 / RAG 测试 / Prompt 注入`
   - 选 **Public**（作品集必须公开，面试官要能直接看）
   - ⚠️ **不要**勾选 "Add a README"（本地已有，勾了会冲突）
3. 点 **Create repository**，页面先放着别关

## 第三步：配置身份 + 用 Personal Access Token 登录（一次性）

GitHub 已不支持账号密码推送，需要用 Token：

1. GitHub 右上角头像 → **Settings** → 左下 **Developer settings** → **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**
2. Note 随便填（如 `my-macbook`），Expiration 选 90 天，权限勾 **repo** 一项即可
3. 生成后**立刻复制** Token（`ghp_` 开头，只显示这一次）
4. 在终端（Terminal）执行（替换引号内内容）：

```bash
git config --global user.name "你的名字"
git config --global user.email "你的GitHub邮箱"
```

## 第四步：把本地作品集推上去

在终端里执行（一行一行来）：

```bash
cd /Users/lyz/WorkBuddy/2026-10-04-17-37-04/ai-testing-portfolio

git init                                    # 初始化本地仓库
git add .                                   # 暂存所有文件
git commit -m "feat: LLM 评测集项目 v0.1（20 条种子用例 + 自动化评测脚本）"

git branch -M main
git remote add origin https://github.com/<你的用户名>/ai-testing-portfolio.git
git push -u origin main                     # 弹出登录窗口时：用户名填 GitHub 用户名，密码粘贴刚才的 Token
```

成功后刷新 GitHub 仓库页面，就能看到 README、项目目录和评测脚本了。

## 第五步：之后每次更新（日常三连）

以后改了用例、脚本或报告，只需：

```bash
cd /Users/lyz/WorkBuddy/2026-10-04-17-37-04/ai-testing-portfolio
git add .
git commit -m "评测集扩到 60 条，新增恶意注入用例分类"
git push
```

Token 有效期内不会重复要求登录。

---

## 第六步：网络不通时的备用上传方案（已验证可用）

如果 `git push` 报 `Failed to connect` / `CONNECT tunnel failed`（github.com 被墙或代理只放行了 api.github.com），用仓库自带的 API 上传工具：

```bash
export GH_TOKEN="ghp_你的token"        # 需要 repo 权限的 classic token
cd /Users/lyz/WorkBuddy/2026-10-04-17-37-04/ai-testing-portfolio
python3 tools/upload_to_github.py          # 上传全部，内容未变的自动跳过
python3 tools/upload_to_github.py README.md  # 只更新指定文件
```

> 注意：API 上传和本地 git 提交是两条平行历史。等哪天 git push 恢复可用时，执行一次
> `git pull origin main --allow-unrelated-histories && git push` 即可合并（内容相同，不会冲突）。

## 常见问题

| 报错 | 原因 | 解决 |
|------|------|------|
| `Authentication failed` | Token 填错或过期 | 重新生成 Token，推送时密码处粘贴新 Token |
| `remote origin already exists` | 之前加过远程地址 | 执行 `git remote set-url origin https://github.com/<用户名>/ai-testing-portfolio.git` |
| `Updates were rejected` | GitHub 上有本地没有的提交（比如手动在网页上建过 README） | 执行 `git pull --rebase origin main` 后再 push |
| push 很慢/超时 | 网络问题 | 换个时间段重试，或使用代理 |

## 面试加分项（仓库上线后再做）

- [ ] GitHub 头像 + 简介 + 简历放仓库链接
- [ ] 把仓库 **Pin**（钉选）到主页
- [ ] README 里的报告数字与 `report.md` 保持同步（每次跑完更新）
- [ ] commit 信息用规范格式（`feat:` 新功能 / `fix:` 修复 / `docs:` 文档），体现工程素养
- [ ] 项目②（RAG 测试）上线后，在首页索引表补一行
