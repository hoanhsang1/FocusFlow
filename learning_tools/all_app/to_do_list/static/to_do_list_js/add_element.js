// add new group
function addGroup(event) {
    event.preventDefault(); // Ngăn form reload trang

    const title = document.getElementById("group-name").value.trim();
    if (!title) return;  // Không gửi rỗng

    fetch("/todolist/add_group/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: "title=" + encodeURIComponent(title)
    })
    .then(res => res.json())
    .then(data => {

        // Thêm group mới vào giao diện (dùng data trả về từ backend)
        const list = document.getElementById("group-list");
        list.innerHTML += `
            <div class="todolist_group" data-id="${data.id}">
                        <div class="todolist_group-name">
                            <form onsubmit="return false;">

                                <input type="text" 
                                    name="title"
                                    value="${data.title}" 
                                    onblur="edit_group(this, ${data.id}')"
                                    onkeypress="if(event.keyCode===13) this.blur()">
                            </form>
                        </div>
                    </div>
        `;

        // Xóa input
        document.getElementById("group-name").value = "";
    });
}

//adđ task
function addTask(event) {
    event.preventDefault();
    const activeGroupId = document.getElementById('taskList').dataset.groupId;
    const title = document.getElementById('task-name').value.trim();
    if (!title) return;
    fetch (`/todolist/add_task/${activeGroupId}/`,{
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: "title=" + encodeURIComponent(title)
    })
    .then(res => res.json())
    .then(data => {
        console.log("Chuẩn bị gửi FETCH: Group ID =", activeGroupId);
        const list = document.getElementById('taskList');
        list.innerHTML += `
            <div class="todolist_task">
                    <div class="task_status" data-id=${data.id}>
                        <i class="fa-regular fa-circle"></i>
                    </div>
                    <div class="task_title">${data.title}</div> 
            </div>
        `;

        document.getElementById("task-name").value = "";
    })
}   


