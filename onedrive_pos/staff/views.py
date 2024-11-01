from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Employee
from branches.models import Branch
from auth_pos.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User  = get_user_model()

# Helper function to handle messages and context
def get_context_with_messages(active_nav_item, request, additional_context=None):
    context = {
        'active_nav_item': active_nav_item,
        'messages': messages.get_messages(request)
    }
    if additional_context:
        context.update(additional_context)
    return context

# Employee management CRUD views
@login_required
@user_passes_test(lambda user: user.has_perm('main.view_employee_list'))
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
def employee_list(request):
    active_nav_item = 'staff'
    try:
        employees = Employee.objects.all()
        branches = Branch.objects.all()
        users = User.objects.all()

        context = get_context_with_messages(active_nav_item, request, {
            'employees': employees,
            'branches': branches,
            'users': users,
        })
        return render(request, 'staff/employees.html', context)
    except Exception as e:
        messages.error(request, f'Error loading employee list: {e}')
        return redirect('staffs:employee_list')

@login_required
@user_passes_test(lambda user: user.has_perm('main.add_employee'))
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
def employee_create(request):
    active_nav_item = 'staff'
    if request.method == 'POST':
        try:
            branch_id = request.POST.get('branch')
            username = request.POST.get('username')
            email = request.POST.get('email')
            role = request.POST.get('role')
            password = request.POST.get('password')

            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email address already in use')
                return redirect('staffs:employee_create')

            user = User.objects.create_user(username=username, email=email)
            user.role = role
            user.set_password(password)  # Set the password using set_password
            user.save()
            branch = get_object_or_404(Branch, pk=branch_id)
            Employee.objects.create(user=user, branch=branch)
            messages.success(request, 'Employee created successfully!')
            return redirect('staffs:employee_list')
        except Branch.DoesNotExist:
            messages.error(request, 'Invalid branch selected.')
        except Exception as e:
            messages.error(request, f'Error creating employee: {e}')

    branches = Branch.objects.all()
    return render(request, 'staff/employees.html', get_context_with_messages(active_nav_item, request, {
        'branches': branches
    }))

@login_required
@user_passes_test(lambda user: user.has_perm('main.update_employee'))
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
def employee_update(request, employee_id):
    active_nav_item = 'staff'
    employee = get_object_or_404(Employee, pk=employee_id)

    if request.method == 'POST':
        email = request.POST.get('email')
        branch_id = request.POST.get('branch')
        role = request.POST.get('role')
        password = request.POST.get('password')

        try:
            branch = get_object_or_404(Branch, pk=branch_id)
            employee.branch = branch
            employee.user.username = request.POST.get('username')
            employee.user.role = role  # Update the user's role
            employee.user.email = email  # Update the user's email  
            employee.user.set_password(password)  # Update the user's password
            employee.user.save()
            employee.save()
            messages.success(request, 'Employee updated successfully!')
            return redirect('staffs:employee_list')
        except Branch.DoesNotExist:
            messages.error(request, 'Invalid branch selected.')
        except Exception as e:
            messages.error(request, f'Error updating employee: {e}')
    else:
        branches = Branch.objects.all()
        return render(request, 'staff/employees.html', get_context_with_messages(active_nav_item, request, {
            'employee': employee,
            'branches': branches
        }))



@login_required
@user_passes_test(lambda user: user.has_perm('main.delete_employee'))
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
def employee_delete(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    employee.delete()  # Use the custom delete method
    messages.success(request, 'Employee deleted successfully!')
    return redirect(' staffs:employee_list')
    active_nav_item = 'staff'
    try:
        employee = Employee.objects.get(pk=employee_id)
        employee.delete()
        messages.success(request, 'Employee deleted successfully!')
    except Employee.DoesNotExist:
        messages.error(request, 'Employee not found.')
    except Exception as e:
        messages.error(request, 'Error deleting employee: {}'.format(e))
    return redirect('staffs:employee_list',{'active_nav_item':active_nav_item})