// ==========================================================
// 1. HÀM TIỆN ÍCH
// ==========================================================

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
    console.log(`Cookie '${name}':`, cookieValue);
    return cookieValue;
}

function sendFetch(url, bodyData) {
    return fetch(url, {
        method: 'POST',
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: bodyData.toString(),
    })
    .then(res => {
        if (!res.ok) {
            return res.text().then(text => { 
                try {
                    const errorJson = JSON.parse(text);
                    throw new Error(errorJson.error || res.statusText);
                } catch {
                    throw new Error(`Server returned HTTP ${res.status} (${res.statusText}).`);
                }
            });
        }
        return res.json();
    });
}

function reloadCurrentSet() {
    const setID_hien_tai = document.querySelector('.item_group').dataset.id;
    if (!setID_hien_tai) return;

    const currentSetElement = document.querySelector(`.flashcards_set[data-id="${setID_hien_tai}"]`);
    if (currentSetElement) {
        currentSetElement.dispatchEvent(new Event('click', { bubbles: true })); 
    }
}


// ==========================================================
// 2. CÁC HÀM XỬ LÝ SỰ KIỆN SUBMIT (Logic chính)
// ==========================================================

function addset(event) {
    event.preventDefault();
    const title = document.getElementById('set-name').value.trim();
    const flashcard_id = document.getElementById('set-list').dataset.id
    if (!title) return;

    const formData = new URLSearchParams();
    formData.append("title", title);

    sendFetch(`/flashcards/home/add_set/${flashcard_id}`, formData)
    .then (data => {
        const set_list = document.getElementById('set-list');
        set_list.innerHTML += `
            <div class="flashcards_set" data-id="${data.set_id}">
                <div class="flashcards_set-name">
                    <form onsubmit="return false;">
                        <i class="fa-regular fa-folder"></i>
                        <input type="text" 
                            name="title"
                            value="${data.title}" 
                            onblur="edit_set(this, '${data.set_id}')"
                            onkeypress="if(event.keyCode===13) this.blur()">
                    </form>
                </div>
            </div>
        `;
        document.getElementById("set-name").value = ""; 

        const newSetElement = document.querySelector(`.flashcards_set[data-id="${data.set_id}"]`);
        if (newSetElement) {
            newSetElement.dispatchEvent(new Event('click', { bubbles: true }));
        }
    })
    .catch(error => {
        console.error('Lỗi thêm Set:', error);
        alert('Lỗi Server: ' + error.message);
    });
}

function add_card(e) {
    if (e) {
        e.preventDefault(); 
        console.log("Block reload!"); 
    }
    const question_input = document.querySelector('.question_card').value.trim()
    const answer_input = document.querySelector('.answer_card').value.trim()
    const setID = document.querySelector('.item_group').dataset.id;
    
    if (!question_input || !answer_input || !setID) return;

    const formData = new URLSearchParams();
    formData.append("question", question_input); 
    formData.append("answer", answer_input);
    
    console.log(setID);
    
    sendFetch(`/flashcards/home/add_card/${setID}`, formData)
    .then (data => {
        if (data.success) {
            document.querySelector('.form_addCard').classList.add('hide'); 
            reloadCurrentSet(); 
            document.querySelector('.question_card').value = '';
            document.querySelector('.answer_card').value = '';
        } else {
            alert('Lỗi: ' + (data.error || 'Không thể lưu'));
        }
    })
    .catch(error => {
        console.error('Lỗi thêm Card:', error);
        alert('Lỗi Server: ' + error.message);
    });
}

function editCard(e) {
    if (e) {
        e.preventDefault(); 
        console.log("Block reload!"); 
    }
    
    const editModal = document.querySelector('.form_editCard');
    const cardID = editModal.dataset.id; 

    const question_input = document.querySelector('.edit_question-card').value.trim()
    const answer_input = document.querySelector('.edit_answer-card').value.trim()
    
    if (!question_input || !answer_input || !cardID) return;

    const formData = new URLSearchParams();
    formData.append("question", question_input); 
    formData.append("answer", answer_input);
    
    console.log(cardID);
    
    sendFetch(`/flashcards/home/edit_card/${cardID}`, formData)
    .then (data => {
        if (data.success) {
            document.querySelector('.form_editCard').classList.add('hide');
            reloadCurrentSet();
        } else {
            alert('Lỗi: ' + (data.error || 'Không thể lưu'));
        }
    })
    .catch(error => {
        console.error('Lỗi chỉnh sửa Card:', error);
        alert('Lỗi Server: ' + error.message);
    });
}

