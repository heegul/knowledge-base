let editingId = null;
let editingTable = null;
let editingField = null;

function enableEditing(element, id, table, field) {
    element.contentEditable = true;
    element.focus();
    editingId = id;
    editingTable = table;
    editingField = field;
    document.querySelector('.editing-buttons').style.display = 'flex';
    document.querySelectorAll('.editing').forEach(el => el.classList.remove('editing'));
    element.classList.add('editing');
}

async function saveTitle(element, id, table) {
    const newTitle = element.innerText;
    const response = await fetch('/update-title', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: id, title: newTitle, table_name: table })
    });

    const result = await response.json();
    if (result.success) {
        element.contentEditable = false;
        alert('Title updated successfully');
    } else {
        alert(`Failed to update title: ${result.error}`);
    }
}

async function saveContent() {
    const activeElement = document.querySelector('.editing');
    if (!activeElement) return;

    const id = activeElement.getAttribute('data-id');
    const table = activeElement.getAttribute('data-table');
    const field = activeElement.getAttribute('data-field');
    const newValue = activeElement.innerHTML;

    const response = await fetch('/update-content', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: id, value: newValue, table_name: table, field_name: field })
    });

    const result = await response.json();
    if (result.success) {
        alert('Content updated successfully');
        activeElement.contentEditable = false;
        activeElement.classList.remove('editing');
        document.querySelector('.editing-buttons').style.display = 'none';
    } else {
        alert(`Failed to update content: ${result.error}`);
    }
}

async function loadSidebar() {
    const sidebar = document.getElementById('sidebar');
    const response = await fetch('/get-topics');
    const topics = await response.json();

    const allLink = document.createElement('a');
    allLink.href = "#";
    allLink.innerText = "All";
    allLink.onclick = () => loadEntries();
    sidebar.appendChild(allLink);

    topics.forEach(topic => {
        const link = document.createElement('a');
        link.href = "#";
        link.innerText = topic;
        link.onclick = () => loadEntries(topic);
        sidebar.appendChild(link);
    });
}

async function addEntry() {
    const url = document.getElementById('url').value;
    const topic = document.getElementById('topic').value;
    const keywords = document.getElementById('keywords').value.split(',').map(kw => kw.trim());
    const content_type = document.getElementById('content_type').value;

    const tableName = url.includes('youtube.com') || url.includes('youtu.be') ? 'videos' : (url.endsWith('.pdf') || url.includes('arxiv.org')) ? 'pdfs' : 'articles';
    if (tableName === 'pdfs') {
        // Handle PDF URL upload
        const response = await fetch('/upload-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: url,
                topic: topic,
                keywords: keywords.join(',')
            })
        });

        const result = await response.json();
        document.getElementById('result').innerText = result.success ? 'PDF uploaded successfully!' : `Error: ${result.error}`;
        if (result.success) {
            loadEntries();
        }
    } else {
        // Handle other content types
        const response = await fetch('/add-entry', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                table_name: tableName,
                link: url,
                topic: topic,
                keywords: keywords,
                content_type: content_type
            })
        });

        const result = await response.json();
        document.getElementById('result').innerText = result.success ? 'Entry added successfully!' : `Error: ${result.error}`;
        if (result.success) {
            loadEntries();
        }
    }
}

async function uploadPDF() {
    const fileInput = document.getElementById('pdf-upload');
    const topicInput = document.getElementById('topic');
    const keywordsInput = document.getElementById('keywords');

    if (fileInput.files.length === 0) {
        alert('Please select a PDF file.');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('topic', topicInput.value.trim() || 'Unspecified');
    formData.append('keywords', keywordsInput.value.trim() || 'None');

    const response = await fetch('/upload-pdf', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    document.getElementById('result').innerText = result.success ? 'PDF uploaded successfully!' : `Error: ${result.error}`;
    if (result.success) {
        loadEntries();
    }
}

// Initialize the page when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Set up topic click handlers in the sidebar
    const topicLinks = document.querySelectorAll('.sidebar a');
    console.log('Found topic links:', topicLinks.length);
    
    topicLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            console.log('Topic clicked:', this.textContent.trim());
            
            // Update active topic
            topicLinks.forEach(l => l.style.textDecoration = 'none');
            this.style.textDecoration = 'underline';
            this.style.fontWeight = 'bold';
            
            // Store the active topic in localStorage for persistence
            localStorage.setItem('activeTopic', this.textContent.trim());
        });
    });
    
    // Check if there's a stored active topic and highlight it
    const storedTopic = localStorage.getItem('activeTopic');
    if (storedTopic) {
        topicLinks.forEach(link => {
            if (link.textContent.trim() === storedTopic) {
                link.style.textDecoration = 'underline';
                link.style.fontWeight = 'bold';
            }
        });
    }
    
    // Load all entries initially
    loadEntries();
});

