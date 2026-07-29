#!/usr/bin/env python3
"""
Update the index.html with latest reports
"""

import os
import json
from datetime import datetime

def get_latest_reports():
    """Get the latest reports for each topic"""
    reports = {}
    topics = ['ai', 'unity']
    
    for topic in topics:
        folder = f"data/{topic}"
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if f.endswith('.md') and f != 'latest.md']
            if files:
                files.sort(reverse=True)
                latest_file = os.path.join(folder, files[0])
                with open(latest_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                reports[topic] = {
                    'date': files[0].replace('.md', ''),
                    'content': content[:2000],  # Limit content size
                    'file': files[0]
                }
    
    return reports

def generate_index_html(reports):
    """Generate the main index.html"""
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    ai_content = ''
    unity_content = ''
    
    if 'ai' in reports:
        ai_content = f'''
        <div class="card">
            <h2>🤖 AI 人工智能</h2>
            <div class="meta">更新于 {reports['ai']['date']}</div>
            <div class="content">
                {reports['ai']['content']}
            </div>
        </div>'''
    
    if 'unity' in reports:
        unity_content = f'''
        <div class="card">
            <h2>🎮 Unity 游戏开发</h2>
            <div class="meta">更新于 {reports['unity']['date']}</div>
            <div class="content">
                {reports['unity']['content']}
            </div>
        </div>'''
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>云端知识库工作台</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding: 30px 0;
            background: white;
            border-radius: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(76, 175, 80, 0.1);
        }}
        header h1 {{ color: #2e7d32; font-size: 28px; }}
        header .sub {{ color: #66bb6a; font-size: 14px; margin-top: 8px; }}
        .last-update {{ color: #81c784; font-size: 12px; margin-top: 12px; }}
        .card {{
            background: white;
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(76, 175, 80, 0.1);
        }}
        .card h2 {{ color: #2e7d32; margin-bottom: 12px; font-size: 22px; }}
        .meta {{ color: #81c784; font-size: 13px; margin-bottom: 16px; }}
        .content {{ line-height: 1.8; color: #333; font-size: 15px; }}
        .content h3 {{ color: #1b5e20; margin: 20px 0 10px; }}
        .content a {{ color: #4caf50; text-decoration: none; }}
        .content a:hover {{ text-decoration: underline; }}
        .content p {{ margin: 8px 0; }}
        .empty {{
            text-align: center;
            padding: 60px 20px;
            color: #a5d6a7;
        }}
        .empty .icon {{ font-size: 64px; margin-bottom: 16px; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}
        .stat {{
            background: white;
            border-radius: 16px;
            padding: 20px 12px;
            text-align: center;
            box-shadow: 0 2px 12px rgba(76, 175, 80, 0.1);
        }}
        .stat .num {{ font-size: 28px; font-weight: 700; color: #2e7d32; }}
        .stat .label {{ font-size: 12px; color: #81c784; margin-top: 4px; }}
        footer {{
            text-align: center;
            padding: 20px;
            color: #a5d6a7;
            font-size: 12px;
        }}
        @media (max-width: 600px) {{
            body {{ padding: 10px; }}
            header {{ padding: 20px 16px; }}
            header h1 {{ font-size: 22px; }}
            .card {{ padding: 16px; }}
            .stats {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 云端知识库工作台</h1>
            <div class="sub">AI 自动抓取 · 智能筛选 · 定时推送</div>
            <div class="last-update">最后更新: {today}</div>
        </header>
        
        <div class="stats">
            <div class="stat">
                <div class="num">{len(reports)}</div>
                <div class="label">领域覆盖</div>
            </div>
            <div class="stat">
                <div class="num">2</div>
                <div class="label">每日更新</div>
            </div>
            <div class="stat">
                <div class="num">∞</div>
                <div class="label">免费使用</div>
            </div>
        </div>
        
        {ai_content if ai_content else '''
        <div class="card">
            <div class="empty">
                <div class="icon">🤖</div>
                <h3>AI 日报</h3>
                <p>等待首次抓取...</p>
            </div>
        </div>'''}
        
        {unity_content if unity_content else '''
        <div class="card">
            <div class="empty">
                <div class="icon">🎮</div>
                <h3>Unity 周报</h3>
                <p>等待首次抓取（每周一）...</p>
            </div>
        </div>'''}
        
        <footer>
            Powered by GitHub Actions · 每天 8:00 自动更新
        </footer>
    </div>
</body>
</html>'''
    
    return html

def main():
    reports = get_latest_reports()
    html = generate_index_html(reports)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Updated index.html with {len(reports)} reports")
    print("Reports available:", list(reports.keys()))

if __name__ == '__main__':
    main()