// ==========================================================
// 3. CÁC HÀM GẮN SỰ KIỆN VÀ LOGIC LOAD
// ==========================================================

function addClickAddBtn() {
    const addCardBtn = document.getElementById('add_card');
    const modal = document.querySelector('.form_addCard');
    if (addCardBtn) {
        addCardBtn.addEventListener('click', function() {
            modal.classList.toggle('hide');
        });
    }
}

function loadSetContent(setId, setTitle) {
    const mainContentContainer = document.querySelector('.item_container');
    
    let initialHtml = `
        <div class="item_header">
            <i class="fa-regular fa-folder"></i>
            <div class="set_title">${setTitle}</div>
        </div>
        <div class="item_group" data-id="${setId}">
            <p>Loading cards...</p> 
        </div>
        <div class="add_card-btn">
            <!-- SỬA: Thêm class 'study-btn' và id 'studyBtn' -->
            <div id="studyBtn" class="studyBtn card_btn bg-blue text-w center study-btn" style="cursor: pointer;">
                <i class="fa-solid fa-book-open"></i> Study
            </div>
            <div id="add_card" class="card_btn bg-w center add-card-btn">
                <i class="fa-solid fa-plus"></i>
                Add
            </div>
        </div>
    `;
    mainContentContainer.innerHTML = initialHtml;
    
    addClickAddBtn();
    
    // THÊM: Gắn sự kiện trực tiếp cho nút Study
    const studyBtn = document.getElementById('studyBtn');
    const studyModal = document.getElementById('studyModal');
    
    if (studyBtn && studyModal) {
        studyBtn.addEventListener('click', function(e) {
            console.log('Study button clicked directly');
            e.stopPropagation(); // Ngăn event bubbling
            
            // Hiển thị modal
            studyModal.style.display = 'flex';
            setTimeout(() => {
                studyModal.classList.remove('hide');
                studyModal.classList.add('show');
            }, 10);
        });
    }

    // Load cards...
    fetch(`/flashcards/home/get_card/${setId}`)
        .then(res => res.json())
        .then(items => {
            const taskContainer = document.querySelector('.item_group');
            let html = "";
            items.forEach(t => {
                html += `
                    <div class="item left" data-id="${t.card_id}">
                        <i class="fa-regular fa-copy"></i>
                        <div class="item_title">${t.question}</div>
                    </div>
                `;
            });
            taskContainer.innerHTML = html;
        });
}

function deleteCard(cardId) {
    if (!cardId) {
        console.error('Card ID is required for deletion');
        return;
    }
    
    console.log('Attempting to delete card:', cardId);
    console.log('CSRF Token:', getCookie("csrftoken"));
    
    const confirmed = confirm('Are you sure you want to delete this card? This action cannot be undone.');
    if (!confirmed) return;

    // Thử với fetch đơn giản để debug
    fetch(`/flashcards/home/delete_card/${cardId}`, {
        method: 'POST',
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: new URLSearchParams({}) // Body rỗng
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status} - ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        
        if (data.success) {
            document.querySelector('.form_editCard').classList.add('hide');
            reloadCurrentSet();
        } else {
            alert('Error: ' + (data.error || 'Could not delete card'));
        }
    })
    .catch(error => {
        console.error('Error deleting card:', error);
        console.error('Error details:', error.message);
        alert('Server Error: ' + error.message);
    });
}

