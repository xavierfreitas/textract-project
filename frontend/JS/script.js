let UPLOAD_BUCKET = '';
let API_URL = '';

// Fetch configuration from config.json
fetch('https://textract-frontend-bucket.s3.amazonaws.com/config.json')
    .then(response => response.json())
    .then(config => {
        UPLOAD_BUCKET = config.UPLOAD_BUCKET;
        API_URL = config.API_URL;
    })
    .catch(err => console.error('Error loading config:', err));

document.getElementById('uploadForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a file!');
        return;
    }

    try {
        // Upload file to S3
        const uploadResponse = await fetch(UPLOAD_BUCKET + file.name, {
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
        const response = await fetch(`${API_URL}?fileKey=${file.name}`);
        const data = await response.json();

        // Display extracted text
        document.getElementById('output').textContent = data.extracted_text || 'No text found.';
    } catch (error) {
        console.error(error);
        alert('An error occurred. Please try again.');
    }
});