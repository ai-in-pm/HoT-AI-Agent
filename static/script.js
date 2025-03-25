document.addEventListener('DOMContentLoaded', () => {
    const questionForm = document.getElementById('questionForm');
    const questionInput = document.getElementById('questionInput');
    const submitBtn = document.getElementById('submitBtn');
    const answerSection = document.getElementById('answerSection');
    const questionDisplay = document.getElementById('questionDisplay');
    const taggedQuestion = document.getElementById('taggedQuestion');
    const answerDisplay = document.getElementById('answerDisplay');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const answerText = document.getElementById('answerText');
    
    // Submit question
    questionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        
        if (!question) {
            alert('Please enter a question');
            return;
        }
        
        // Disable submit button and show loading
        submitBtn.disabled = true;
        questionDisplay.classList.add('hidden');
        answerDisplay.classList.remove('hidden');
        loadingIndicator.style.display = 'flex';
        answerText.innerHTML = '';
        answerSection.scrollIntoView({ behavior: 'smooth' });
        
        try {
            // Send request to backend
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question })
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            // Set up EventSource for streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            // Hide loading indicator once we start receiving the answer
            loadingIndicator.style.display = 'none';
            
            // Process the stream
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) {
                    break;
                }
                
                // Decode the chunk and add to buffer
                buffer += decoder.decode(value, { stream: true });
                
                // Process complete SSE messages
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // Keep the last potentially incomplete line in buffer
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const content = line.substring(6); // Remove 'data: ' prefix
                        
                        if (content === '[DONE]') {
                            // End of stream
                            break;
                        } else if (!content.startsWith('Error:')) {
                            // Add content to answer
                            answerText.innerHTML += content;
                            typeSimulationScroll();
                        } else {
                            // Show error
                            answerText.innerHTML += `<span style="color: red;">${content}</span>`;
                        }
                    }
                }
            }
            
            // Now that we have the answer, show the tagged question
            // First, extract the tagged question from the original
            const factRegex = /<fact(\d+)>([^<]+)<\/fact\1>/g;
            let taggedQuestionText = question;
            const facts = [];
            
            // Extract facts from the answer
            let match;
            while ((match = factRegex.exec(answerText.innerHTML)) !== null) {
                const factNumber = match[1];
                const factContent = match[2];
                if (!facts.includes(factContent)) {
                    facts.push({ number: factNumber, content: factContent });
                }
            }
            
            // Add tags to the question based on facts found in the answer
            for (const fact of facts) {
                const factRegex = new RegExp(`\\b${escapeRegExp(fact.content)}\\b`, 'i');
                taggedQuestionText = taggedQuestionText.replace(
                    factRegex, 
                    `<fact${fact.number}>${fact.content}</fact${fact.number}>`
                );
            }
            
            // Display tagged question
            taggedQuestion.innerHTML = taggedQuestionText;
            questionDisplay.classList.remove('hidden');
            
            // Add hover effect for fact highlighting
            addFactHoverEffects();
            
        } catch (error) {
            console.error('Error:', error);
            answerText.innerHTML = `<span style="color: red;">Error: ${error.message}</span>`;
            loadingIndicator.style.display = 'none';
        } finally {
            submitBtn.disabled = false;
        }
    });
    
    // Function to handle typing simulation scrolling
    function typeSimulationScroll() {
        // Auto-scroll to bottom of answer as it's being typed
        answerText.scrollTop = answerText.scrollHeight;
    }
    
    // Function to add hover effects to fact tags
    function addFactHoverEffects() {
        // For each fact tag in the answer
        document.querySelectorAll('[id^="fact"]').forEach(factElement => {
            const factNumber = factElement.id.replace('fact', '');
            
            // Add hover event listeners
            factElement.addEventListener('mouseenter', () => {
                // Highlight all instances of this fact
                document.querySelectorAll(`fact${factNumber}`).forEach(el => {
                    el.style.boxShadow = '0 0 0 2px #f44336';
                });
            });
            
            factElement.addEventListener('mouseleave', () => {
                // Remove highlight
                document.querySelectorAll(`fact${factNumber}`).forEach(el => {
                    el.style.boxShadow = 'none';
                });
            });
        });
    }
    
    // Helper function to escape special characters in regex
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
});
