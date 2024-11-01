from django.shortcuts import render
from django.shortcuts  import render 
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .models import *
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from products.models import Product, Category
from staff.models import Employee
from  pos.models import Sale
from django.db.models import Count, Sum
from django.http import HttpResponse




# Branch management  CRUD views
@login_required
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
def branch_list(request):
    active_nav_item = 'branches'
    try:
        branches = Branch.objects.filter(is_deleted=False)
        return render(request, 'branches/branches.html', {'branches': branches,'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})
    except Exception as e:
        messages.error(request, 'Error fetching branches: {}'.format(e))
        return redirect('branches:branch_list',{'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})

@login_required
@user_passes_test(lambda user: user.has_perm('main.add_branch'))

def branch_create(request):
    active_nav_item = 'branches'
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')

        # Validate input
        if not location or not name:
            messages.error(request, 'Please fill in all fields')
            return render(request, 'branches/branches.html', {'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})

        try:

            Branch.objects.create(name=name, location=location)
            messages.success(request, 'Branch created successfully!')
            return redirect('branches:branch_list')  # Redirect to branch list after success
        except Exception as e:
            messages.error(request, 'Error creating branch: {}'.format(e))
            return render(request, 'branches/branches.html', {'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})
    return render(request, 'branches/branches.html',{'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})




@login_required
@user_passes_test(lambda user: user.has_perm('main.update_branch'))
def branch_update(request):
    active_nav_item = 'branches'
    try:
        branch = Branch.objects.get(id=request.GET.get('id'))
        context = {'branch': branch,
                   'active_nav_item':active_nav_item,
                   'messages': messages.get_messages(request)
                   }
        return render(request, 'branches/branches.html', context)
    except Branch.DoesNotExist:
        messages.error(request, 'Branch not found')
        return redirect('branches:branch_list',{'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})

@login_required
@user_passes_test(lambda user: user.has_perm('main.update_branch'))
def save_update_branch(request):
    active_nav_item = 'branches'
    if request.method == 'POST':
        try:
            branchid = request.POST.get('id')
            branch = Branch.objects.get(id=branchid)
            branch.name = request.POST.get('name')
            branch.location = request.POST.get('location')
            branch.save()
            messages.success(request, 'Branch updated successfully!')
            return redirect('branches:branch_list',{'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})
        except Exception as e:
            messages.error(request, 'Error updating branch: {}'.format(e))
            return render(request, 'branches/branches.html', {'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})

@login_required
@user_passes_test(lambda user: user.has_perm('main.delete_branch'))
def branch_delete(request, id):
    try:
        branch = Branch.objects.get(id=id)
        if branch.product_set.exists():
            messages.error(request, 'Cannot delete branch with products. Please delete or transfer products first.')
            return redirect('branches:branch_list',{'active_nav_item':'branches', 'messages': messages.get_messages(request)})
        else:
            branch.delete()  # Use the custom delete method
            messages.success(request, 'Branch deleted successfully!')
            return redirect('branches:branch_list',{'active_nav_item':'branches', 'messages': messages.get_messages(request)})
    except Branch.DoesNotExist:

        messages.error(request, 'Branch not found')
        return redirect('branches:branch_list',{'active_nav_item':'branches', 'messages': messages.get_messages(request)})

@login_required
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
def branch_detail(request, branch_id):
    active_nav_item = 'branches'
    try:
        branch = Branch.objects.get(id=branch_id)
        products_count = Product.objects.filter(branch=branch).count()
        employees_count = Employee.objects.filter(branch=branch).count()
        sales_count = Sale.objects.filter(branch=branch).count()
        revenue = Sale.objects.filter(branch=branch).aggregate(total_revenue=Sum('total'))['total_revenue']

        context = {
            'active_nav_item':active_nav_item,
            'branch': branch,
            'products_count': products_count,
            'employees_count': employees_count,
            'sales_count': sales_count,
            'revenue': revenue,
            'messages': messages.get_messages(request)
        }
        return render(request, 'branches/branches.html', context)
    except Branch.DoesNotExist:
        messages.error(request, 'Branch not found')
        return redirect('branches:branch_list',{'active_nav_item':'branches', 'messages': messages.get_messages(request)})

@login_required
def view_branch_products(request):
    active_nav_item = 'branches'
    if request.user.role == 'manager':
        branch = request.user.employee.branch
        products = Product.objects.filter(branch=branch)
        product_count = products.count()

        # Get the search query from the GET parameters
        search_query = request.GET.get('search', '')

        # Filter products based on the search query
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(make__icontains=search_query) |
                Q(model__icontains=search_query) |
                Q(price__icontains=search_query) |
                Q(category__name__icontains=search_query)  # Added category field
            )

        # Filter products by category
        category_id = request.GET.get('category')
        if category_id:
            products = products.filter(category_id=category_id)

        # Paginate the filtered and ordered products

        page_size = 10 
        paginator = Paginator(products.order_by('name'), page_size)

        page = request.GET.get('page')
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

        context = {
            'active_nav_item':active_nav_item,
            'paginator': paginator,
            'products': products,
            'search_query': search_query,
            'product_count': product_count,
            'categories': Category.objects.all(),  # Pass categories for filtering
            'messages': messages.get_messages(request)
        }
        return render(request, 'branches/branch_based_products.html', context)
    else:
        return redirect('auth_pos:login')

@login_required
def view_branch_employees(request):
    active_nav_item = 'staff'
    if request.user.role == 'manager':
        branch = request.user.employee.branch
        employees = Employee.objects.filter(branch=branch)
        branches = Branch.objects.all()

        employee_count = employees.count()
        context = {
            'active_nav_item':active_nav_item,
            'branch': branch,
            'employees': employees,
            'employee_count': employee_count,
            'branches': branches,
            'messages': messages.get_messages(request)
        }
        return render(request, 'branches/branch_employees.html', context)
    else:
        return redirect('auth_pos:login')

@login_required
def branch_employee_update(request, employee_id):
    active_nav_item = 'staff'
    employee = Employee.objects.get(pk=employee_id)
    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role')

        try:
            employee.user.username = request.POST.get('username')
            employee.user.role = role
            employee.user.email = email
            employee.user.save()
            employee.save()
            messages.success(request, 'Employee updated successfully!')
            return redirect('branches:view_branch_employees',{'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})
        except Exception as e:
            messages.error(request, 'Error updating employee: {}'.format(e))
    else:
        branches = Branch.objects.all()
        return render(request, 'branches/branch_employees.html', {'employee': employee, 'branches': branches,'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})

@login_required
def branch_employee_delete(request, employee_id):
    active_nav_item = 'staff'
    employee = Employee.objects.get(pk=employee_id)
    employee.delete()
    messages.success(request, 'Employee deleted successfully!')
    return redirect('branches:view_branch_employees',{'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})

@login_required
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
def branch_products(request, branch_id):
    active_nav_item = 'branches'
    
    try:
        branch = Branch.objects.get(id=branch_id)
        products = branch.product_set.select_related('branch')
        branch_products_count = products.count()

        # Get the search query from the GET parameters
        search_query = request.GET.get('search', '')

        # Filter products based on the search query
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(make__icontains=search_query) |
                Q(model__icontains=search_query) |
                Q(price__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )

        # Filter products by category
        category_id = request.GET.get('category')
        if category_id:
            products = products.filter(category_id=category_id)
        # Paginate the filtered and ordered products
        page_size = 10
        paginator = Paginator(products.order_by('name'), page_size)

        page = request.GET.get('page')
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

        context = {
            'active_nav_item':active_nav_item,
            'branch': branch,
            'products': products,
            'paginator': paginator,
            'search_query': search_query,
            'branch_options': Branch.objects.all(),
            'branch_products_count': branch_products_count,
            'categories': Category.objects.all(),
            'messages': messages.get_messages(request)
        }
        return render(request, 'branches/branch_products.html', context)
    except Branch.DoesNotExist:
        messages.error(request, 'Branch not found')
        return redirect('branches:branch_list',{'active_nav_item':active_nav_item, 'messages': messages.get_messages(request)})