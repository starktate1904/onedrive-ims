from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import cache_page
from .models import Branch
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from products.models import Product, Category
from staff.models import Employee
from pos.models import Sale
from django.db.models import Sum

# Helper function to handle messages and context
def get_context_with_messages(active_nav_item, request, additional_context=None):
    context = {
        'active_nav_item': active_nav_item,
        'messages': messages.get_messages(request)
    }
    if additional_context:
        context.update(additional_context)
    return context

# Branch management CRUD views
@cache_page( 60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
def branch_list(request):
    active_nav_item = 'branches'
    branches = Branch.objects.filter(is_deleted=False)
    return render(request, 'branches/branches.html', get_context_with_messages(active_nav_item, request, {'branches': branches}))

@cache_page( 60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.add_branch'))
def branch_create(request):
    active_nav_item = 'branches'
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')

        if not name or not location:
            messages.error(request, 'Please fill in all fields')
            return render(request, 'branches/branches.html', get_context_with_messages(active_nav_item, request))

        try:
            Branch.objects.create(name=name, location=location)
            messages.success(request, 'Branch created successfully!')
            return redirect('branches:branch_list')
        except Exception as e:
            messages.error(request, f'Error creating branch: {e}')
    
    return render(request, 'branches/branches.html', get_context_with_messages(active_nav_item, request))


@cache_page( 60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.update_branch'))
def branch_update(request):
    active_nav_item = 'branches'
    branch_id = request.GET.get('id')
    branch = get_object_or_404(Branch, id=branch_id)
    return render(request, 'branches/branches.html', get_context_with_messages(active_nav_item, request, {'branch': branch}))


@cache_page( 60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.update_branch'))
def save_update_branch(request):
    active_nav_item = 'branches'
    if request.method == 'POST':
        branch_id = request.POST.get('id')
        branch = get_object_or_404(Branch, id=branch_id)

        branch.name = request.POST.get('name')
        branch.location = request.POST.get('location')
        branch.save()
        messages.success(request, 'Branch updated successfully!')
        return redirect('branches:branch_list')

@cache_page( 60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.delete_branch'))
def branch_delete(request, id):
    branch = get_object_or_404(Branch, id=id)
    if branch.product_set.exists():
        messages.error(request, 'Cannot delete branch with products. Please delete or transfer products first.')
    else:
        branch.delete()
        messages.success(request, 'Branch deleted successfully!')
    return redirect('branches:branch_list')


@cache_page( 60 * 1)
@login_required
def view_branch_products(request):
    active_nav_item = 'branches'
    if request.user.role != 'manager':
        return redirect('auth_pos:login')

    branch = request.user.employee.branch
    products = Product.objects.filter(branch=branch)
    product_count = products.count()

    # Get the search query from the GET parameters
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query) |
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
        'paginator': paginator,
        'products': products,
        'search_query': search_query,
        'product_count': product_count,
        'categories': Category.objects.all()
    }
    return render(request, 'branches/branch_based_products.html', get_context_with_messages(active_nav_item, request, context))

@login_required
def view_branch_employees(request):
    active_nav_item = 'staff'
    if request.user.role != 'manager':
        return redirect('auth_pos:login')

    branch = request.user.employee.branch
    employees = Employee.objects.filter(branch=branch)
    employee_count = employees.count()
    branches = Branch.objects.all()

    context = {
        'branch': branch,
        'employees': employees,
        'employee_count': employee_count,
        'branches': branches
    }
    return render(request, 'branches/branch_employees.html', get_context_with_messages(active_nav_item, request, context))

@cache_page( 60 * 1)
@login_required
def branch_employee_update(request, employee_id):
    active_nav_item = 'staff'
    employee = get_object_or_404(Employee, pk=employee_id)
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
            return redirect('branches:view_branch_employees')
        except Exception as e:
            messages.error(request, f'Error updating employee: {e}')

    branches = Branch.objects.all()
    return render(request, 'branches/branch_employees.html', get_context_with_messages(active_nav_item, request, {'employee': employee, 'branches': branches}))


@cache_page( 60 * 1)
@login_required
def branch_employee_delete(request, employee_id):
    active_nav_item = 'staff'
    employee = get_object_or_404(Employee, pk=employee_id)
    employee.delete()
    messages.success(request, 'Employee deleted successfully!')
    return redirect('branches:view_branch_employees')

@cache_page( 60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
def branch_products(request, branch_id):
    active_nav_item = 'branches'
    branch = get_object_or_404(Branch, id=branch_id)
    products = branch.product_set.select_related('branch')
    branch_products_count = products.count()

    # Get the search query from the GET parameters
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query) |
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
        'branch': branch,
        'products': products,
        'paginator': paginator,
        'search_query': search_query,
        'branch_options': Branch.objects.all(),
        'branch_products_count': branch_products_count,
        'categories': Category.objects.all()
    }
    return render(request, 'branches/branch_products.html', get_context_with_messages(active_nav_item, request, context))