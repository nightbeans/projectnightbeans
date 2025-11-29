#!/usr/bin/env python3

import os
import shutil
import re

# Directories to process
directories = ['posts', 'benedict', 'work']

def convert_to_clean_url(dir_name):
    if not os.path.exists(dir_name):
        print(f"Directory {dir_name} does not exist, skipping...")
        return

    files = os.listdir(dir_name)

    for file in files:
        if file.endswith('.html') and file != 'index.html':
            file_path = os.path.join(dir_name, file)
            file_name = file.replace('.html', '')
            new_dir = os.path.join(dir_name, file_name)
            new_file_path = os.path.join(new_dir, 'index.html')

            # Create new directory
            os.makedirs(new_dir, exist_ok=True)

            # Read the content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Update internal links in the content
            if dir_name == 'posts':
                # Posts are one level deeper now (posts/slug/index.html instead of posts/slug.html)
                content = content.replace('href="../style.css"', 'href="../../style.css"')
                content = content.replace('href="../index.html"', 'href="../../"')
                content = content.replace('href="../blog.html"', 'href="../../blog/"')
                content = content.replace('href="../work.html"', 'href="../../work/"')
                content = content.replace('href="../benedict.html"', 'href="../../benedict/"')
            elif dir_name in ['benedict', 'work']:
                # These files are also one level deeper now
                content = content.replace('href="../style.css"', 'href="../../style.css"')
                content = content.replace('href="../index.html"', 'href="../../"')
                content = content.replace('href="../blog.html"', 'href="../../blog/"')
                content = content.replace('href="../work.html"', 'href="../../work/"')
                content = content.replace('href="../benedict.html"', 'href="../../benedict/"')
                content = content.replace('href="benedict.html"', 'href="../../benedict/"')

            # Write to new location
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Converted: {file_path} -> {new_file_path}")

            # Delete old file
            os.remove(file_path)
            print(f"Deleted: {file_path}")

# Convert root HTML files
root_files = ['blog.html', 'work.html', 'benedict.html']
for file in root_files:
    file_name = file.replace('.html', '')
    new_dir = file_name
    new_file_path = os.path.join(new_dir, 'index.html')

    if not os.path.exists(file):
        print(f"{file} does not exist, skipping...")
        continue

    # Create directory
    os.makedirs(new_dir, exist_ok=True)

    # Read and update content
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update links to remove .html
    content = re.sub(r'href="index\.html"', 'href="/"', content)
    content = re.sub(r'href="blog\.html"', 'href="/blog/"', content)
    content = re.sub(r'href="work\.html"', 'href="/work/"', content)
    content = re.sub(r'href="benedict\.html"', 'href="/benedict/"', content)

    # Update CSS path
    content = re.sub(r'href="style\.css"', 'href="/style.css"', content)

    # Update post links
    content = re.sub(r'href="posts/([^"]+)\.html"', r'href="/posts/\1/"', content)
    content = re.sub(r'href="benedict/([^"]+)\.html"', r'href="/benedict/\1/"', content)
    content = re.sub(r'href="work/([^"]+)\.html"', r'href="/work/\1/"', content)

    # Write to new location
    with open(new_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Converted: {file} -> {new_file_path}")

    # Delete old file
    os.remove(file)
    print(f"Deleted: {file}")

# Update index.html
if os.path.exists('index.html'):
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Update links
    content = re.sub(r'href="index\.html"', 'href="/"', content)
    content = re.sub(r'href="blog\.html"', 'href="/blog/"', content)
    content = re.sub(r'href="work\.html"', 'href="/work/"', content)
    content = re.sub(r'href="benedict\.html"', 'href="/benedict/"', content)
    content = re.sub(r'href="posts/([^"]+)\.html"', r'href="/posts/\1/"', content)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated: index.html')

# Convert subdirectory files
for directory in directories:
    print(f"\nProcessing {directory}/...")
    convert_to_clean_url(directory)

# Update publish forms
publish_forms = ['publish-blog.html', 'publish-eggs.html', 'publish-work.html']
for file in publish_forms:
    if not os.path.exists(file):
        continue

    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update links
    content = re.sub(r'href="index\.html"', 'href="/"', content)
    content = re.sub(r'href="blog\.html"', 'href="/blog/"', content)
    content = re.sub(r'href="work\.html"', 'href="/work/"', content)
    content = re.sub(r'href="benedict\.html"', 'href="/benedict/"', content)

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated: {file}")

print('\n✅ Conversion complete!')
print('\nNext steps:')
print('1. Test the site locally')
print('2. Update blog-posts.js, benedict-reviews.js, and work-items.js to use clean URLs')
print('3. Commit and push to GitHub')
