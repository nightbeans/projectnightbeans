#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Directories to process
const directories = ['posts', 'benedict', 'work'];

function convertToCleanUrl(dir) {
    if (!fs.existsSync(dir)) {
        console.log(`Directory ${dir} does not exist, skipping...`);
        return;
    }

    const files = fs.readdirSync(dir);

    files.forEach(file => {
        if (file.endsWith('.html') && file !== 'index.html') {
            const filePath = path.join(dir, file);
            const fileName = file.replace('.html', '');
            const newDir = path.join(dir, fileName);
            const newFilePath = path.join(newDir, 'index.html');

            // Create new directory
            if (!fs.existsSync(newDir)) {
                fs.mkdirSync(newDir, { recursive: true });
            }

            // Read the content
            let content = fs.readFileSync(filePath, 'utf8');

            // Update internal links in the content
            // Update relative paths for CSS and links
            if (dir === 'posts') {
                // Posts are one level deeper now (posts/slug/index.html instead of posts/slug.html)
                // So we need to update paths from ../ to ../../
                content = content.replace(/href="\.\.\/style\.css"/g, 'href="../../style.css"');
                content = content.replace(/href="\.\.\/index\.html"/g, 'href="../../"');
                content = content.replace(/href="\.\.\/blog\.html"/g, 'href="../../blog/"');
                content = content.replace(/href="\.\.\/work\.html"/g, 'href="../../work/"');
                content = content.replace(/href="\.\.\/benedict\.html"/g, 'href="../../benedict/"');
            } else if (dir === 'benedict' || dir === 'work') {
                // These files are also one level deeper now
                content = content.replace(/href="\.\.\/style\.css"/g, 'href="../../style.css"');
                content = content.replace(/href="\.\.\/index\.html"/g, 'href="../../"');
                content = content.replace(/href="\.\.\/blog\.html"/g, 'href="../../blog/"');
                content = content.replace(/href="\.\.\/work\.html"/g, 'href="../../work/"');
                content = content.replace(/href="\.\.\/benedict\.html"/g, 'href="../../benedict/"');
                content = content.replace(/href="benedict\.html"/g, 'href="../../benedict/"');
            }

            // Write to new location
            fs.writeFileSync(newFilePath, content);
            console.log(`Converted: ${filePath} -> ${newFilePath}`);

            // Delete old file
            fs.unlinkSync(filePath);
            console.log(`Deleted: ${filePath}`);
        }
    });
}

// Convert root HTML files
const rootFiles = ['index.html', 'blog.html', 'work.html', 'benedict.html'];
rootFiles.forEach(file => {
    if (file === 'index.html') return; // Keep index.html in root

    const fileName = file.replace('.html', '');
    const newDir = fileName;
    const newFilePath = path.join(newDir, 'index.html');

    if (!fs.existsSync(file)) {
        console.log(`${file} does not exist, skipping...`);
        return;
    }

    // Create directory
    if (!fs.existsSync(newDir)) {
        fs.mkdirSync(newDir, { recursive: true });
    }

    // Read and update content
    let content = fs.readFileSync(file, 'utf8');

    // Update links to remove .html
    content = content.replace(/href="index\.html"/g, 'href="/"');
    content = content.replace(/href="blog\.html"/g, 'href="/blog/"');
    content = content.replace(/href="work\.html"/g, 'href="/work/"');
    content = content.replace(/href="benedict\.html"/g, 'href="/benedict/"');

    // Update CSS path
    content = content.replace(/href="style\.css"/g, 'href="/style.css"');

    // Update post links
    content = content.replace(/href="posts\/([^"]+)\.html"/g, 'href="/posts/$1/"');
    content = content.replace(/href="benedict\/([^"]+)\.html"/g, 'href="/benedict/$1/"');
    content = content.replace(/href="work\/([^"]+)\.html"/g, 'href="/work/$1/"');

    // Write to new location
    fs.writeFileSync(newFilePath, content);
    console.log(`Converted: ${file} -> ${newFilePath}`);

    // Delete old file
    fs.unlinkSync(file);
    console.log(`Deleted: ${file}`);
});

// Update index.html
if (fs.existsSync('index.html')) {
    let content = fs.readFileSync('index.html', 'utf8');

    // Update links
    content = content.replace(/href="index\.html"/g, 'href="/"');
    content = content.replace(/href="blog\.html"/g, 'href="/blog/"');
    content = content.replace(/href="work\.html"/g, 'href="/work/"');
    content = content.replace(/href="benedict\.html"/g, 'href="/benedict/"');
    content = content.replace(/href="posts\/([^"]+)\.html"/g, 'href="/posts/$1/"');

    fs.writeFileSync('index.html', content);
    console.log('Updated: index.html');
}

// Convert subdirectory files
directories.forEach(dir => {
    console.log(`\nProcessing ${dir}/...`);
    convertToCleanUrl(dir);
});

// Update publish forms
const publishForms = ['publish-blog.html', 'publish-eggs.html', 'publish-work.html'];
publishForms.forEach(file => {
    if (!fs.existsSync(file)) return;

    let content = fs.readFileSync(file, 'utf8');

    // Update links
    content = content.replace(/href="index\.html"/g, 'href="/"');
    content = content.replace(/href="blog\.html"/g, 'href="/blog/"');
    content = content.replace(/href="work\.html"/g, 'href="/work/"');
    content = content.replace(/href="benedict\.html"/g, 'href="/benedict/"');

    fs.writeFileSync(file, content);
    console.log(`Updated: ${file}`);
});

console.log('\n✅ Conversion complete!');
console.log('\nNext steps:');
console.log('1. Test the site locally');
console.log('2. Update blog-posts.js, benedict-reviews.js, and work-items.js to use clean URLs');
console.log('3. Commit and push to GitHub');
