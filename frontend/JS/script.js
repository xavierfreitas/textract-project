let UPLOAD_BUCKET = '';
let API_URL = '';

// Fetch configuration from config.json
fetch('config.json')
    .then(response => response.json())
    .then(config => {
        UPLOAD_BUCKET = config.UPLOAD_BUCKET;
        API_URL = config.API_URL;

        // Add event listener after configuration is loaded
        document.getElementById('uploadForm').addEventListener('submit', uploadAndExtractText);
    })
    .catch(err => {
        console.error('Error loading config:', err);
        alert('Failed to load configuration. Please try again later.');
    });

async function uploadAndExtractText(event) {
    event.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a file!');
        return;
    }

    try {
        // Generate a unique filename to avoid conflicts
        const fileName = `${Date.now()}-${file.name}`;

        // Upload file to S3
        const uploadResponse = await fetch(UPLOAD_BUCKET + fileName, {
            method: 'PUT',
            body: file,
            headers: {
                'Content-Type': file.type
            }
        });

        if (!uploadResponse.ok) {
            throw new Error('File upload failed.');
        }

        // Fetch extracted text from API Gateway
        const response = await fetch(`${API_URL}?fileKey=${encodeURIComponent(fileName)}`);
        if (!response.ok) {
            throw new Error('Failed to retrieve extracted text.');
        }
        const data = await response.json();

        // Display extracted text
        document.getElementById('output').textContent = data.extracted_text || 'No text found.';
    } catch (error) {
        console.error(error);
        alert('An error occurred. Please try again.');
    }
}