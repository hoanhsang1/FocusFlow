from django.shortcuts import render
from all_app.users.check_login_role import *
from .to_do_list_models import *
from django.http import JsonResponse
# Create your views here.

@role_required('user')
def get_home(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    # Lấy ToDoList của user
    try:
        todo = ToDoList.objects.get(user_id=user_id)
    except ToDoList.DoesNotExist:
        return redirect('setup_todolist')

    # Lấy toàn bộ group + prefetch toàn bộ task trong group
    groups = (
        ToDoListGroup.objects
        .filter(todolist=todo, is_deleted=False)
        .prefetch_related('task_set')
    )

    context = {
        'groups': groups,
    }
    return render(request, 'to_do_list/home.html', context)

# tạo group id
def generate_group_id():
    last_group = ToDoListGroup.objects.order_by('-group_id').first()
    if not last_group:
        return "GRP001"
    number = int(last_group.group_id[3:]) + 1
    return f"GRP{number:03d}"

def add_group(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    user_id = request.session.get("user_id")
    todo = ToDoList.objects.get(user_id=user_id)

    group = ToDoListGroup.objects.create(
        group_id=generate_group_id(),
        todolist=todo,
        title=request.POST.get("title","").strip()
    )

    return JsonResponse({
        "id": group.group_id,
        "title": group.title
    }) 

# tạo task id
# TRONG views.py
def generate_task_id():
    last_task = Task.objects.order_by('-task_id').first()
    if not last_task:
        return "TSK001"
    try:
        number = int(last_task.task_id[3:]) + 1
        return f"TSK{number:03d}"
    except ValueError:
        return "TSK001"

def get_tasks(request, group_id):
    if request.method != "GET":
        return JsonResponse({"error": "Invalid method"}, status=400)

    try:
        group = ToDoListGroup.objects.get(group_id=group_id)
    except ToDoListGroup.DoesNotExist:
        return JsonResponse({"error": "Group not found"}, status=404)

    tasks = Task.objects.filter(group=group).values("task_id", "title", "status")

    return JsonResponse(list(tasks), safe=False)

def add_task(request,group_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)
    group = ToDoListGroup.objects.get(group_id=group_id)

    task = Task.objects.create(
        task_id = generate_task_id(),
        group = group,
        title = request.POST.get("title","").strip()
    )
    return JsonResponse({
        "id": task.task_id,
        "title": task.title
    })


def change_status(request, task_id):
    if request.method == 'POST':
        task = Task.objects.get(task_id=task_id)
        
        # 1. Thay đổi trạng thái
        if task.status == 'pending':
            task.status = 'completed'
        else:
            task.status = 'pending'
        task.save() 
        
        # 2. Chuẩn bị context để render phần icon hoặc task status
        context = {
            't': task, # Đặt task vào biến 't' để khớp với template logic của bạn
        }
        
        # 3. Render một phần template chứa icon đã cập nhật
        # Bạn cần tạo một template con (partial template) cho việc này
        return render(request, 'to_do_list/task_status_icon.html', context)