// Function to search by keyword
function searchByKeyword() {
    const keyword = document.getElementById('search-keywords')?.value || '';
    const activeTopic = document.querySelector('.topic-list a.active')?.getAttribute('data-topic') || 
                        document.querySelector('.topic-list a.active')?.textContent.trim() || '';
    loadEntries(activeTopic, keyword);
}

// Function to delete an entry
async function deleteEntry(table, id) {
    try {
        // Store the current state before deletion
        const activeTopic = localStorage.getItem('activeTopic') || '';
        const currentKeyword = document.getElementById('search-keywords')?.value || '';
        
        const response = await fetch('/delete-entry', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ table_name: table, id: id })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Reload entries with the current topic and keyword
            loadEntries(activeTopic, currentKeyword);
            
            // Preserve scroll position
            const scrollPosition = window.scrollY;
            setTimeout(() => {
                window.scrollTo(0, scrollPosition);
            }, 100);
            
            // Show a temporary success message
            const messageDiv = document.createElement('div');
            messageDiv.className = 'success-message';
            messageDiv.textContent = 'Entry deleted successfully';
            document.body.appendChild(messageDiv);
            
            // Remove the message after 3 seconds
            setTimeout(() => {
                messageDiv.remove();
            }, 3000);
        } else {
            console.error(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error deleting entry:', error);
    }
}

function toggleContent(button) {
    const entryDiv = button.parentElement;
    const preview = entryDiv.querySelector('.content-preview');
    const full = entryDiv.querySelector('.content-full');
    
    if (preview.style.display !== 'none') {
        preview.style.display = 'none';
        full.style.display = 'block';
        button.textContent = 'Show Less';
    } else {
        preview.style.display = 'block';
        full.style.display = 'none';
        button.textContent = 'Show More';
    }
}

function handleBlur(event) {
    const element = event.target;
    saveContent(element);
}

async function loadEntries(topic = '', keyword = '') {
    try {
        // Fetch all types of entries
        const articlesResponse = await fetch(`/get-entries?table=articles&topic=${topic}&keyword=${keyword}`);
        const videosResponse = await fetch(`/get-entries?table=videos&topic=${topic}&keyword=${keyword}`);
        const pdfsResponse = await fetch(`/get-entries?table=pdfs&topic=${topic}&keyword=${keyword}`);
        
        const articles = await articlesResponse.json();
        const videos = await videosResponse.json();
        const pdfs = await pdfsResponse.json();

        // Get the container elements
        const articlesDiv = document.getElementById('articles');
        const videosDiv = document.getElementById('videos');
        const pdfsDiv = document.getElementById('pdfs');

        // Clear existing content
        articlesDiv.innerHTML = '<h2>Articles</h2>';
        videosDiv.innerHTML = '<h2>Videos</h2>';
        pdfsDiv.innerHTML = '<h2>PDFs</h2>';

        // Display articles
        if (articles.length === 0) {
            articlesDiv.innerHTML += '<p>No articles found for this topic.</p>';
        } else {
            articles.forEach(article => {
                const articleDiv = document.createElement('div');
                articleDiv.classList.add('entry');
                articleDiv.innerHTML = `
                    <div class="entry-header">
                        <h3 class="title">${article.title}</h3>
                        <button class="delete-btn" onclick="deleteEntry('articles', ${article.id})">×</button>
                    </div>
                    <div class="content-preview">${formatContent(article.content, 200)}</div>
                    <div class="content-full" style="display: none;">${article.content}</div>
                    <button class="show-more-btn" onclick="toggleContent(this)">Show More</button>
                    <div class="metadata">
                        <div class="date">Date: ${new Date(article.date).toLocaleString()}</div>
                        <div class="topic">Topic: ${article.topic}</div>
                        <div class="keywords">Keywords: ${article.keywords}</div>
                    </div>
                    <a href="${article.url}" target="_blank">Read more</a>
                `;
                articlesDiv.appendChild(articleDiv);
            });
        }

        // Display videos
        if (videos.length === 0) {
            videosDiv.innerHTML += '<p>No videos found for this topic.</p>';
        } else {
            videos.forEach(video => {
                const videoDiv = document.createElement('div');
                videoDiv.classList.add('entry');
                videoDiv.innerHTML = `
                    <div class="entry-header">
                        <h3 class="title">${video.title}</h3>
                        <button class="delete-btn" onclick="deleteEntry('videos', ${video.id})">×</button>
                    </div>
                    <div class="content-preview">${formatContent(video.content, 200)}</div>
                    <div class="content-full" style="display: none;">${video.content}</div>
                    <button class="show-more-btn" onclick="toggleContent(this)">Show More</button>
                    <div class="metadata">
                        <div class="date">Date: ${new Date(video.date).toLocaleString()}</div>
                        <div class="topic">Topic: ${video.topic}</div>
                        <div class="keywords">Keywords: ${video.keywords}</div>
                    </div>
                    <a href="${video.url}" target="_blank">Watch Video</a>
                `;
                videosDiv.appendChild(videoDiv);
            });
        }

        // Display PDFs
        if (pdfs.length === 0) {
            pdfsDiv.innerHTML += '<p>No PDFs found for this topic.</p>';
        } else {
            pdfs.forEach(pdf => {
                const pdfDiv = document.createElement('div');
                pdfDiv.classList.add('entry');
                pdfDiv.innerHTML = `
                    <div class="entry-header">
                        <h3 class="title">${pdf.title}</h3>
                        <button class="delete-btn" onclick="deleteEntry('pdfs', ${pdf.id})">×</button>
                    </div>
                    <div class="content-preview">${formatContent(pdf.content, 200)}</div>
                    <div class="content-full" style="display: none;">${pdf.content}</div>
                    <button class="show-more-btn" onclick="toggleContent(this)">Show More</button>
                    <div class="metadata">
                        <div class="date">Date: ${new Date(pdf.date).toLocaleString()}</div>
                        <div class="topic">Topic: ${pdf.topic}</div>
                        <div class="keywords">Keywords: ${pdf.keywords}</div>
                    </div>
                    <a href="${pdf.url}" target="_blank">View PDF</a>
                `;
                pdfsDiv.appendChild(pdfDiv);
            });
        }
    } catch (error) {
        console.error('Error loading entries:', error);
        document.getElementById('result').innerText = `Error: ${error.message}`;
    }
}

