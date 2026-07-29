---
created: 2026-07-25
tags: [配置, Horizon, 自动抓取]
---

# 📡 Horizon 资讯自动抓取指南

本知识库已接入 [Horizon](https://github.com/Thysrael/Horizon) AI 新闻雷达，自动抓取 AI 和 Unity 领域的高分热点资讯。

## 自动抓取计划

| 任务 | 频率 | 时间 | 存入位置 | 筛选标准 |
|------|------|------|----------|----------|
| AI 热点 | 每天 | 18:00 | `01-AI高效使用/raw/` | AI 评分 ≥ 7.0 |
| Unity 热点 | 每周一 | 18:00 | `02-Unity学习/raw/` | AI 评分 ≥ 7.0 |

## 信息来源

### AI 领域
- **Hacker News** — 热门技术故事（min_score: 100）
- **Reddit** — r/MachineLearning, r/LocalLLaMA, r/artificial, r/singularity
- **RSS** — Simon Willison 博客、量子位、新智元
- **GitHub** — karpathy 动态、OpenAI SDK 发布
- **OSS Insight** — GitHub 上 AI 相关趋势项目
- **Google News** — AI 相关新闻

### Unity 领域
- **Reddit** — r/Unity3D, r/gamedev, r/Unity
- **RSS** — Unity 官方博客、Game Developer
- **GitHub** — Unity-Technologies 仓库发布
- **Google News** — Unity 引擎相关新闻

## 手动运行

### 抓取 AI 热点
```powershell
.\run-horizon.ps1 -Topic ai
```

### 抓取 Unity 热点
```powershell
.\run-horizon.ps1 -Topic unity
```

## 管理定时任务

### 查看任务状态
```powershell
Get-ScheduledTask -TaskName "Horizon-*"
```

### 手动触发一次
```powershell
Start-ScheduledTask -TaskName "Horizon-AI-Daily"
Start-ScheduledTask -TaskName "Horizon-Unity-Weekly"
```

### 禁用/启用
```powershell
# 禁用
Disable-ScheduledTask -TaskName "Horizon-AI-Daily"
# 启用
Enable-ScheduledTask -TaskName "Horizon-AI-Daily"
```

### 修改时间
```powershell
# 改为每天 8:00
$trigger = New-ScheduledTaskTrigger -Daily -At "08:00"
Set-ScheduledTask -TaskName "Horizon-AI-Daily" -Trigger $trigger
```

## 工作流程

```
Horizon 抓取 → DeepSeek AI 打分筛选 → 生成中英双语日报
     → 存入 raw/ 文件夹 → 告诉 Trae AI "整理 raw 文件夹"
     → AI 提炼为知识页存入 wiki/ → 知识库自生长
```

## 配置文件位置

| 文件 | 作用 |
|------|------|
| `.horizon/.env` | API Key（DeepSeek） |
| `.horizon/data/config-ai.json` | AI 抓取配置 |
| `.horizon/data/config-unity.json` | Unity 抓取配置 |
| `run-horizon.ps1` | 运行脚本 |

## 调整筛选标准

编辑 `.horizon/data/config-ai.json` 或 `config-unity.json`：

```json
{
  "filtering": {
    "ai_score_threshold": 7.0,  // 只保留 7 分以上
    "max_items": 20              // 最多 20 条
  }
}
```

评分标准：
- **9-10**: 重大突破、范式转移
- **7-8**: 重要进展、深度技术内容
- **5-6**: 值得了解但不紧急
- **3-4**: 一般性内容
- **0-2**: 噪音

## 常见问题

**Q: 日报没生成？**
- 检查网络连接
- 检查 DeepSeek API Key 是否有效
- 手动运行 `.\run-horizon.ps1 -Topic ai` 看错误信息

**Q: 想添加新的信息源？**
- 编辑对应的 config-*.json，在 sources 中添加
- 参考 [.horizon/docs/configuration.md](../.horizon/docs/configuration.md)

**Q: API 额度用完了？**
- 登录 https://platform.deepseek.com/ 查看余额
- 或切换到本地模型（Ollama），详见 [模型配置指南](模型配置指南.md)
