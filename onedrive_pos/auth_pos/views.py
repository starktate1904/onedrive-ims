from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .models import Notification, User
from django.contrib import messages
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Coalesce, TruncMonth
from datetime import datetime, date, timedelta
from datetime import datetime
import datetime as dt  # Renamed for clarity
import json
from products.models import Product
from staff.models import Employee
from pos.models import Sale
from branches.models import *
from user_profile.models import UserProfile
from django.core.paginator import Paginator
import requests


def send_low_stock_alert(products):
    product_list = "\n".join([f"{product.name}: {product.quantity}" for product in products])
    message_body = f"The following products are running low on stock:\n{product_list}"

    response = requests.post('https://textbelt.com/text', {
        'phone': '+263718910821',  # Replace with the admin's phone number
        'message': message_body,
        'key': 'textbelt',  # Use 'textbelt' for free messages
    })

# Helper function to handle messages and context

def get_context_with_messages(active_nav_item, request, additional_context=None):
    context = {
        'active_nav_item': active_nav_item,
        'messages': messages.get_messages(request)
    }
    if additional_context:
        context.update(additional_context)
    return context

def register(request):
    if request.method == 'POST':
        messages.warning(request, 'Important Notice: This signup is for OneDrive company members only.')
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        if not all([username, password, email]):
            messages.error(request, 'Please fill in all fields')
            return render(request, 'authentication/register.html')

        if User.objects.filter(username=username, email=email).exists():
            messages.error(request, 'Username or Email already taken')
            return render(request, 'authentication/register.html')

        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            Notification.objects.create(user=user, message=f'New user registered. Please go to staff management to allocate them a Branch: {user.username}')
            Employee.objects.create(user=user, branch=None)  # Link user to the employee
            user.role = 'cashier'  # Set the default role
            user.save()
            messages.success(request, 'Registration successful! Please contact the company admin for allocation.')
        except Exception:
            messages.error(request, 'An error occurred during registration')
            return render(request, 'authentication/register.html')

        return render(request, 'authentication/register_success.html')

    return render(request, 'authentication/register.html')

@cache_page(60 * 5)
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Please fill in all fields')
            return render(request, 'authentication/login.html')

        # Authenticate user with specified backend
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Login successful!')

            # Cache user role to avoid repeated database hits
            user_role = cache.get(f'user_role_{user.id}')
            if user_role is None:
                user_role = user.role  # Assuming user.role is a simple attribute
                cache.set(f'user_role_{user.id}', user_role, timeout=60 * 1)  # Cache for 15 minutes

            # Redirect immediately after login
            return redirect(f'auth_pos:{user_role}_dashboard')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'authentication/login.html')
  
@login_required
def logout_user(request):
    logout(request)
    return redirect('auth_pos:lock_screen')