function setupCardEditClick() {
    const itemGroup = document.querySelector('.item_container');
    const editModal = document.querySelector('.form_editCard');

    if (!itemGroup || !editModal) return;

    itemGroup.addEventListener('click', function(event) {
        const cardElement = event.target.closest('.item');
        
        if (cardElement) {
            const cardID = cardElement.dataset.id;
            const questionText = cardElement.querySelector('.item_title').textContent.trim();
            
            editModal.dataset.id = cardID; 
            document.querySelector('.edit_question-card').value = questionText;
            
            // TODO: Cần thêm logic lấy Answer và điền vào form

            editModal.classList.remove('hide');
            
            // THÊM PHẦN NÀY: Thiết lập sự kiện cho nút Delete
            const deleteBtn = document.getElementById('deleteCardBtn');
            if (deleteBtn) {
                // Xóa event listener cũ (nếu có)
                const newDeleteBtn = deleteBtn.cloneNode(true);
                deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);
                
                // Thêm event listener mới cho nút Delete mới
                newDeleteBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    // Xác nhận trước khi xóa
                    if (confirm('Are you sure you want to delete this card?')) {
                        deleteCard(cardID);
                    }
                });
            }
        }
    });
}
function setupSetClickDelegation() {
    const setListContainer = document.getElementById('set-list');
    if (!setListContainer) return;

    setListContainer.addEventListener('click', function(event) {
        const setElement = event.target.closest('.flashcards_set');

        if (setElement) {
            
            // ===============================================
            // 💡 PHẦN THÊM HIỆU ỨNG ACTIVE
            // ===============================================
            
            // 1. Lấy tất cả các set trong container
            const allSets = setListContainer.querySelectorAll('.flashcards_set');
            
            // 2. Loại bỏ class 'active' khỏi TẤT CẢ các set
            allSets.forEach(set => {
                set.classList.remove('active');
            });
            
            // 3. Thêm class 'active' cho set vừa được click
            setElement.classList.add('active');
            
            // ===============================================
            // ⚙️ LOGIC HIỆN TẠI (Load nội dung)
            // ===============================================
            
            let setId = setElement.dataset.id;
            const setTitleElement = setElement.querySelector('.flashcards_set-name input');
            const setTitle = setTitleElement ? setTitleElement.value : 'N/A';
            
            loadSetContent(setId, setTitle);
        }
    });
    
    // // TÙY CHỌN: Gọi loadSetContent cho set đầu tiên và đánh dấu active ban đầu
    // const firstSet = setListContainer.querySelector('.flashcards_set');
    // if (firstSet) {
    //     firstSet.classList.add('active');
    //     // Tùy chọn: loadSetContent(firstSet.dataset.id, firstSet.querySelector('.flashcards_set-name input').value);
    // }
}

function setupModalClose(modalSelector, closeBtnSelector) {
    const modal = document.querySelector(modalSelector);
    if (!modal) return;
    const closeButton = modal.querySelector(closeBtnSelector);

    function closeModal() {
        modal.classList.add('hide');
    }

    if (closeButton) {
        closeButton.addEventListener('click', closeModal);
    }

    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });
}

function setupStudyButtonDelegation() {
    const mainContentContainer = document.querySelector('.item_container');
    const studyModal = document.getElementById('studyModal'); // Đúng
    
    if (!mainContentContainer || !studyModal) {
        console.error('❌ Không tìm thấy:', {
            container: !!mainContentContainer,
            modal: !!studyModal
        });
        return;
    }
    
    console.log('✅ Study modal found:', studyModal);
    
    mainContentContainer.addEventListener('click', function(event) {
        console.log('Clicked element:', event.target);
        console.log('Clicked class:', event.target.className);
        
        const studyBtn = event.target.closest('.card_btn.bg-blue');
        
        if (studyBtn) {
            console.log('Study button found:', studyBtn);
            console.log('Button text:', studyBtn.textContent);
            console.log('Has study-btn class:', studyBtn.classList.contains('study-btn'));
            
            // Kiểm tra đây có phải nút Study không
            if (studyBtn.classList.contains('study-btn') || 
                studyBtn.textContent.trim().toLowerCase().includes('study')) {
                
                console.log('✅ Opening study modal...');
                studyModal.classList.remove('hide');
                
                // Thêm animation
                studyModal.style.display = 'flex';
                setTimeout(() => {
                    studyModal.classList.add('show');
                }, 10);
            }
        }
    });
}


// ==========================================================
// 4. HÀM KHỞI TẠO CHÍNH (Đã thêm setupStudyButtonDelegation)
// ==========================================================

