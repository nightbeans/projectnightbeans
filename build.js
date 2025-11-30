#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

// Helper function to parse HTML files
function parseHTML(filePath) {
    const html = fs.readFileSync(filePath, 'utf8');
    const dom = new JSDOM(html);
    return dom.window.document;
}

// Helper function to format date display
function formatDateDisplay(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

// 1. Generate benedict-reviews.js
function generateBenedictReviews() {
    console.log('Generating benedict-reviews.js...');

    const benedictDir = 'benedict';
    const reviews = [];

    if (!fs.existsSync(benedictDir)) {
        console.log('Benedict directory not found, skipping...');
        return;
    }

    const dirs = fs.readdirSync(benedictDir);

    dirs.forEach(dir => {
        const indexPath = path.join(benedictDir, dir, 'index.html');

        // Skip benedict/index.html (the main page)
        if (dir === 'index.html' || !fs.existsSync(indexPath)) {
            return;
        }

        try {
            const doc = parseHTML(indexPath);

            // Extract title
            const titleEl = doc.querySelector('h1');
            const title = titleEl ? titleEl.textContent.trim() : dir;

            // Extract date
            const timeEl = doc.querySelector('time');
            const datetime = timeEl ? timeEl.getAttribute('datetime') : '';
            const date = datetime.split(' ')[0]; // Get just YYYY-MM-DD part
            const dateDisplay = formatDateDisplay(date);

            // Extract rating (count egg emojis)
            const ratingEl = doc.querySelector('.benedict-rating');
            const ratingText = ratingEl ? ratingEl.textContent.trim() : '🍳';
            const rating = (ratingText.match(/🍳/g) || []).length;
            const ratingDisplay = '🍳';

            // Extract summary (first paragraph)
            const contentDiv = doc.querySelector('.post-content');
            const paragraphs = contentDiv ? Array.from(contentDiv.querySelectorAll('p')) : [];
            const firstPara = paragraphs.filter(p => p.textContent.trim().length > 0)[0];
            const summary = firstPara ? firstPara.textContent.trim() : '';

            // Extract coordinates from map script
            const scripts = Array.from(doc.querySelectorAll('script'));
            let lat = 0, lng = 0;

            scripts.forEach(script => {
                const content = script.textContent;
                const mapMatch = content.match(/setView\(\[(-?\d+\.\d+),\s*(-?\d+\.\d+)\]/);
                if (mapMatch) {
                    lat = parseFloat(mapMatch[1]);
                    lng = parseFloat(mapMatch[2]);
                }
            });

            // Extract fellow
            const fellowEl = doc.querySelector('.benedict-fellow');
            const fellowText = fellowEl ? fellowEl.textContent : '';
            const fellowMatch = fellowText.match(/Benedict Fellow:\s*(.+)/);
            const fellow = fellowMatch ? fellowMatch[1].trim() : 'Joel Delaney';

            reviews.push({
                title,
                date,
                dateDisplay,
                rating,
                ratingDisplay,
                summary,
                url: `/benedict/${dir}/`,
                lat,
                lng,
                fellow
            });

            console.log(`  ✓ Processed: ${title}`);
        } catch (error) {
            console.error(`  ✗ Error processing ${dir}:`, error.message);
        }
    });

    // Sort by date (newest first)
    reviews.sort((a, b) => new Date(b.date) - new Date(a.date));

    // Generate JavaScript file
    const fileContent = `// Benedict Reviews Data
// Add new reviews to this array - they will automatically appear on benedict.html
// Reviews are automatically sorted by date (newest first)

const benedictReviews = ${JSON.stringify(reviews, null, 4)};
`;

    fs.writeFileSync('benedict-reviews.js', fileContent);
    console.log(`✅ Generated benedict-reviews.js with ${reviews.length} reviews\n`);
}

// 2. Generate blog-posts.js
function generateBlogPosts() {
    console.log('Generating blog-posts.js...');

    const postsDir = 'posts';
    const posts = [];

    if (!fs.existsSync(postsDir)) {
        console.log('Posts directory not found, skipping...');
        return;
    }

    const dirs = fs.readdirSync(postsDir);

    dirs.forEach(dir => {
        const indexPath = path.join(postsDir, dir, 'index.html');

        if (!fs.existsSync(indexPath)) {
            return;
        }

        try {
            const doc = parseHTML(indexPath);

            // Extract title
            const titleEl = doc.querySelector('h1');
            const title = titleEl ? titleEl.textContent.trim() : dir;

            // Extract date
            const timeEl = doc.querySelector('time');
            const datetime = timeEl ? timeEl.getAttribute('datetime') : '';
            const date = datetime.split(' ')[0]; // Get just YYYY-MM-DD part
            const dateDisplay = formatDateDisplay(date);

            // Extract excerpt (first paragraph)
            const contentDiv = doc.querySelector('.post-content');
            const firstPara = contentDiv ? contentDiv.querySelector('p') : null;
            const excerpt = firstPara ? firstPara.textContent.trim() : '';

            posts.push({
                title,
                url: `/posts/${dir}/`,
                date,
                dateDisplay,
                excerpt
            });

            console.log(`  ✓ Processed: ${title}`);
        } catch (error) {
            console.error(`  ✗ Error processing ${dir}:`, error.message);
        }
    });

    // Sort by date (newest first)
    posts.sort((a, b) => new Date(b.date) - new Date(a.date));

    // Generate JavaScript file
    const fileContent = `// Blog Posts Data
// This file is automatically generated by build.js
// Do not edit manually - run 'node build.js' to regenerate

const blogPosts = ${JSON.stringify(posts, null, 4)};
`;

    fs.writeFileSync('blog-posts.js', fileContent);
    console.log(`✅ Generated blog-posts.js with ${posts.length} posts\n`);

    return posts;
}

// 3. Update homepage with latest post
function updateHomepage(posts) {
    console.log('Updating homepage...');

    if (!posts || posts.length === 0) {
        console.log('No posts found, skipping homepage update...');
        return;
    }

    const latestPost = posts[0];
    const indexPath = 'index.html';

    if (!fs.existsSync(indexPath)) {
        console.log('index.html not found, skipping...');
        return;
    }

    const doc = parseHTML(indexPath);

    // Update latest post section
    const latestPostEl = doc.querySelector('.latest-post');
    if (latestPostEl) {
        latestPostEl.innerHTML = `
            <h2><a href="${latestPost.url}">${latestPost.title}</a></h2>
            <time datetime="${latestPost.date}">${latestPost.dateDisplay}</time>
            <div class="post-preview-content">
                <p>${latestPost.excerpt}</p>
            </div>
            <a href="${latestPost.url}" class="read-more">Read more →</a>
        `.trim();

        // Write updated HTML
        const html = doc.documentElement.outerHTML;
        fs.writeFileSync(indexPath, '<!DOCTYPE html>\n' + html);

        console.log(`✅ Updated homepage with latest post: ${latestPost.title}\n`);
    } else {
        console.log('Could not find .latest-post element in index.html');
    }
}

// Run all generators
console.log('🔨 Building site...\n');
generateBenedictReviews();
const posts = generateBlogPosts();
updateHomepage(posts);
console.log('✅ Build complete!\n');
