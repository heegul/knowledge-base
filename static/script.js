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
    formData.append('topic', topicInput.value);
    formData.append('keywords', keywordsInput.value);

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

async function deleteEntry(table, id) {
    const response = await fetch('/delete-entry', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ table_name: table, id: id })
    });

    const result = await response.json();
    if (result.success) {
        loadEntries();
    } else {
        alert(`Failed to delete entry: ${result.error}`);
    }
}

function toggleContent(button) {
    const descriptionDiv = button.nextElementSibling;
    if (descriptionDiv.style.display === 'none' || descriptionDiv.style.display === '') {
        descriptionDiv.style.display = 'block';
        button.textContent = 'Show Less';
    } else {
        descriptionDiv.style.display = 'none';
        button.textContent = 'Show More';
    }
}

function handleBlur(event) {
    const element = event.target;
    saveContent(element);
}

async function loadEntries(topic = '', keyword = '') {
    const articlesResponse = await fetch(`/get-entries?table=articles&topic=${topic}&keyword=${keyword}`);
    const videosResponse = await fetch(`/get-entries?table=videos&topic=${topic}&keyword=${keyword}`);
    const pdfsResponse = await fetch(`/get-entries?table=pdfs&topic=${topic}&keyword=${keyword}`);
    const articles = await articlesResponse.json();
    const videos = await videosResponse.json();
    const pdfs = await pdfsResponse.json();

    const articlesDiv = document.getElementById('articles');
    const videosDiv = document.getElementById('videos');
    const pdfsDiv = document.getElementById('pdfs');

    articlesDiv.innerHTML = '<h2>Articles</h2>';
    videosDiv.innerHTML = '<h2>Videos</h2>';
    pdfsDiv.innerHTML = '<h2>PDFs</h2>';

    articles.forEach(article => {
        const articleDiv = document.createElement('div');
        articleDiv.classList.add('article');
        articleDiv.innerHTML = `
            <h3 class="title" id="title-articles-${article.id}" 
                data-id="${article.id}" data-table="articles" data-field="title"
                onclick="enableEditing(this, ${article.id}, 'articles', 'title')" 
                onblur="saveTitle(this, ${article.id}, 'articles')">${article.title}</h3>
            <button class="toggle-button" onclick="toggleContent(this)">Show More</button>
            <div class="description" style="display: none;" data-id="${article.id}" data-table="articles" data-field="content"
                onclick="enableEditing(this, ${article.id}, 'articles', 'content')" onblur="handleBlur(event)">${formatDescription(article.content)}</div>
            <div class="date">Date: ${new Date(article.date).toLocaleString()}</div>
            <div class="topic">Topic: ${article.topic}</div>
            <div class="keywords">Keywords: ${article.keywords}</div>
            <a href="${article.url}" target="_blank">Read more</a>
            <button onclick="deleteEntry('articles', ${article.id})">Delete</button>
        `;
        articlesDiv.appendChild(articleDiv);
    });

    videos.forEach(video => {
        const videoDiv = document.createElement('div');
        videoDiv.classList.add('video');
        videoDiv.innerHTML = `
            <h3 class="title" id="title-videos-${video.id}" 
                data-id="${video.id}" data-table="videos" data-field="title"
                onclick="enableEditing(this, ${video.id}, 'videos', 'title')" 
                onblur="saveTitle(this, ${video.id}, 'videos')">${video.title}</h3>
            <button class="toggle-button" onclick="toggleContent(this)">Show More</button>
            <div class="description" style="display: none;" data-id="${video.id}" data-table="videos" data-field="content"
                onclick="enableEditing(this, ${video.id}, 'videos', 'content')" onblur="handleBlur(event)">${formatDescription(video.content)}</div>
            <div class="date">Date: ${new Date(video.date).toLocaleString()}</div>
            <div class="topic">Topic: ${video.topic}</div>
            <div class="keywords">Keywords: ${video.keywords}</div>
            <a href="${video.url}" target="_blank">Watch video</a>
            <button onclick="deleteEntry('videos', ${video.id})">Delete</button>
        `;
        videosDiv.appendChild(videoDiv);
    });

    pdfs.forEach(pdf => {
        const pdfDiv = document.createElement('div');
        pdfDiv.classList.add('pdf');
        pdfDiv.innerHTML = `
            <h3 class="title" id="title-pdfs-${pdf.id}" 
                data-id="${pdf.id}" data-table="pdfs" data-field="title"
                onclick="enableEditing(this, ${pdf.id}, 'pdfs', 'title')" 
                onblur="saveTitle(this, ${pdf.id}, 'pdfs')">${pdf.title}</h3>
            <button class="toggle-button" onclick="toggleContent(this)">Show More</button>
            <div class="description" style="display: none;" data-id="${pdf.id}" data-table="pdfs" data-field="content"
                onclick="enableEditing(this, ${pdf.id}, 'pdfs', 'content')" onblur="handleBlur(event)">${formatDescription(pdf.content)}</div>
            <div class="topic">Topic: ${pdf.topic}</div>
            <div class="keywords">Keywords: ${pdf.keywords}</div>
            <a href="${pdf.url}" target="_blank">Download PDF</a>
            <button onclick="deleteEntry('pdfs', ${pdf.id})">Delete</button>
        `;
        pdfsDiv.appendChild(pdfDiv);
    });
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

// function formatDescription(description) {
//     const lines = description.split('\n').map(line => {
//         // Replace **text** with <strong>text</strong>
//         line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

//         // Replace ### text with <h3>text</h3>
//         line = line.replace(/### (.*)/g, '<h3>$1</h3>');

//         // Add special formatting for "In conclusion,"
//         if (/^In conclusion,/.test(line.trim())) {
//             return `<p><strong style="color:red;">${line.trim()}</strong></p>`;
//         }

//         // Replace lists with bullet points
//         if (/^- /.test(line.trim())) {
//             return `<li>${line.trim().substring(2)}</li>`;
//         } else if (/^\* /.test(line.trim())) {
//             return `<ul><li>${line.trim().substring(2)}</li></ul>`;
//         } else if (/^\d+\./.test(line.trim())) {
//             return `<li>${line.trim().replace(/^\d+\.\s*/, '')}</li>`;
//         }

//         // Add <p> tags around plain text
//         return `<p>${line.trim()}</p>`;
//     });

//     // Combine lines into a single string and close any open list tags
//     let formattedDescription = lines.join('');
//     formattedDescription = formattedDescription.replace(/<\/ul><ul>/g, '')
//                                                .replace(/<\/ol><ol>/g, '');

//     // Wrap lists in <ul> tags
//     formattedDescription = formattedDescription.replace(/(<li>.*?<\/li>)/g, '<ul>$1</ul>');

//     return formattedDescription;
// }

// function formatDescription(description) {
//     const subtitles = [
//         "Main Ideas", "Key Technical Insights", "Elaboration on Important Points",
//         "Deep, Nuanced Analysis", "In conclusion", "Overall", "Firstly", "Secondly",
//         "Thirdly", "Finally"
//     ];

//     // Regex to match entire lines with subtitles and words ending with ":"
//     const subtitleRegex = new RegExp(`^.*(${subtitles.join('|')}|\\b\\w+:).*$`, 'gm');

//     const lines = description.split('\n').map(line => {
//         // Replace **text** with <strong>text</strong>
//         line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

//         // Replace ### text with <h3>text</h3>
//         line = line.replace(/### (.*)/g, '<h3>$1</h3>');

//         // Apply subtitle formatting to the entire line
//         line = line.replace(subtitleRegex, '<strong style="font-size: 1.2em;">$&</strong>');

//         // Wrap lines in <p> tags
//         if (line.trim() !== "") {
//             return `<p>${line.trim()}</p>`;
//         }
//         return '';
//     });

//     return lines.join('');
// }


// Event listeners for formatting buttons
document.getElementById('bold-button').addEventListener('click', applyBold);
document.getElementById('increase-font-button').addEventListener('click', increaseFontSize);
document.getElementById('decrease-font-button').addEventListener('click', decreaseFontSize);
document.getElementById('save-button').addEventListener('click', saveContent);

window.onload = () => {
    loadSidebar();
    loadEntries();
};
