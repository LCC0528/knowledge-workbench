#!/usr/bin/env python3
"""
Fetch AI/Unity news from multiple sources
"""

import os
import sys
import json
import requests
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import argparse
import re
import time
import hashlib

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
TOPICS = {
    'ai': {
        'sources': [
            'https://news.ycombinator.com/rss',
            'https://www.reddit.com/r/artificial/.rss',
            'https://www.reddit.com/r/MachineLearning/.rss',
            'https://www.reddit.com/r/LocalLLaMA/.rss',
            'https://newsapi.org/v2/everything?q=AI+artificial+intelligence&sortBy=publishedAt&pageSize=10&language=en',
        ],
        'keywords': ['AI', 'artificial intelligence', 'LLM', 'GPT', 'deep learning', 'machine learning', 'model', 'agent'],
        'folder': 'data/ai'
    },
    'unity': {
        'sources': [
            'https://www.reddit.com/r/Unity3D/.rss',
            'https://www.reddit.com/r/IndieGameDev/.rss',
            'https://www.reddit.com/r/gamedev/.rss',
            'https://newsapi.org/v2/everything?q=Unity+game+development&sortBy=publishedAt&pageSize=10&language=en',
        ],
        'keywords': ['Unity', 'game engine', 'gamedev', 'indie game', 'game development'],
        'folder': 'data/unity'
    }
}

def fetch_hackernews(topic):
    """Fetch from Hacker News"""
    items = []
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            story_ids = resp.json()[:30]
            
            for sid in story_ids:
                try:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                    story_resp = requests.get(story_url, timeout=5)
                    if story_resp.status_code == 200:
                        story = story_resp.json()
                        title = story.get('title', '').lower()
                        if any(kw.lower() in title for kw in TOPICS[topic]['keywords']):
                            items.append({
                                'title': story.get('title', ''),
                                'url': story.get('url', f"https://news.ycombinator.com/item?id={sid}"),
                                'source': 'Hacker News',
                                'score': story.get('score', 0),
                                'text': story.get('text', '')
                            })
                except:
                    pass
                time.sleep(0.1)
    except Exception as e:
        print(f"Error fetching HN: {e}")
    return items

def fetch_reddit(topic):
    """Fetch from Reddit"""
    items = []
    subs = {
        'ai': ['artificial', 'MachineLearning', 'LocalLLaMA'],
        'unity': ['Unity3D', 'gamedev', 'IndieGameDev']
    }
    for sub in subs.get(topic, []):
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=15"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for post in data.get('data', {}).get('children', []):
                    d = post.get('data', {})
                    items.append({
                        'title': d.get('title', ''),
                        'url': f"https://reddit.com{d.get('permalink', '')}",
                        'source': f"Reddit r/{sub}",
                        'score': d.get('score', 0),
                        'text': d.get('selftext', '')[:200]
                    })
        except Exception as e:
            print(f"Error fetching Reddit r/{sub}: {e}")
    return items

def fetch_rss_feeds(topic):
    """Fetch from RSS feeds"""
    items = []
    rss_feeds = {
        'ai': [
            'https://www.marktechpost.com/feed/',
            'https://www.artificialintelligence-news.com/feed/',
        ],
        'unity': [
            'https://blog.unity.com/feed',
        ]
    }
    for feed_url in rss_feeds.get(topic, []):
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                items.append({
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'source': feed_url.split('/')[2] if '/' in feed_url else 'RSS',
                    'score': 0,
                    'text': entry.get('summary', '')[:200]
                })
        except Exception as e:
            print(f"Error fetching RSS: {e}")
    return items

def score_with_ai(item, topic):
    """Score an item using AI API"""
    if not DEEPSEEK_API_KEY:
        return 5.0  # Default score if no API key
    
    url = "https://api.deepseek.com/v1/chat/completions"
    prompt = f"""Rate this {topic} news item from 0-10 based on its importance and relevance:

Title: {item['title']}
Source: {item['source']}

Consider:
- Is this a significant event in {topic}?
- Does it have practical value?
- Is it a new development or just a minor update?

Respond with ONLY a number from 0-10."""

    try:
        headers = {
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 10
        }
        resp = requests.post(url, headers=headers, json=data, timeout=15)
        if resp.status_code == 200:
            content = resp.json()['choices'][0]['message']['content'].strip()
            score = float(re.search(r'[\d.]+', content).group())
            return min(10, max(0, score))
    except Exception as e:
        print(f"Error scoring: {e}")
    
    # Score based on popularity
    base_score = 5.0
    if item.get('score', 0) > 1000:
        base_score = 8.0
    elif item.get('score', 0) > 500:
        base_score = 7.0
    elif item.get('score', 0) > 100:
        base_score = 6.0
    return base_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--topic', default='ai', choices=['ai', 'unity'])
    args = parser.parse_args()
    
    topic = args.topic
    print(f"Fetching {topic} news...")
    
    # Fetch from all sources
    all_items = []
    all_items.extend(fetch_hackernews(topic))
    all_items.extend(fetch_reddit(topic))
    all_items.extend(fetch_rss_feeds(topic))
    
    print(f"Fetched {len(all_items)} items")
    
    # Deduplicate by title similarity
    seen = set()
    unique_items = []
    for item in all_items:
        title_hash = hashlib.md5(item['title'].encode()).hexdigest()[:8]
        if title_hash not in seen:
            seen.add(title_hash)
            unique_items.append(item)
    
    print(f"After dedup: {len(unique_items)} items")
    
    # Score items
    print("Scoring items with AI...")
    for i, item in enumerate(unique_items):
        item['ai_score'] = score_with_ai(item, topic)
        if (i + 1) % 5 == 0:
            print(f"  Scored {i+1}/{len(unique_items)}")
    
    # Filter and sort
    qualified = [item for item in unique_items if item['ai_score'] >= 6.0]
    qualified.sort(key=lambda x: x['ai_score'], reverse=True)
    
    # Take top items
    top_items = qualified[:8]
    print(f"Selected {len(top_items)} items with score >= 6.0")
    
    # Save raw data
    os.makedirs(TOPICS[topic]['folder'], exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    
    with open(f"{TOPICS[topic]['folder']}/raw_{today}.json", 'w', encoding='utf-8') as f:
        json.dump({
            'date': today,
            'topic': topic,
            'items': top_items
        }, f, ensure_ascii=False, indent=2)
    
    print(f"Saved raw data to {TOPICS[topic]['folder']}/raw_{today}.json")
    return top_items

if __name__ == '__main__':
    main()