// Helper function to format content with a character limit and preserve markdown formatting
function formatContent(content, limit) {
    if (!content) return 'No content available.';
    
    // Replace HTML tags with appropriate markdown
    let formattedContent = content
        .replace(/<p>/g, '')
        .replace(/<\/p>/g, '\n\n')
        .replace(/<br\s*\/?>/g, '\n')
        .replace(/<h1>/g, '# ')
        .replace(/<\/h1>/g, '\n\n')
        .replace(/<h2>/g, '## ')
        .replace(/<\/h2>/g, '\n\n')
        .replace(/<h3>/g, '### ')
        .replace(/<\/h3>/g, '\n\n')
        .replace(/<ul>/g, '')
        .replace(/<\/ul>/g, '\n')
        .replace(/<li>/g, '• ')
        .replace(/<\/li>/g, '\n')
        .replace(/<strong>/g, '**')
        .replace(/<\/strong>/g, '**')
        .replace(/<em>/g, '*')
        .replace(/<\/em>/g, '*')
        .replace(/<code>/g, '`')
        .replace(/<\/code>/g, '`');
    
    // Remove any remaining HTML tags
    formattedContent = formattedContent.replace(/<[^>]*>/g, '');
    
    // Apply character limit if needed
    if (limit && formattedContent.length > limit) {
        return formattedContent.substring(0, limit) + '...';
    }
    
    return formattedContent;
}

function applyBold() {
    const selection = window.getSelection();
    if (!selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    const span = document.createElement('span');
    span.style.fontWeight = 'bold';
    range.surroundContents(span);
}

function increaseFontSize() {
    const element = document.querySelector('.editing');
    let fontSize = window.getComputedStyle(element).fontSize;
    fontSize = parseFloat(fontSize) + 2;
    element.style.fontSize = fontSize + 'px';
}

function decreaseFontSize() {
    const element = document.querySelector('.editing');
    let fontSize = window.getComputedStyle(element).fontSize;
    fontSize = parseFloat(fontSize) - 2;
    element.style.fontSize = fontSize + 'px';
}

function formatDescription(description) {
    const subtitles = [
        "Main Ideas", "Key Technical Insights", "Elaboration on Important Points",
        "Deep, Nuanced Analysis", "In conclusion", "Overall", "Firstly", "Secondly",
        "Thirdly", "Finally","Deep, Nuanced Analysis:","Important Points Elaborated:","Key Technical Insights:",
        "Main Ideas:"
    ];

    // Regex to match entire lines with subtitles and words ending with ":"
    const subtitleRegex = new RegExp(`^(${subtitles.join('|')}|\\w+:)`, 'gm');

    const lines = description.split('\n').map(line => {
        // Replace **text** with <strong>text</strong>
        line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Replace ### text with <h3>text</h3>
        line = line.replace(/### (.*)/g, '<h3>$1</h3>');
        // Apply subtitle formatting to the entire line
        line = line.replace(subtitleRegex, '<strong style="font-size: 1.2em;">$&</strong>');
        if (/^\d+\./.test(line.trim())) {
            return `<p>${line.trim()}</p>`;
        }
        return `<p>${line.trim()}</p>`;
    });
    return lines.join('');
}

// Event listeners for formatting buttons
document.getElementById('bold-button').addEventListener('click', applyBold);
document.getElementById('increase-font-button').addEventListener('click', increaseFontSize);
document.getElementById('decrease-font-button').addEventListener('click', decreaseFontSize);
document.getElementById('save-button').addEventListener('click', saveContent);

window.onload = () => {
    loadSidebar();
    loadEntries();
};

// Fallback initialization in case DOMContentLoaded has already fired
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    console.log('Document already loaded, initializing tabs now');
    setTimeout(initializeTabs, 100);
}

