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
            <div class="todolist_group">
                <p class="todolist_group-name">${data.title}</p>
            </div>
        `;

        // Xóa input
        document.getElementById("group-name").value = "";
    });
}

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
                    <div class="task_status" data-id=${data.task_id}>
                        <i class="fa-regular fa-circle"></i>
                    </div>
                    <div class="task_title">${data.title}</div> 
            </div>
        `;

        document.getElementById("task-name").value = "";
    })
}   


function getCookie(name) {
    return document.cookie.split("; ")
        .find(row => row.startsWith(name + "="))
        ?.split("=")[1];
}

// show task list when click group
document.querySelectorAll(".todolist_group").forEach(item => {
    item.addEventListener("click", function () {
        let groupId = this.dataset.id;  

        // THÊM KIỂM TRA groupId:
        if (groupId && groupId.trim() !== "") { // Đảm bảo groupId không rỗng hoặc chỉ khoảng trắng
            document.getElementById('taskList').dataset.groupId = groupId;
            // URL đã khớp với urls.py (có '/' cuối)
            fetch(`/todolist/get_tasks/${groupId}/`) 
                .then(res => {
                    if (!res.ok) { // Rất quan trọng: Xử lý lỗi HTTP status (ví dụ: 404, 500)
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
                        <div class="todolist_task">
                                <div class="task_status" data-id=${t.task_id}>
                                    ${statusIcon} 
                                </div>
                                <div class="task_title">${t.title}</div> 
                        </div>
                        `; 
                    });
                    document.getElementById("taskList").innerHTML = html;
                })
                .catch(err => {
                    console.error('Lỗi khi tải tasks:', err);
                    // Hiển thị thông báo lỗi thân thiện cho người dùng
                    document.getElementById("taskList").innerHTML = `<li style="color: red;">Lỗi khi tải danh sách công việc: ${err.message || 'Không rõ lỗi'}</li>`;
                });
        } else {
            console.warn("Không tìm thấy ID nhóm hợp lệ cho phần tử được click. Kiểm tra data-id trong HTML.");
            document.getElementById("taskList").innerHTML = `<li style="color: red;">Vui lòng chọn một nhóm hợp lệ.</li>`;
        }
    });
});

// change status
document.getElementById('taskList').addEventListener('click', function(event) {
    const clickedElement = event.target.closest('.task_status');

    if (clickedElement) {
        let taskId = clickedElement.dataset.id;
        
        if (taskId && taskId.trim() !== "") {
            // Tùy chọn: Thêm một hiệu ứng loading
            // clickedElement.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>'; 

            fetch(`/todolist/change_status/${taskId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie("csrftoken")
                }
            })
            .then(res => {
                // *** LOẠI BỎ hoặc sửa đổi khối kiểm tra lỗi này ***
                // Lý do: Khi Django trả về 200 OK với HTML icon, res.ok là TRUE.
                //        Khối này sẽ bị bỏ qua.
                //        Nếu có lỗi thực sự (ví dụ: 404, 500), nó sẽ được catch ở .catch() bên dưới
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
                // Bạn có thể giữ alert này để xử lý các lỗi thực sự
                alert('Không thể cập nhật trạng thái: ' + err.message);
            });
        } else {
            console.warn("Không tìm thấy ID task hợp lệ cho phần tử được click.");
        }
    }
});