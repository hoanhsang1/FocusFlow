// flashcards/static/flashcards/js/study_logic.js

// Khởi tạo khi DOM ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing flashcards...');
    initFlashcards();
});

function initFlashcards() {
    console.log('Initializing flashcards...');
    
    // Lấy container
    const container = document.getElementById('flashcards-container');
    if (!container) {
        console.error('Container not found');
        return;
    }
    
    // Lấy dữ liệu từ window object
    const flashcardsData = window.flashcardsData || [];
    const config = window.flashcardsConfig || {};
    
    // DOM elements
    const flashcardElement = document.getElementById('flashcard');
    const cardInner = document.getElementById('cardInner');
    const questionContent = document.getElementById('questionContent');
    const answerContent = document.getElementById('answerContent');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const flipBtn = document.getElementById('flipBtn');
    const markLearnedBtn = document.getElementById('markLearnedBtn');
    const progressFill = document.getElementById('progressFill');
    const cardCounter = document.getElementById('cardCounter');
    const statusBadge = document.getElementById('statusBadge');
    const statusBadgeBack = document.getElementById('statusBadgeBack');
    
    // State
    let currentCardIndex = 0;
    const totalCards = flashcardsData.length;
    
    console.log('Total cards:', totalCards);
    console.log('Flashcards data:', flashcardsData);
    
    if (totalCards === 0) {
        console.error('No flashcards data available');
        return;
    }
    
    // Helper: Get CSRF token
    function getCsrfToken() {
        return config.csrfToken || getCookie('csrftoken');
    }
    
    // Helper: Get cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Helper: Show toast notification
    function showToast(message, type = 'info') {
        console.log('Showing toast:', message, type);
        
        // Create toast container if not exists
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000;';
            document.body.appendChild(toastContainer);
        }
        
        // Remove existing toasts
        const existingToasts = toastContainer.querySelectorAll('.toast');
        existingToasts.forEach(toast => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="toast-message">${message}</span>
            <button class="toast-close">&times;</button>
        `;
        
        // Add to container
        toastContainer.appendChild(toast);
        
        // Add close button functionality
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            toast.style.animation = 'toastSlideOut 0.3s ease-out forwards';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        });
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'toastSlideOut 0.3s ease-out forwards';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }
        }, 3000);
    }

    //chuyển từ nút next thành finish
    function updateNavigationButtons() {
        if (!nextBtn) return;
        
        if (currentCardIndex === totalCards - 1) {
            // Đặt data attribute để biết đang ở chế độ Finish
            nextBtn.setAttribute('data-action', 'finish');
            nextBtn.innerHTML = '<i class="fas fa-flag-checkered"></i> Finish';
            showCompletionMessage()
        } else {
            nextBtn.setAttribute('data-action', 'next');
            nextBtn.innerHTML = 'Next <i class="fas fa-arrow-right"></i>';
        }
    }

    // Event listener cho nút Next
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            
            if (action === 'next') {
                // Chuyển đến thẻ tiếp theo
                if (currentCardIndex < totalCards - 1) {
                    currentCardIndex++;
                    showCard();
                }
            } else if (action === 'finish') {
                // Hiển thị xác nhận và quay về trang chủ
                const confirmed = confirm('Are you sure you want to finish?');
                if (confirmed) {
                    window.location.href = container.dataset.homeUrl || '/flashcards/home/';
                }
            }
        });
    }

    // Update progress bar
    function updateProgress() {
        if (!progressFill || !cardCounter) {
            console.warn('Progress elements not found');
            return;
        }
        
        const progressPercentage = ((currentCardIndex + 1) / totalCards) * 100;
        progressFill.style.width = `${progressPercentage}%`;
        cardCounter.textContent = `${currentCardIndex + 1} / ${totalCards}`;
        
        console.log('Progress updated:', progressPercentage + '%');
    }
        
    // Update status badge - GIẢI PHÁP ĐƠN GIẢN
    function updateStatusBadge() {
        console.log('Updating status badge...');
        
        const card = flashcardsData[currentCardIndex];
        if (!card) return;
        
        console.log('Card learned status:', card.learned);
        
        // Update badges
        // if (card.learned) {
        //     if (statusBadge) {
        //         statusBadge.textContent = 'Learned';
        //         statusBadge.className = 'status-badge status-learned';
        //     }
        //     if (statusBadgeBack) {
        //         statusBadgeBack.textContent = 'Learned';
        //         statusBadgeBack.className = 'status-badge status-learned';
        //     }
        // } else {
        //     if (statusBadge) {
        //         statusBadge.textContent = 'Not Learned';
        //         statusBadge.className = 'status-badge status-unknown';
        //     }
        //     if (statusBadgeBack) {
        //         statusBadgeBack.textContent = 'Not Learned';
        //         statusBadgeBack.className = 'status-badge status-unknown';
        //     }
        // }
        
        // Update button - đơn giản, chỉ thay đổi class và nội dung
        if (markLearnedBtn) {
            if (card.learned) {
                markLearnedBtn.classList.add('learned');
                markLearnedBtn.innerHTML = '<i class="fas fa-check"></i> Learned';
            } else {
                markLearnedBtn.classList.remove('learned');
                markLearnedBtn.innerHTML = '<i class="fas fa-check"></i> Mark as Learned';
            }
        }
    }
        
        // Show current card
    function showCard() {
        console.log('Showing card at index:', currentCardIndex);
        
        if (!cardInner || !questionContent || !answerContent) {
            console.error('Card elements not found');
            return;
        }
        
        const card = flashcardsData[currentCardIndex];
        if (!card) {
            console.error('Card not found at index:', currentCardIndex);
            return;
        }
        
        // Reset to front (unflip)
        cardInner.classList.remove('flipped');
        
        // Update content
        questionContent.textContent = card.question || 'No question';
        answerContent.textContent = card.answer || 'No answer';
        
        // Update progress and status
        updateProgress();
        updateStatusBadge();
        updateNavigationButtons();

        
        // Disable/enable buttons
        if (prevBtn) {
            prevBtn.disabled = currentCardIndex === 0;
            console.log('Prev button disabled:', prevBtn.disabled);
        }
        
        // if (nextBtn) {
        //     nextBtn.disabled = currentCardIndex === totalCards - 1;
        //     console.log('Next button disabled:', nextBtn.disabled);
        // }
        
        console.log('Card shown successfully');
    }

    // Toggle learned status - GIẢI PHÁP ĐƠN GIẢN
    async function toggleLearnedStatus() {
        console.log('Toggling learned status...');
        
        const card = flashcardsData[currentCardIndex];
        if (!card) return;
        
        const newLearnedStatus = !card.learned;
        
        // Disable button tạm thời
        if (markLearnedBtn) {
            markLearnedBtn.disabled = true;
        }
        
        try {
            const apiUrl = `/flashcards/flashcard_learn/${card.card_id}/toggle-learned/`;
            console.log('API URL:', apiUrl);
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    learned: newLearnedStatus 
                })
            });
            
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.success) {
                // Cập nhật dữ liệu
                card.learned = newLearnedStatus;
                
                // Cập nhật UI
                updateStatusBadge();
                
                showToast(`Card marked as ${newLearnedStatus ? 'learned' : 'unlearned'}!`, 'success');
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Error toggling learned status:', error);
            showToast('Failed to update status. Please try again.', 'error');
        } finally {
            if (markLearnedBtn) {
                markLearnedBtn.disabled = false;
            }
        }
    }
        
    // Show completion message (nếu cần)
    function showCompletionMessage() {
        const completionPercentage = Math.round((learnedCount / totalCards) * 100);
        showToast(`You've completed all ${totalCards} cards! (${completionPercentage}% learned)`, 'success');
    }
        
    // Event listeners
    if (cardInner) {
        cardInner.addEventListener('click', () => {
            console.log('Card clicked, toggling flip...');
            cardInner.classList.toggle('flipped');
        });
    } else {
        console.error('Card inner element not found');
    }

    if (flipBtn) {
        flipBtn.addEventListener('click', () => {
            console.log('Flip button clicked');
            cardInner.classList.toggle('flipped');
        });
    } else {
        console.warn('Flip button not found');
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            console.log('Previous button clicked');
            if (currentCardIndex > 0) {
                currentCardIndex--;
                showCard();
            }
        });
    } else {
        console.warn('Previous button not found');
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            console.log('Next button clicked');
            if (currentCardIndex < totalCards - 1) {
                currentCardIndex++;
                showCard();
            } else {
                console.log('All cards completed');
                showToast('You have completed all cards!', 'success');
            }
        });
    } else {
        console.warn('Next button not found');
    }

    if (markLearnedBtn) {
        markLearnedBtn.addEventListener('click', toggleLearnedStatus);
    } else {
        console.warn('Mark as Learned button not found');
    }

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        console.log('Key pressed:', e.key);
        
        switch(e.key) {
            case 'ArrowLeft':
            case 'a':
            case 'A':
                e.preventDefault();
                if (currentCardIndex > 0) {
                    currentCardIndex--;
                    showCard();
                }
                break;
                
            case 'ArrowRight':
            case 'd':
            case 'D':
                e.preventDefault();
                if (currentCardIndex < totalCards - 1) {
                    currentCardIndex++;
                    showCard();
                }
                break;
                
            case ' ':
            case 'Enter':
                e.preventDefault();
                if (cardInner) {
                    cardInner.classList.toggle('flipped');
                }
                break;
                
            case 'l':
            case 'L':
                e.preventDefault();
                toggleLearnedStatus();
                break;
        }
    });

    // Initialize
    showCard();

    console.log('Flashcards initialized successfully');
}

// End of file - đảm bảo không thiếu dấu đóng ngoặc