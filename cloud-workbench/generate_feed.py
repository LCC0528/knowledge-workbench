#!/usr/bin/env python3
"""Generate ai-news.json feed from raw data for the AI news page"""

import os, json, glob
from datetime import datetime

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    all_items = []

    for topic in ['ai', 'unity']:
        pattern = f"data/{topic}/raw_*.json"
        for fpath in sorted(glob.glob(pattern)):
            date_str = os.path.basename(fpath).replace('raw_', '').replace('.json', '')
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                items = data.get('items', [])
                for item in items:
                    item['date'] = date_str
                    item['topic'] = topic
                all_items.extend(items)
            except:
                pass

    all_items.sort(key=lambda x: x.get('date', ''), reverse=True)

    feed = {
        'updated': today,
        'count': len(all_items),
        'items': all_items
    }

    os.makedirs('data', exist_ok=True)
    with open('data/ai-news.json', 'w', encoding='utf-8') as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)

    print(f"Feed generated: {len(all_items)} items -> data/ai-news.json")

if __name__ == '__main__':
    main()