@login_required
def lock_screen(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect(f'auth_pos:{user.role}_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'authentication/lockscreen.html')


@cache_page(60 * 5)
@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    messages.success(request, 'Notification marked as read.')
    return redirect('auth_pos:admin_dashboard')



@cache_page(60 * 5)
@login_required
def admin_dashboard(request):
    try:
        current_time = datetime.now()
        today = date.today()

        greeting = "Good Morning" if current_time.hour < 12 else "Good Afternoon" if current_time.hour < 18 else "Good Evening"

        user_profile = UserProfile.objects.get_or_create(user=request.user)[0]

        branches_count = Branch.objects.count()
        products_count = Product.objects.count()
        employee_count = Employee.objects.count()

        total_revenue = Sale.objects.aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0
        total_sales = Sale.objects.count()

        today_sales = Sale.objects.filter(date_created__date=today)[:5]
        today_sales_count = Sale.objects.filter(date_created__date=today).count()


        month_earnings = Sale.objects.annotate(month=TruncMonth('date_created')).values('month').annotate(earnings=Sum('total_amount')).order_by('month')

        low_stock_products = Product.objects.filter(quantity__lt=2)

        # Send SMS alert if there are low stock products
        if low_stock_products.exists():
            send_low_stock_alert(low_stock_products)

        month_earnings_labels = [month['month'].strftime('%b') for month in month_earnings]
        month_earnings_data = [float(month['earnings']) for month in month_earnings]

        monthly_earnings = []
        for month in range(1, 13):
            earning = Sale.objects.filter(date_created__year=today.year, date_created__month=month).aggregate(
                total_variable=Coalesce(Sum(F('total_amount')), 0.0, output_field=FloatField())).get('total_variable')
            monthly_earnings.append(earning)

        annual_earnings = Sale.objects.filter(date_created__year=today.year).aggregate(total_variable=Coalesce(
            Sum(F('total_amount')), 0.0, output_field=FloatField())).get('total_variable')
        annual_earnings = format(annual_earnings, '.2f')

        avg_month = format(sum(monthly_earnings)/12, '.2f')

        notifications = Notification.objects.filter(is_read=False)

        context = {
            'greeting': greeting,
            'today': today,
            'low_stock_products':low_stock_products,
            'user_profile': user_profile,
            'branches_count': branches_count,
            'products_count': products_count,
            'employee_count': employee_count,
            'total_revenue': total_revenue,
            'total_sales': total_sales,
            'today_sales': today_sales,
            'today_sales_count': today_sales_count,
            'month_earnings_labels': json.dumps(month_earnings_labels),
            'month_earnings_data': json.dumps(month_earnings_data),
            'monthly_earnings': monthly_earnings,
            'annual_earnings': annual_earnings,
            'avg_month': avg_month,
            'notifications': notifications,
        }

        return render(request, 'dashboard/admin_dashboard.html', context)
    except Exception as e:
        messages.error(request, 'An error occurred while loading the dashboard')
        return render(request, 'dashboard/admin_dashboard.html')


import logging

logger = logging.getLogger(__name__)

@cache_page(60 * 5)
@login_required
def manager_dashboard(request):
    try:
        # Get the employee and branch associated with the logged-in user
        employee = get_object_or_404(Employee, user=request.user)
        branch = employee.branch

        # Determine the greeting based on the current time
        current_hour = datetime.now().hour
        greeting = "Good Morning" if current_hour < 12 else "Good Afternoon" if current_hour < 18 else "Good Evening"

        # Get or create the user profile, ensuring the employee is set
        user_profile, created = UserProfile.objects.get_or_create(user=request.user, defaults={'employee': employee})

        # Fetch employees and products for the branch
        employees = Employee.objects.filter(branch=branch)
        products = Product.objects.filter(branch=branch)

        # Count employees and products in the branch
        branch_employees_count = employees.count()
        branch_products_count = products.count()

        # Calculate total sales and revenue for the branch
        total_sales = Sale.objects.filter(branch=branch).count()
        total_revenue = Sale.objects.filter(branch=branch).aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0

        # Calculate monthly earnings
        monthly_earnings = []
        for month in range(1, 13):
            earning = Sale.objects.filter(
                branch=branch,
                date_created__year=date.today().year,
                date_created__month=month
            ).aggregate(
                total_variable=Coalesce(Sum(F('total_amount')), 0.0, output_field=FloatField())
            ).get('total_variable')
            monthly_earnings.append(earning)

        # Calculate annual earnings
        annual_earnings = Sale.objects.filter(
            branch=branch,
            date_created__year=date.today().year
        ).aggregate(
            total_variable=Coalesce(Sum(F('total_amount')), 0.0, output_field=FloatField())
        ).get('total_variable')
        annual_earnings = format(annual_earnings, '.2f')

        # Calculate average monthly earnings
        avg_month = format(sum(monthly_earnings) / 12, '.2f') if monthly_earnings else '0.00'

        # Prepare context for rendering
        context = {
            'greeting': greeting,
            'today': date.today(),
            'branch': branch,
            'employees': employees,
            'products': products,
            'branch_employees_count': branch_employees_count,
            'branch_products_count': branch_products_count,
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'monthly_earnings': monthly_earnings,
            'annual_earnings': annual_earnings,
            'avg_month': avg_month,
            'user_profile': user_profile,
        }

        return render(request, 'dashboard/manager_dashboard.html', context)

    except Exception as e:
        messages.error(request, f'An error occurred while loading the dashboard: {str(e)}')
        return render(request, 'dashboard/manager_dashboard.html', )

@cache_page(60 * 5)
@login_required
def cashier_dashboard(request):
    try:
        # Get the employee and branch associated with the logged-in user
        employee = Employee.objects.get(user=request.user)
        branch = employee.branch

        # Determine the greeting based on the current time
        current_hour = datetime.now().hour
        if current_hour < 12:
            greeting = "Good Morning"
        elif current_hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"

        # Get or create the user profile
          # Get or create the user profile, ensuring the employee is set
        user_profile, created = UserProfile.objects.get_or_create(user=request.user, defaults={'employee': employee})

        # Fetch products and sales data
        products = Product.objects.filter(branch=branch)
        products_count = products.count()  # Count products in the specific branch
        total_sales = Sale.objects.filter(branch=branch).count()
        total_revenue = Sale.objects.filter(branch=branch).aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0

        # Get today's sales and count
        today = dt.date.today()
        today_sales = Sale.objects.filter(branch=branch, date_created__date=today)[:5]
        today_sales_count = Sale.objects.filter(branch=branch, date_created__date=today).count()

        # Prepare context for rendering
        context = {
            'greeting': greeting,
            'today': today,
            'branch': branch,
            'products': products,
            'products_count': products_count,
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'today_sales': today_sales,
            'today_sales_count': today_sales_count,
            'user_profile': user_profile,
        }

        return render(request, 'dashboard/cashier_dashboard.html', context)

    except Employee.DoesNotExist:
        messages.error(request, 'Employee record not found.')
        return render(request, 'dashboard/cashier_dashboard.html')

    except Exception as e:
        messages.error(request, 'An error occurred while loading the dashboard: {}'.format(str(e)))
        return render(request, 'dashboard/cashier_dashboard.html')


@cache_page(60 * 5)
@login_required
def admin_sale_list(request):
    active_nav_item = 'sales'

    sales = Sale.objects.all()

    date_filter = request.GET.get('date_filter')
    if date_filter == 'today':
        sales = sales.filter(date_created__date=datetime.today())
    elif date_filter == 'yesterday':
        sales = sales.filter(date_created__date=datetime.today() - timedelta(days=1))
    elif date_filter == 'last_week':
        sales = sales.filter(date_created__week=datetime.today().isocalendar()[1] - 1)
    elif date_filter == 'last_month':
        sales = sales.filter(date_created__month=datetime.today().month - 1)

    total_amount_filter = request.GET.get('total_amount_filter')
    if total_amount_filter:
        sales = sales.filter(total_amount__gte=int(total_amount_filter))

    sale_item_filter = request.GET.get('sale_item_filter')
    if sale_item_filter:
        sales = sales.filter(saleitem__product__name__icontains=sale_item_filter)

    product_filter = request.GET.get('product_filter')
    if product_filter:
        sales = sales.filter(saleitem__product__name__icontains=product_filter)

    cashier_filter = request.GET.get('cashier_filter')
    if cashier_filter:
        sales = sales.filter(cashier__name__icontains=cashier_filter)

    branch_filter = request.GET.get('branch_filter')
    if branch_filter:
        sales = sales.filter(branch__name__icontains=branch_filter)

    paginator = Paginator(sales, 10)
    page_number = request.GET.get('page')
    sales_page = paginator.get_page(page_number)

    return render(request, 'reports/sales.html', {
        'sales': sales_page,
        'active_nav_item': active_nav_item,
        'paginator': paginator,
    })

@cache_page(60 * 5)
@login_required
def manager_sales_list_view(request):
    # Implement the manager sales list view logic here
   
    branch = request.user.employee.branch
    sales = Sale.objects.filter(branch=branch)

    active_nav_item = 'branches'

    date_filter = request.GET.get('date_filter')
    if date_filter == 'today':
        sales = sales.filter(date_created__date=datetime.date.today())
    elif date_filter == 'yesterday':
        sales = sales.filter(date_created__date=datetime.date.today() - datetime.timedelta(days=1))
    elif date_filter == 'last_week':
        sales = sales.filter(date_created__week=datetime.date.today().isocalendar()[1] - 1)
    elif date_filter == 'last_month':
        sales = sales.filter(date_created__month=datetime.date.today().month - 1)

    total_amount_filter = request.GET.get('total_amount_filter')
    if total_amount_filter:
        sales = sales.filter(total_amount__gte=int(total_amount_filter))

    sale_item_filter = request.GET.get('sale_item_filter')
    if sale_item_filter:
        sales = sales.filter(saleitem__product__name__icontains=sale_item_filter)

    product_filter = request.GET.get('product_filter')
    if product_filter:
        sales = sales.filter(saleitem__product__name__icontains=product_filter)

    cashier_filter = request.GET.get('cashier_filter')
    if cashier_filter:
        sales = sales.filter(cashier__name__icontains=cashier_filter)

    branch_filter = request.GET.get('branch_filter')
    if branch_filter:
        sales = sales.filter(branch__name__icontains=branch_filter)

    paginator = Paginator(sales, 10)
    page_number = request.GET.get('page')
    sales_page = paginator.get_page(page_number)

    return render(request, 'reports/branch_sales.html', {
        'sales': sales_page,
        'active_nav_item': active_nav_item,
        'paginator': paginator,
    })