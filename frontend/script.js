document.addEventListener('DOMContentLoaded', () => {
    const videoUpload = document.getElementById('videoUpload');
    const analyzeButton = document.getElementById('analyzeButton');
    const resultDiv = document.getElementById('result');

    analyzeButton.addEventListener('click', async () => {
        const videoFile = videoUpload.files[0];
        if (!videoFile) {
            resultDiv.innerHTML = '<p style="color: red;">Please select a video file.</p>';
            return;
        }

        resultDiv.innerHTML = '<p>Uploading and analyzing video...</p>';
        analyzeButton.disabled = true;

        const formData = new FormData();
        formData.append('video', videoFile);

        try {
            const response = await fetch('http://localhost:5000/analyze-video', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                resultDiv.innerHTML = `
                    <p><strong>Analysis Status:</strong> ${data.status}</p>
                    <p><strong>Message:</strong> ${data.message}</p>
                    <p><strong>Potential Risk:</strong> ${data.potential_risk}</p>
                    <p><strong>Details:</strong> ${data.details}</p>
                `;
            } else {
                resultDiv.innerHTML = `<p style="color: red;">Error: ${data.error || 'Unknown error'}</p>`;
            }
        } catch (error) {
            resultDiv.innerHTML = `<p style="color: red;">Network error: ${error.message}</p>`;
        } finally {
            analyzeButton.disabled = false;
        }
    });
});