function initializeApp() {
    const studyModal = document.getElementById('studyModal');
    
    // A. Thiết lập đóng modal
    setupModalClose('.form_addCard', '.modal_close');
    setupModalClose('.form_editCard', '.modal_close');
    setupModalClose('#studyModal', '.modal_close');
    
    // B. Thiết lập sự kiện
    setupSetClickDelegation();
    setupCardEditClick();
    
    // C. Gắn sự kiện cho các form
    const addCardForm = document.getElementById('add-card-form');
    if (addCardForm) addCardForm.addEventListener('submit', add_card); 
    
    const editCardForm = document.getElementById('edit-card-form');
    if (editCardForm) editCardForm.addEventListener('submit', editCard);
    
    // D. Xử lý chế độ học trong modal
    document.querySelectorAll('.option_card').forEach(card => {
        card.addEventListener('click', function() {
            const mode = this.dataset.mode;
            const currentSetElement = document.querySelector('.item_group');
            
            if (!currentSetElement) {
                alert('Vui lòng chọn một Set để học.');
                if (studyModal) {
                    studyModal.classList.add('hide');
                    studyModal.classList.remove('show');
                    studyModal.style.display = 'none';
                }
                return;
            }
            
            const currentSetId = currentSetElement.dataset.id;
            
            // Đóng Modal
            if (studyModal) {
                studyModal.classList.add('hide');
                studyModal.classList.remove('show');
                setTimeout(() => {
                    studyModal.style.display = 'none';
                }, 300);
            }
            
            // Chuyển hướng
            if (mode === 'flashcard') {
                window.location.href = `/flashcards/home/study/${currentSetId}/flashcard`;
            } else {
                alert(`Chế độ "${mode}" đang được phát triển.`);
            }
        });
    });
    
    // E. THÊM: Gắn sự kiện đóng modal khi click ra ngoài
    if (studyModal) {
        studyModal.addEventListener('click', function(e) {
            if (e.target === studyModal) {
                studyModal.classList.add('hide');
                studyModal.classList.remove('show');
                setTimeout(() => {
                    studyModal.style.display = 'none';
                }, 300);
            }
        });
    }
    
    // F. THÊM: Debug - log ra console
    console.log('App initialized');
    console.log('Study modal exists:', !!studyModal);
    console.log('Study button elements:', document.querySelectorAll('.study-btn'));
}

function edit_set(inputElement, setID) {
    const title = inputElement.value.trim();
    const originalTitle = inputElement.defaultValue || inputElement.getAttribute('data-original') || '';

    console.log('Editing set:', { setID, title, originalTitle });

    // Nếu title trống, hỏi xác nhận xóa
    if (!title) {
        const confirmed = confirm('Set name is empty. Do you want to delete this set?');
        if (!confirmed) {
            // Khôi phục giá trị cũ nếu không xóa
            inputElement.value = originalTitle;
            return;
        }
    }

    // Tạo data object
    const formData = {
        title: title
    };

    // Gửi request với POST method
    fetch(`/flashcards/home/edit_set/${setID}`, {
        method: 'POST',
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            // Nếu là lỗi 401 (Unauthorized)
            if (response.status === 401) {
                throw new Error('Please login to continue');
            }
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        
        if (data.success) {
            if (data.deleted) {
                // Xóa set khỏi DOM
                const setElement = document.querySelector(`.flashcards_set[data-id="${setID}"]`);
                if (setElement) {
                    setElement.remove();
                }
                
                // Nếu set đang được xem, clear content
                const currentSetId = document.querySelector('.item_group')?.dataset.id;
                if (currentSetId === setID) {
                    document.querySelector('.item_container').innerHTML = `
                        <div style="text-align: center; padding: 50px; color: #666;">
                            <i class="fa-regular fa-folder-open" style="font-size: 3rem; margin-bottom: 20px; opacity: 0.5;"></i>
                            <h3>Select a set to view flashcards</h3>
                        </div>
                    `;
                }
                
            } else {
                // Cập nhật thành công
                inputElement.defaultValue = title; // Lưu giá trị mới làm mặc định
                inputElement.setAttribute('data-original', title); // Lưu backup
                
                // Cập nhật title nếu set đang được xem
                const currentSetId = document.querySelector('.item_group')?.dataset.id;
                if (currentSetId === setID) {
                    const setTitleElement = document.querySelector('.set_title');
                    if (setTitleElement) {
                        setTitleElement.textContent = title;
                    }
                }
                
            }
        } else {
            // Hiển thị lỗi và khôi phục giá trị cũ
            alert('Error: ' + (data.error || 'Operation failed'));
            inputElement.value = originalTitle;
        }
    })
    .catch(error => {
        console.error('Error editing set:', error);
        alert('Error: ' + error.message);
        
        // Khôi phục giá trị cũ
        inputElement.value = originalTitle;
    });
}
// Chạy hàm khởi tạo khi DOM đã load
document.addEventListener('DOMContentLoaded', initializeApp);