// ĐẢM BẢO HÀM getCookie HOẠT ĐỘNG ĐÚNG
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
// change status
function changeStatus(classTask) {
    document.getElementById(classTask).addEventListener('click', function(event) {
        const clickedElement = event.target.closest('.task_status');

        if (clickedElement) {
            let taskId = clickedElement.dataset.id;
            
            if (taskId && taskId.trim() !== "") {

                fetch(`/todolist/change_status/${taskId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie("csrftoken")
                    }
                })
                .then(res => {
                    
                    if (!res.ok) { // Nếu có lỗi HTTP status code (ví dụ: 404, 500)
                        return res.text().then(text => { // Vẫn đọc response text để log lỗi chi tiết
                            throw new Error(`Server error: ${res.status} - ${text}`);
                        });
                    }
                    // Nếu res.ok là TRUE, server đã phản hồi thành công (với status 200)
                    // và nội dung là HTML của icon mới.
                    return res.text(); 
                })
                .then(htmlContent => { 
                    clickedElement.innerHTML = htmlContent; 
                })
                .catch(err => {
                    console.error('Lỗi khi thay đổi trạng thái task:', err);
                    //có thể giữ alert này để xử lý các lỗi thực sự
                    alert('Không thể cập nhật trạng thái: ' + err.message);
                });
            } else {
                console.warn("Không tìm thấy ID task hợp lệ cho phần tử được click.");
            }
        }
    });
}

function updateClickEvent() {
    document.querySelectorAll(".todolist_task").forEach(item => {
        item.addEventListener("click", function () {
            let taskID = this.dataset.id;
            console.log("hello")
            fetch(`/todolist/get_taskInfo/${taskID}/`) 
                .then(res => {
                    if (!res.ok) { // Xử lý lỗi HTTP status (ví dụ: 404, 500)
                            return res.text().then(text => { // Lấy thông báo lỗi từ server nếu có
                                throw new Error(`Server error: ${res.status} - ${text}`);
                            });
                        }
                        return res.json(); // Chỉ parse JSON nếu phản hồi OK
                })
                .then (task => {
                    let html = "";
                    const statusIcon = task.status === 'pending' ? 
                                '<i class="fa-regular fa-circle"></i>' : 
                                '<i class="fa-regular fa-circle-check"></i>';
                    html += `
                    <form id="taskForm" onsubmit="return false;" method="post">
                        <div class="todolist_task warp" id="taskInfo">
                            <div class="task_status" data-id="${task.id}">
                                ${statusIcon}
                            </div>
                            <input class="task_title taskInfo_title w-100" type="text" name="title" value="${task.title}">
                        </div>
                            <label for="date-picker">Deadline</label>
                            <input name="deadline" type="date" id="date-picker" data-id="task_deadline" value="${task.deadline}">
                            
                            <label for="task-note">Note</label>
                            <textarea name="task_note" id="task-note" placeholder="Thêm ghi chú...">${task.description}</textarea>
                            
                            <div class="form-buttons">
                                <button type="submit" class="btn btn-save" onclick="edit_taskInfo(this.closest('form'), '${task.id}')" data-id="${task.task_id}">
                                    <i class="fa-solid fa-floppy-disk"></i>
                                    Save
                                </button>
                                <button type="button" onclick="soft_delete_task('${task.id}')" class="btn btn-delete" data-id="${task.task_id}">
                                    <i class="fa-solid fa-trash"></i>
                                    Delete
                                </button>
                            </div>
                    </form>
                    `;
                    const taskInfoContainer = document.querySelector('.task_info');
                    taskInfoContainer.innerHTML = html;
                    changeStatus("taskInfo")
                })
        })
    })
}

// HÀM RELOAD CHỈ 1 TASK
function reloadSingleTask(taskID) {
    // Gọi API lấy thông tin task mới
    fetch(`/todolist/get_taskInfo/${taskID}/`)
        .then(response => response.json())
        .then(updatedTask => {
            // Tìm task element cần update
            const taskElement = document.querySelector(`.todolist_task[data-id="${taskID}"]`);
            
            if (taskElement) {
                // Cập nhật tiêu đề
                const titleElement = taskElement.querySelector('.task_title');
                if (titleElement) {
                    titleElement.textContent = updatedTask.title;
                }
                console.log('Đã cập nhật task:', taskID);
            }
        })
}

// HÀM RELOAD CHỈ 1 group
function reloadSingleTask(groupID) {
    // Gọi API lấy thông tin task mới
    fetch(`/todolist/edit_group/${groupID}/`)
        .then(response => response.json())
        .then(updatedTask => {
            // Tìm task element cần update
            const groupElement = document.querySelector(`.todolist_group[data-id="${groupID}"]`);
            
            if (groupElement) {
                // Cập nhật tiêu đề
                const titleElement = groupElement.querySelector('.task_title');
                if (titleElement) {
                    titleElement.textContent = updatedTask.title;
                }
                console.log('Đã cập nhật task:', groupID);
            }
        })
}

function removeTaskFromUI(taskID) {
    // Tìm và xóa task element
    const taskElement = document.querySelector(`.todolist_task[data-id="${taskID}"]`);
    if (taskElement) {
        taskElement.remove();
    }
}

// HÀM RELOAD CHỈ 1 GROUP
function reloadSingleGroup(groupID) {
    fetch(`/todolist/get_group_info/${groupID}/`)
        .then(response => response.json())
        .then(updatedGroup => {
            const groupElement = document.querySelector(`.todolist_group[data-id="${groupID}"]`);
            
            if (groupElement) {
                // Cập nhật tiêu đề
                const inputElement = groupElement.querySelector('input[type="text"]');
                if (inputElement) {
                    inputElement.value = updatedGroup.title;
                }
                console.log('Đã cập nhật group:', groupID);
            }
        })
        .catch(error => console.error('Error reloading group:', error));
}

function removeGroupFromUI(groupID) {
    const groupElement = document.querySelector(`.todolist_group[data-id="${groupID}"]`);
    if (groupElement) {
        groupElement.remove();
        console.log('Đã xóa group khỏi UI:', groupID);
    }
    
    // Nếu đang xem tasks của group bị xóa, clear task info
    document.querySelector('.task_info').innerHTML = '';
}

// show task list when click group
function clickGroup () {
    document.querySelectorAll(".todolist_group").forEach(item => {
        item.addEventListener("click", function () {
            let groupId = this.dataset.id;  

            // THÊM KIỂM TRA groupId:
            if (groupId && groupId.trim() !== "") { // Đảm bảo groupId không rỗng hoặc chỉ khoảng trắng
                document.getElementById('taskList').dataset.groupId = groupId;
                // URL đã khớp với urls.py (có '/' cuối)
                fetch(`/todolist/get_tasks/${groupId}/`) 
                    .then(res => {
                        if (!res.ok) { //Xử lý lỗi HTTP status (ví dụ: 404, 500)
                            return res.text().then(text => { // Lấy thông báo lỗi từ server nếu có
                                throw new Error(`Server error: ${res.status} - ${text}`);
                            });
                        }
                        return res.json(); // Chỉ parse JSON nếu phản hồi OK
                    })
                    .then(tasks => {
                        let html = "";
                        tasks.forEach(t => {
                            const statusIcon = t.status === 'pending' ? 
                                '<i class="fa-regular fa-circle"></i>' : 
                                '<i class="fa-regular fa-circle-check"></i>';
                            html += `
                            <div class="todolist_task" data-id="${t.task_id}">
                                    <div class="task_status" data-id="${t.task_id}">
                                        ${statusIcon} 
                                    </div>
                                    <div class="task_title">${t.title}</div> 
                            </div>
                            `; 
                        });
                        document.getElementById("taskList").innerHTML = html;
                        updateClickEvent()
                    })
                    .catch(err => {
                        console.error('Lỗi khi tải tasks:', err);
                        // Hiển thị thông báo lỗi
                        document.getElementById("taskList").innerHTML = `<li style="color: red;">Lỗi khi tải danh sách công việc: ${err.message || 'Không rõ lỗi'}</li>`;
                    });
            } else {
                console.warn("Không tìm thấy ID nhóm hợp lệ cho phần tử được click. Kiểm tra data-id trong HTML.");
                document.getElementById("taskList").innerHTML = `<li style="color: red;">Vui lòng chọn một nhóm hợp lệ.</li>`;
            }
        });
    });
}

clickGroup()
changeStatus("taskList");


function edit_taskInfo(formElement, taskID) {
    const csrfToken = getCookie("csrftoken");

    const formData = new FormData(formElement);
    formData.append('csrfmiddlewaretoken', csrfToken);

    // Hiển thị loading
    const saveButton = formElement.querySelector('.btn-save');
    const originalText = saveButton.innerHTML;
    saveButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang lưu...';
    saveButton.disabled = true;

    // Gửi POST request
    fetch(`/todolist/get_taskInfo/edit_taskInfo/${taskID}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            alert('Lưu thành công!');
            document.querySelector('.task_info').innerHTML = '';
            reloadSingleTask(taskID);
        } else {
            alert('Lỗi: ' + (data.error || 'Không thể lưu'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Lỗi khi lưu dữ liệu');
    })
    .finally(() => {
        saveButton.innerHTML = originalText;
        saveButton.disabled = false;
    });
}

function edit_group(inputElement, groupID) {
    const title = inputElement.value.trim();

    if (!title) {
        if (!confirm('Xóa group?')) return;
    }

    // Tạo URL và chuyển hướng (hoặc dùng fetch)
    const url = `/todolist/edit_group/${groupID}/?title=${encodeURIComponent(title)}`;
    
    // Cách 1: Dùng fetch
    fetch(url)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.deleted) removeGroupFromUI(groupID);
        } else alert('Lỗi: ' + data.error);
    })
    .catch(error => console.error('Error:', error));
}

function soft_delete_task(taskID) {
    // 1. Lấy CSRF token từ cookie để bảo mật
    const csrfToken = getCookie("csrftoken");

    // 2. Tạo đối tượng FormData để đóng gói dữ liệu gửi lên server
    const formData = new FormData();

    // 3. Thêm CSRF token vào form data để Django xác thực
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch(`/todolist/get_taskInfo/soft_delete_task/${taskID}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    // 5. XỬ LÝ KHI NHẬN ĐƯỢC RESPONSE TỪ SERVER
    .then(response => response.json()) 
    // ↑ DÒNG QUAN TRỌNG: 
    // - `response` là object chứa toàn bộ HTTP response
    // - `response.json()` ĐỌC và CHUYỂN ĐỔI nội dung response từ JSON string → JavaScript object
    // - RETURN kết quả để chuyển sang bước tiếp theo

    // 6. NHẬN DỮ LIỆU ĐÃ ĐƯỢC XỬ LÝ
    .then(data => {  // data chứa kết quả từ server
        // ↑ BÂY GIỜ `data` là JavaScript object đã được parse
        // Ví dụ: {success: true, message: "Xóa thành công"}
        if (data.success) {
            alert('Xoá thành công!');
            document.querySelector('.task_info').innerHTML = '';
            removeTaskFromUI(taskID);
        } else {
            alert('Lỗi: ' + (data.error || 'Không thể xoá'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Lỗi khi xoá dữ liệu');
    });
}

function searchGroups() {
    const searchInput = document.querySelector('input[name="q"]'); // ĐỊNH NGHĨA searchInput
    const searchQuery = searchInput.value;
    
    fetch(`/todolist/search_groups/?q=${encodeURIComponent(searchQuery)}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            renderGroups(data.groups);
        }
    })
    .catch(error => console.error('Search error:', error));
}

function renderGroups(groups) {
    const groupList = document.getElementById('group-list');
    let html = '';
    
    if (groups.length === 0) {
        html = `<div class="no-results">Không tìm thấy nhóm nào</div>`;
    } else {
        groups.forEach(group => {
            html += `
                <div class="todolist_group" data-id="${group.group_id}">
                    <div class="todolist_group-name">
                        <form onsubmit="return false;">
                            <input type="text" 
                                   name="title"
                                   value="${group.title}" 
                                   onblur="edit_group(this, '${group.group_id}')"
                                   onkeypress="if(event.keyCode===13) this.blur()">
                        </form>
                    </div>
                </div>`;
        });
    }
    
    groupList.innerHTML = html;
    clickGroup(); // Thêm event listeners lại
}