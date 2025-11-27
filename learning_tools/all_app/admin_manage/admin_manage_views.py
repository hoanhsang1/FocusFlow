from django.shortcuts import render
from all_app.users.check_login_role import *
# Create your views here.
@role_required('admin')
def get_admin_manage_page(request):
    return render(request, 'admin_manage/admin_home.html',{})