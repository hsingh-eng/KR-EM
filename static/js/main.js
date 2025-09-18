// static/js/main.js
document.addEventListener('DOMContentLoaded', function () {
    const formView = document.getElementById('form-view');
    const progressView = document.getElementById('progress-view');
    const completeView = document.getElementById('complete-view');
    
    const emailForm = document.getElementById('email-form');
    const submitBtn = document.getElementById('submit-btn');
    
    const progressBar = document.getElementById('progress-bar');
    const progressPercent = document.getElementById('progress-percent');
    const successCounter = document.getElementById('success-counter');
    const statusMessage = document.getElementById('status-message');
    
    const downloadLink = document.getElementById('download-link');
    const resetBtn = document.getElementById('reset-btn');

    let eventSource;

    emailForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        submitBtn.disabled = true;
        submitBtn.textContent = 'Uploading...';

        const formData = new FormData(emailForm);

        try {
            const response = await fetch('/start-sending', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Server error during setup.');
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            // Switch to progress view
            formView.classList.add('hidden');
            progressView.classList.remove('hidden');
            
            startListening(data.job_id);

        } catch (error) {
            alert(`An error occurred: ${error.message}`);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Start Sending';
        }
    });

    function startListening(jobId) {
        eventSource = new EventSource(`/progress/${jobId}`);

        eventSource.addEventListener('progress', function (event) {
            const data = JSON.parse(event.data);
            progressBar.style.width = data.progress + '%';
            progressPercent.textContent = data.progress + '%';
            successCounter.textContent = data.success_count;
            statusMessage.textContent = `Sending to: ${data.current_email}`;
        });

        eventSource.addEventListener('complete', function (event) {
            const reportFilename = event.data;
            statusMessage.textContent = 'All emails processed.';
            
            // Final update for progress bar
            progressBar.style.width = '100%';
            progressPercent.textContent = '100%';

            downloadLink.href = `/download/${reportFilename}`;

            progressView.classList.add('hidden');
            completeView.classList.remove('hidden');

            eventSource.close();
        });

        eventSource.addEventListener('error', function (event) {
            const data = JSON.parse(event.data);
            alert(`An error occurred during sending: ${data.error}`);
            eventSource.close();
            resetToForm();
        });
    }

    resetBtn.addEventListener('click', function() {
        resetToForm();
    });

    function resetToForm() {
        // Reset progress bar and stats
        progressBar.style.width = '0%';
        progressPercent.textContent = '0%';
        successCounter.textContent = '0';
        statusMessage.textContent = 'Initializing...';
        emailForm.reset();

        // Switch views
        completeView.classList.add('hidden');
        progressView.classList.add('hidden');
        formView.classList.remove('hidden');
        
        // Re-enable button
        submitBtn.disabled = false;
        submitBtn.textContent = 'Start Sending';
    }
});