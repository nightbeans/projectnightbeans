#!/usr/bin/env python3

import os
import re
import json
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = {}
        self.current_tag = None
        self.current_attrs = {}
        self.capture_text = False
        self.captured_text = []
        self.in_class = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)

        # Capture h1 text
        if tag == 'h1':
            self.capture_text = True
            self.captured_text = []

        # Capture time datetime
        if tag == 'time' and 'datetime' in self.current_attrs:
            self.data['datetime'] = self.current_attrs['datetime']
            self.capture_text = True
            self.captured_text = []

        # Track class context
        if 'class' in self.current_attrs:
            self.in_class = self.current_attrs['class']
            if 'benedict-rating' in self.in_class:
                self.capture_text = True
                self.captured_text = []
            elif 'benedict-fellow' in self.in_class:
                self.capture_text = True
                self.captured_text = []
            elif 'post-content' in self.in_class:
                self.data['in_content'] = True
                self.data['paragraphs'] = []

        # Capture paragraphs in content
        if tag == 'p' and self.data.get('in_content'):
            self.capture_text = True
            self.captured_text = []

    def handle_endtag(self, tag):
        if tag == 'h1' and self.capture_text:
            self.data['title'] = ''.join(self.captured_text).strip()
            self.capture_text = False

        if tag == 'time' and self.capture_text:
            self.capture_text = False

        if tag == 'p' and self.data.get('in_content') and self.capture_text:
            text = ''.join(self.captured_text).strip()
            if text:
                self.data['paragraphs'].append(text)
            self.capture_text = False

        if tag == 'div' and self.in_class:
            if 'benedict-rating' in self.in_class and self.capture_text:
                self.data['rating_text'] = ''.join(self.captured_text).strip()
                self.capture_text = False
            elif 'benedict-fellow' in self.in_class and self.capture_text:
                self.data['fellow_text'] = ''.join(self.captured_text).strip()
                self.capture_text = False
            elif 'post-content' in self.in_class:
                self.data['in_content'] = False
            self.in_class = None

    def handle_data(self, data):
        if self.capture_text:
            self.captured_text.append(data)

def format_date_display(date_str):
    """Convert YYYY-MM-DD to 'Month Day Year'"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%B %d %Y')
    except:
        return date_str

def parse_html_file(file_path):
    """Parse HTML file and extract metadata"""
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    parser = SimpleHTMLParser()
    parser.feed(html_content)

    # Extract coordinates from script
    script_match = re.search(r'setView\(\[(-?\d+\.\d+),\s*(-?\d+\.\d+)\]', html_content)
    if script_match:
        parser.data['lat'] = float(script_match.group(1))
        parser.data['lng'] = float(script_match.group(2))

    return parser.data

def generate_benedict_reviews():
    """Generate benedict-reviews.js from HTML files"""
    print('Generating benedict-reviews.js...')

    benedict_dir = Path('benedict')
    if not benedict_dir.exists():
        print('Benedict directory not found, skipping...')
        return

    reviews = []

    for item in benedict_dir.iterdir():
        if not item.is_dir():
            continue

        index_path = item / 'index.html'
        if not index_path.exists():
            continue

        try:
            data = parse_html_file(index_path)

            title = data.get('title', item.name)
            datetime_str = data.get('datetime', '')
            date = datetime_str.split(' ')[0] if datetime_str else ''
            date_display = format_date_display(date)

            # Count egg emojis for rating
            rating_text = data.get('rating_text', '🍳')
            rating = rating_text.count('🍳')

            # Get summary (last non-empty paragraph)
            paragraphs = data.get('paragraphs', [])
            summary = paragraphs[-1] if paragraphs else ''

            # Extract fellow name
            fellow_text = data.get('fellow_text', '')
            fellow_match = re.search(r'Benedict Fellow:\s*(.+)', fellow_text)
            fellow = fellow_match.group(1).strip() if fellow_match else 'Joel Delaney'

            review = {
                'title': title,
                'date': date,
                'dateDisplay': date_display,
                'rating': rating,
                'ratingDisplay': '🍳',
                'summary': summary,
                'url': f'/benedict/{item.name}/',
                'lat': data.get('lat', 0),
                'lng': data.get('lng', 0),
                'fellow': fellow
            }

            reviews.append(review)
            print(f'  ✓ Processed: {title}')

        except Exception as e:
            print(f'  ✗ Error processing {item.name}: {e}')

    # Sort by date (newest first)
    reviews.sort(key=lambda x: x['date'], reverse=True)

    # Generate JavaScript file
    js_content = f"""// Benedict Reviews Data
// Add new reviews to this array - they will automatically appear on benedict.html
// Reviews are automatically sorted by date (newest first)

const benedictReviews = {json.dumps(reviews, indent=4, ensure_ascii=False)};
"""

    with open('benedict-reviews.js', 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f'✅ Generated benedict-reviews.js with {len(reviews)} reviews\n')

def generate_blog_posts():
    """Generate blog-posts.js from HTML files"""
    print('Generating blog-posts.js...')

    posts_dir = Path('posts')
    if not posts_dir.exists():
        print('Posts directory not found, skipping...')
        return []

    posts = []

    for item in posts_dir.iterdir():
        if not item.is_dir():
            continue

        index_path = item / 'index.html'
        if not index_path.exists():
            continue

        try:
            data = parse_html_file(index_path)

            title = data.get('title', item.name)
            datetime_str = data.get('datetime', '')
            date = datetime_str.split(' ')[0] if datetime_str else ''
            date_display = format_date_display(date)

            # Get excerpt (first paragraph)
            paragraphs = data.get('paragraphs', [])
            excerpt = paragraphs[0] if paragraphs else ''

            post = {
                'title': title,
                'url': f'/posts/{item.name}/',
                'date': date,
                'dateDisplay': date_display,
                'excerpt': excerpt
            }

            posts.append(post)
            print(f'  ✓ Processed: {title}')

        except Exception as e:
            print(f'  ✗ Error processing {item.name}: {e}')

    # Sort by date (newest first)
    posts.sort(key=lambda x: x['date'], reverse=True)

    # Generate JavaScript file
    js_content = f"""// Blog Posts Data
// This file is automatically generated by build.py
// Do not edit manually - run 'python3 build.py' to regenerate

const blogPosts = {json.dumps(posts, indent=4, ensure_ascii=False)};
"""

    with open('blog-posts.js', 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f'✅ Generated blog-posts.js with {len(posts)} posts\n')
    return posts

def update_homepage(posts):
    """Update homepage with latest blog post"""
    print('Updating homepage...')

    if not posts:
        print('No posts found, skipping homepage update...')
        return

    index_path = Path('index.html')
    if not index_path.exists():
        print('index.html not found, skipping...')
        return

    latest_post = posts[0]

    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Find and replace the latest-post article content
    pattern = r'<article class="latest-post">.*?</article>'
    replacement = f'''<article class="latest-post">
            <h2><a href="{latest_post['url']}">{latest_post['title']}</a></h2>
            <time datetime="{latest_post['date']}">{latest_post['dateDisplay']}</time>
            <div class="post-preview-content">
                <p>{latest_post['excerpt']}</p>
            </div>
            <a href="{latest_post['url']}" class="read-more">Read more →</a>
        </article>'''

    html = re.sub(pattern, replacement, html, flags=re.DOTALL)

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'✅ Updated homepage with latest post: {latest_post["title"]}\n')

# Run all generators
if __name__ == '__main__':
    print('🔨 Building site...\n')
    generate_benedict_reviews()
    posts = generate_blog_posts()
    update_homepage(posts)
    print('✅ Build complete!\n')
