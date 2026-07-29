#!/usr/bin/env python3
"""
Push summary to WeChat via PushPlus
"""

import os
import sys
import json
import requests
from datetime import datetime
import argparse

PUSHPLUS_TOKEN = os.environ.get('PUSHPLUS_TOKEN', '')

def condense_report(file_path, max_items=6):
    """Condense the markdown report for WeChat"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    items = []
    current_item = None
    
    for line in lines:
        if line.startswith('### ') and current_item is not None:
            items.append(current_item)
            current_item = {'title': line, 'content': []}
        elif line.startswith('### '):
            current_item = {'title': line, 'content': []}
        elif current_item is not None:
            current_item['content'].append(line)
    
    if current_item is not None:
        items.append(current_item)
    
    # Take top items
    condensed = []
    for item in items[:max_items]:
        condensed.append(item['title'])
        condensed.extend(item['content'][:3])
        condensed.append('')
    
    return '\n'.join(condensed)

def push_to_wechat(title, content, token):
    """Push message to WeChat via PushPlus"""
    if not token:
        print("Warning: PUSHPLUS_TOKEN not set, skipping push")
        return False
    
    url = "https://www.pushplus.plus/send"
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": "html"
    }
    
    try:
        resp = requests.post(url, json=data, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('code') == 200:
                print(f"Push successful!")
                return True
            else:
                print(f"Push failed: {result}")
                return False
    except Exception as e:
        print(f"Push error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--topic', default='ai', choices=['ai', 'unity'])
    args = parser.parse_args()
    
    topic = args.topic
    today = datetime.now().strftime('%Y-%m-%d')
    topic_names = {'ai': 'AI', 'unity': 'Unity'}
    
    # Find latest report
    report_file = f"data/{topic}/latest.md"
    if not os.path.exists(report_file):
        print(f"Error: {report_file} not found")
        sys.exit(1)
    
    # Condense report
    print("Condensing report for WeChat...")
    condensed = condense_report(report_file)
    
    if not condensed:
        print("No content to push")
        return
    
    # Push to WeChat
    title = f"📰 {topic_names[topic]} 日报 {today}"
    print(f"Pushing to WeChat: {title}")
    print(f"Content length: {len(condensed)} chars")
    
    success = push_to_wechat(title, condensed, PUSHPLUS_TOKEN)
    
    if success:
        print("✅ WeChat push completed!")
    else:
        print("❌ Push failed, check your token")

if __name__ == '__main__':
    main()