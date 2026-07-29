#!/usr/bin/env python3
"""
Generate summary in Chinese with AI translation
"""

import os
import sys
import json
import requests
from datetime import datetime
import argparse

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
TOPIC_NAMES = {
    'ai': 'AI 人工智能',
    'unity': 'Unity 游戏开发'
}

def translate_to_chinese(text):
    """Translate text to Chinese using AI"""
    if not DEEPSEEK_API_KEY:
        return text
    
    url = "https://api.deepseek.com/v1/chat/completions"
    prompt = f"Translate this to Chinese (just return the translation, nothing else):\n\n{text}"
    
    try:
        headers = {
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 500
        }
        resp = requests.post(url, headers=headers, json=data, timeout=15)
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Translation error: {e}")
    return text

def generate_summary(items, topic):
    """Generate a markdown summary"""
    today = datetime.now().strftime('%Y-%m-%d')
    topic_name = TOPIC_NAMES.get(topic, topic)
    
    lines = [
        f"# {topic_name} 日报 - {today}",
        "",
        f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"## 今日热点（共 {len(items)} 条）",
        "",
    ]
    
    for i, item in enumerate(items, 1):
        # Translate title to Chinese
        title_en = item['title']
        title_zh = translate_to_chinese(title_en) if any(c.isalpha() and ord(c) < 128 for c in title_en) else title_en
        
        score = item.get('ai_score', 0)
        source = item.get('source', 'Unknown')
        url = item.get('url', '#')
        
        lines.extend([
            f"### {i}. {title_zh} ({score:.1f}/10)",
            "",
            f"**原文**: [{title_en}]({url})",
            f"**来源**: {source}",
            "",
        ])
    
    lines.extend([
        "---",
        "",
        f"*由 AI 自动生成 | 数据来源: Hacker News, Reddit, RSS*",
    ])
    
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--topic', default='ai', choices=['ai', 'unity'])
    args = parser.parse_args()
    
    topic = args.topic
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Load raw data
    raw_file = f"data/{topic}/raw_{today}.json"
    if not os.path.exists(raw_file):
        print(f"Error: {raw_file} not found. Run fetch_news.py first.")
        sys.exit(1)
    
    with open(raw_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data.get('items', [])
    print(f"Loaded {len(items)} items from {raw_file}")
    
    # Generate summary
    print("Generating summary...")
    summary = generate_summary(items, topic)
    
    # Save summary
    os.makedirs(f"data/{topic}", exist_ok=True)
    
    # Save as latest
    latest_file = f"data/{topic}/latest.md"
    with open(latest_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    # Save dated copy
    dated_file = f"data/{topic}/{today}.md"
    with open(dated_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"Summary saved to {latest_file}")
    print(f"Summary saved to {dated_file}")
    print("\n" + summary[:500] + "...")

if __name__ == '__main__':
    main()