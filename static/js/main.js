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

    let finalReportData = [];

    // --- ENTIRE FORM SUBMISSION LOGIC IS REBUILT ---
    emailForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const subject = document.getElementById('subject').value;
        const body = document.getElementById('body').value;
        const recipientsFile = document.getElementById('recipients_file').files[0];
        const sendersFile = document.getElementById('senders_file').files[0];

        if (!recipientsFile || !sendersFile) {
            alert('Please select both recipients and senders files.');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

        try {
            // Read and parse files directly in the browser
            const recipients = await parseCsv(recipientsFile);
            const senders = await parseCsv(sendersFile);

            if (recipients.length === 0) {
                 throw new Error("Could not read recipients. Check the CSV format for 'Name' and 'Email' columns.");
            }
            if (senders.length === 0) {
                throw new Error("Could not read sender accounts. Check the CSV format for 'email' and 'app_password' columns.");
            }

            // Switch to progress view
            formView.classList.add('hidden');
            progressView.classList.remove('hidden');

            await startClientSideSending(recipients, senders, subject, body);

        } catch (error) {
            alert(`An error occurred: ${error.message}`);
            resetToForm();
        }
    });

    // --- NEW FUNCTION TO MANAGE THE SENDING LOOP ---
    async function startClientSideSending(recipients, senders, subject, body) {
        let successCount = 0;
        finalReportData = []; // Clear previous report
        const totalRecipients = recipients.length;

        for (let i = 0; i < totalRecipients; i++) {
            const recipient = recipients[i];
            // Round-robin sender selection
            const sender = senders[i % senders.length];
            
            const progress = Math.round(((i + 1) / totalRecipients) * 100);
            
            // Update UI
            progressBar.style.width = progress + '%';
            progressPercent.textContent = progress + '%';
            statusMessage.textContent = `(${i + 1}/${totalRecipients}) Sending to: ${recipient.Email}`;

            try {
                const response = await fetch('/send-one-email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        recipient: { name: recipient.Name, email: recipient.Email },
                        sender: { email: sender.email, password: sender.app_password },
                        subject: subject,
                        body: body
                    })
                });

                const result = await response.json();
                finalReportData.push(result);

                if (response.ok) {
                    successCount++;
                    successCounter.textContent = successCount;
                }

            } catch (error) {
                finalReportData.push({
                    recipient_email: recipient.Email,
                    sender_email: sender.email,
                    status: 'Failed',
                    reason: 'Network error or server unreachable'
                });
            }

            // The delay is now handled by the browser
            if (i < totalRecipients - 1) {
                const delay = 20000 + Math.random() * 10000; // 20-30 seconds
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
        
        // --- CAMPAIGN COMPLETE ---
        statusMessage.textContent = 'Campaign Complete!';
        generateReport(finalReportData);
        progressView.classList.add('hidden');
        completeView.classList.remove('hidden');
    }

    // --- NEW HELPER TO PARSE CSV FILES IN JAVASCRIPT ---
    function parseCsv(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = function(event) {
                const text = event.target.result;
                const lines = text.split(/\r\n|\n/).filter(line => line); // Filter out empty lines
                if (lines.length < 2) {
                    return resolve([]); // Handle empty or header-only files
                }
                const headers = lines[0].split(',').map(h => h.trim());
                const result = [];
                for (let i = 1; i < lines.length; i++) {
                    const obj = {};
                    const currentline = lines[i].split(',');
                    for (let j = 0; j < headers.length; j++) {
                        obj[headers[j]] = currentline[j] ? currentline[j].trim() : '';
                    }
                    result.push(obj);
                }
                resolve(result);
            };
            reader.onerror = function() {
                reject(new Error('Failed to read file'));
            };
            reader.readAsText(file);
        });
    }

    // --- NEW FUNCTION TO GENERATE AND DOWNLOAD THE REPORT ---
    function generateReport(data) {
        if (data.length === 0) return;
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => `"${row[header]}"`).join(','))
        ].join('\r\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        downloadLink.href = URL.createObjectURL(blob);
        downloadLink.download = `report_${new Date().getTime()}.csv`;
    }

    resetBtn.addEventListener('click', function() {
        resetToForm();
    });

    function resetToForm() {
        progressBar.style.width = '0%';
        progressPercent.textContent = '0%';
        successCounter.textContent = '0';
        statusMessage.textContent = 'Initializing...';
        emailForm.reset();

        completeView.classList.add('hidden');
        progressView.classList.add('hidden');
        formView.classList.remove('hidden');
        
        submitBtn.disabled = false;
        submitBtn.textContent = 'Start Sending';
    }
});