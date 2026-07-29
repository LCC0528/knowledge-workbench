# 部署指南

## 步骤 1：创建 GitHub 仓库

1. 登录 https://github.com
2. 点击右上角「+」→「New repository」
3. 仓库名填：`knowledge-workbench`
4. 选择 **Private**（私有，更安全）
5. **不要勾选** "Add a README file"
6. 点击「Create repository」

## 步骤 2：上传代码

### 方法 A：网页上传（最简单）

1. 进入新建的仓库页面
2. 点击仓库页面的 **"uploading an existing file"** 链接
3. 打开本地的 `cloud-workbench` 文件夹
4. **拖拽** 所有文件到网页上
   - 包括 `.github`、`data` 等文件夹
   - 如果看不到 `.github` 文件夹，在 Windows 文件夹选项里开启"显示隐藏文件"
5. 等待上传完成

### 方法 B：命令行上传

在电脑上打开 PowerShell：

```powershell
# 进入 cloud-workbench 目录
cd "c:\Users\李超超\Desktop\知识\cloud-workbench"

# 初始化 git
git init
git add .
git commit -m "Initial setup"

# 关联远程仓库（把 YOUR_USERNAME 换成你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/knowledge-workbench.git

# 推送
git branch -M main
git push -u origin main
```

## 步骤 3：配置密钥

1. 进入仓库 → **Settings** → **Secrets and variables** → **Actions**
2. 点击 **"New repository secret"**
3. 添加两个密钥：

**第一个密钥：**
- Name: `DEEPSEEK_API_KEY`
- Value: `sk-db60296abb8d48e49d89e2f3b00cfc99`（你的 DeepSeek API Key）

**第二个密钥：**
- Name: `PUSHPLUS_TOKEN`
- Value: `11ecf93d017846f9bcb299778bfef6af`（你的 PushPlus Token）

## 步骤 4：启用 GitHub Pages

1. 进入仓库 → **Settings** → **Pages**
2. Source 选择 `GitHub Actions`
3. 保存

## 步骤 5：首次运行

1. 进入仓库 → **Actions**
2. 点击左侧的 **"AI Daily Report"**
3. 点击右上角 **"Run workflow"** 按钮
4. 等待运行完成（约 5 分钟）
5. 查看运行结果

## 步骤 6：查看效果

运行成功后：

- 📱 **网页版**: `https://你的用户名.github.io/knowledge-workbench/`
- 💬 **微信**: 检查是否收到推送
- 📊 **历史报告**: `data/ai/` 和 `data/unity/` 文件夹

## 验证清单

- [x] 仓库已创建
- [x] 代码已上传
- [x] 两个密钥已配置
- [x] GitHub Pages 已启用
- [x] 首次运行成功
- [x] 网页可访问
- [x] 微信能收到推送

## 常见问题

### Q: Actions 运行失败？
检查仓库 → Actions → 具体运行 → Logs 查看错误信息

### Q: 网页显示 404？
等待 1-2 分钟让 GitHub Pages 部署完成

### Q: 没有收到微信推送？
检查 PushPlus Token 是否正确，查看 Actions 日志

### Q: 想修改推送时间？
编辑 `.github/workflows/fetch-ai.yml` 中的 cron 表达式：
```yaml
schedule:
  - cron: '0 0 * * *'  # 每天 UTC 0点 = 北京时间 8点
```

### Q: 想修改 AI 日报数据源？
编辑 `fetch_news.py` 中的 `TOPICS` 配置

## 更新本地代码后

如果你修改了本地代码，需要重新推送到 GitHub：

```powershell
cd "c:\Users\李超超\Desktop\知识\cloud-workbench"
git add .
git commit -m "Update"
git push
```

## 安全提醒

- 你的 API Key 和 Token 存储在 GitHub Secrets 中，不会暴露
- 建议仓库设为 **Private**（私有）
- 不要把密钥写在代码里

## 免费额度

- GitHub Actions: 每月 2000 分钟（足够使用）
- GitHub Pages: 无限流量
- PushPlus: 每月 200 条免费推送