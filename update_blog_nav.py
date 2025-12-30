#!/usr/bin/env python3
"""Update all blog posts with navigation arrows and clickable titles"""

import os
import re
from pathlib import Path

def update_blog_post(file_path):
    """Update a single blog post with new navigation structure"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract the current title from post-header section
    header_section = re.search(r'<header class="post-header">(.+?)</header>', content, re.DOTALL)
    if not header_section:
        print(f"Warning: Could not find post-header in {file_path}")
        return False

    title_match = re.search(r'<h1>(?:<a[^>]*>)?(.+?)(?:</a>)?</h1>', header_section.group(1))
    if not title_match:
        print(f"Warning: Could not find title in post-header in {file_path}")
        return False

    title = title_match.group(1)

    # Find the post-nav section to get prev/next links
    nav_match = re.search(r'<nav class="post-nav">\s*(.+?)\s*</nav>', content, re.DOTALL)

    prev_link = None
    next_link = None

    if nav_match:
        nav_content = nav_match.group(1)
        # Find previous link (← at start) - extract just the folder name
        prev_match = re.search(r'<a href="\.\./([^"]+)/">←', nav_content)
        if prev_match:
            prev_link = prev_match.group(1)
            print(f"  Found prev: {prev_link}")

        # Find next link (→ at end) - extract just the folder name
        next_match = re.search(r'<a href="\.\./([^"]+)/">[^<]*→</a>', nav_content)
        if next_match:
            next_link = next_match.group(1)
            print(f"  Found next: {next_link}")
    else:
        print(f"  No nav-match found in {file_path}")

    # Build navigation arrows HTML
    arrows_html = '<div class="nav-arrows">\n                    '

    if next_link:
        arrows_html += f'<a href="../{next_link}/" class="nav-arrow">→</a>\n                    '
    else:
        arrows_html += '<a href="#" class="nav-arrow disabled">→</a>\n                    '

    if prev_link:
        arrows_html += f'<a href="../{prev_link}/" class="nav-arrow">←</a>\n                '
    else:
        arrows_html += '<a href="#" class="nav-arrow disabled">←</a>\n                '

    arrows_html += '</div>'

    # Update the header section
    old_header = re.search(
        r'<header class="post-header">(.+?)</header>',
        content,
        re.DOTALL
    )

    if not old_header:
        print(f"Warning: Could not find post-header in {file_path}")
        return False

    # Extract time element
    time_match = re.search(r'<time[^>]*>.*?</time>', old_header.group(1))
    time_elem = time_match.group(0) if time_match else ''

    new_header = f'''<header class="post-header">
                <div>
                    <h1><a href="../../blog/">{title}</a></h1>
                    {time_elem}
                </div>
                {arrows_html}
            </header>'''

    # Build bottom navigation HTML (same arrows but horizontal)
    bottom_nav_html = '\n                <div class="bottom-nav">\n                    '

    if prev_link:
        bottom_nav_html += f'<a href="../{prev_link}/" class="nav-arrow">←</a>\n                    '
    else:
        bottom_nav_html += '<a href="#" class="nav-arrow disabled">←</a>\n                    '

    if next_link:
        bottom_nav_html += f'<a href="../{next_link}/" class="nav-arrow">→</a>\n                '
    else:
        bottom_nav_html += '<a href="#" class="nav-arrow disabled">→</a>\n                '

    bottom_nav_html += '</div>'

    # Replace the old header with the new one
    content = content.replace(old_header.group(0), new_header)

    # Remove the old post-nav section at the bottom
    content = re.sub(r'\s*<nav class="post-nav">.*?</nav>', '', content, flags=re.DOTALL)

    # Add bottom navigation before the closing </div> of post-content
    content = re.sub(
        r'(</div>\s*</article>)',
        bottom_nav_html + r'\n            \1',
        content
    )

    # Write the updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def main():
    """Update all blog posts"""
    posts_dir = Path('/Users/joeldelaney/project-nightbeans/posts')

    if not posts_dir.exists():
        print(f"Error: Posts directory not found: {posts_dir}")
        return

    updated_count = 0
    failed_count = 0

    for post_dir in sorted(posts_dir.iterdir()):
        if not post_dir.is_dir():
            continue

        index_file = post_dir / 'index.html'
        if not index_file.exists():
            continue

        print(f"Updating {post_dir.name}...")
        if update_blog_post(index_file):
            updated_count += 1
        else:
            failed_count += 1

    print(f"\nComplete! Updated {updated_count} posts, {failed_count} failed")

if __name__ == '__main__':
    main()
