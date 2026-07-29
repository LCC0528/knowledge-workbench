# 云端知识库工作台

基于 GitHub Actions + GitHub Pages 的云端知识库，电脑不开机也能自动运行。

## 功能特性

- ✅ **云端定时抓取** - 每天 8:00 自动抓取 AI/Unity 热点
- ✅ **AI 智能筛选** - 自动打分、翻译、去重
- ✅ **微信推送** - 精简版日报推送到微信
- ✅ **网页版知识库** - GitHub Pages 部署，手机电脑都能访问
- ✅ **完全免费** - GitHub 免费额度足够使用

## 快速开始

### 1. 创建 GitHub 仓库

1. 登录 https://github.com
2. 点击右上角「+」→「New repository」
3. 仓库名填：`knowledge-workbench`
4. 选择 Public 或 Private
5. 勾选「Add a README file」
6. 点击「Create repository」

### 2. 配置仓库密钥

1. 进入仓库 → Settings → Secrets and variables → Actions
2. 点击「New repository secret」
3. 添加以下密钥：

| Name | Value | 说明 |
|------|-------|------|
| `DEEPSEEK_API_KEY` | 你的 API Key | 用于 AI 打分和翻译 |
| `PUSHPLUS_TOKEN` | 你的 PushPlus Token | 用于微信推送 |

### 3. 上传代码

下载本目录所有文件，上传到 GitHub 仓库：

```bash
# 克隆仓库
git clone https://github.com/你的用户名/knowledge-workbench.git

# 复制所有文件到仓库
复制 cloud-workbench 目录下所有文件到仓库

# 提交并推送
cd knowledge-workbench
git add .
git commit -m "Initial setup"
git push
```

### 4. 启用 GitHub Pages

1. 仓库 → Settings → Pages
2. Source 选择 `GitHub Actions`
3. 等待部署完成

### 5. 查看效果

- 网页版地址：`https://你的用户名.github.io/knowledge-workbench/`
- Actions 日志：仓库 → Actions 查看运行状态

## 目录结构

```
knowledge-workbench/
├── .github/workflows/
│   ├── fetch-ai.yml          # AI 日报抓取工作流
│   └── fetch-unity.yml       # Unity 周报抓取工作流
├── data/
│   ├── ai/                   # AI 日报存档
│   └── unity/                # Unity 周报存档
├── index.html                # 知识库主页
├── push_report.py            # 推送脚本
└── README.md
```

## 自定义

### 修改抓取时间

编辑 `.github/workflows/fetch-ai.yml`：
```yaml
schedule:
  - cron: '0 0 * * *'  # UTC 0点 = 北京时间 8点
```

### 修改数据源

编辑工作流中的抓取源配置。

## 技术栈

- **GitHub Actions** - 云端定时任务
- **Python** - 数据抓取和 AI 处理
- **GitHub Pages** - 网页托管
- **PushPlus** - 微信推送
- **DeepSeek API** - AI 打分和翻译