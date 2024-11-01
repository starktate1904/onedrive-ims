from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate,logout
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .models import *
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Coalesce
from django.db.models.functions import TruncMonth
from datetime import datetime, date,timedelta
import json
from django.core.serializers.json import DjangoJSONEncoder
import datetime
from products.models import *
from staff.models import *
from .models import User
from django.contrib.auth import get_user_model
from datetime import date
from django.contrib.auth.decorators import login_required
from pos.models import Sale
from django.db.models.functions import Trunc
from django.http import JsonResponse
from django.urls import reverse
from user_profile.models import *
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import time
from .auth_backend import RememberMeAuthBackend
User = get_user_model()




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
            hashed_password = make_password(password)
            user = User.objects.create_user(username, password=hashed_password, email=email)
            Notification.objects.create(user=user, message=f'New user registered Please got to staff management to allocate them a Branch: {user.username}')
            Employee.objects.create(user=user, branch=None)  # Link user to the employee
            user.role = 'cashier'  # Set the default role
            user.save()
            messages.success(request, 'Registration successful! Please contact the company admin for allocation.')
        except Exception as e:
            messages.error(request, 'An error occurred during registration')
            return render(request, 'authentication/register.html')

        # Instead of redirecting to a dashboard, display a success message
        return render(request, 'authentication/register_success.html')

    else:
        return render(request, 'authentication/register.html')

# login view
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        if not all([username, password]):
            messages.error(request, 'Please fill in all fields')
            return render(request, 'authentication/login.html')

        try:
            user = authenticate(request, username=username, password=password,backend='auth_pos.auth_backend.RememberMeAuthBackend')
            if user is not None:
                auth_login(request, user)
                messages.success(request, 'Login successful!')

                # Check if the user wants to be remembered
                if remember_me:
                    try:
                        # Set the session to expire in 30 days
                        request.session.set_expiry(30 * 24 * 60 * 60)
                    except Exception as e:
                        messages.error(request, 'Error setting session expiration: ' + str(e))
                else:
                    try:
                        # Set the session to expire when the browser is closed
                        request.session.set_expiry(0)
                    except Exception as e:
                        messages.error(request, 'Error setting session expiration: ' + str(e))
            else:
                messages.error(request, 'Invalid credentials')
                return render(request, 'authentication/login.html')
        except Exception as e:
            messages.error(request, 'An error occurred during login: ' + str(e))
            return render(request, 'authentication/login.html')

        # Redirect based on user role
        if user.role == 'admin':
            return redirect('auth_pos:admin_dashboard')
        elif user.role == 'manager':
            return redirect('auth_pos:manager_dashboard')
        else:
            return redirect('auth_pos:cashier_dashboard')

    else:
        return render(request, 'authentication/login.html')



@login_required
def logout_user(request):
    logout(request)
    return redirect('auth_pos:lock_screen')



def lock_screen(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password, backend='django.contrib.auth.backends.ModelBackend')
        if user is not None:
            auth_login(request, user)  # Call the login function to authenticate the user
            role_map = {
                'admin': 'auth_pos:admin_dashboard',
                'manager': 'auth_pos:manager_dashboard',
                'cashier': 'auth_pos:cashier_dashboard'
            }
            messages.success(request, f'Welcome back, {user.username}!')  # Add a welcome message
            return redirect(role_map.get(user.role, 'auth_pos:login'))
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'authentication/lockscreen.html')



@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True  # Assuming there is an 'is_read' field in your Notification model
    notification.save()
    messages.success(request, 'Notification marked as read.')
    return redirect('auth_pos:admin_dashboard')  # Redirect back to the admin dashboard or wherever appropriate




# admin_dashboard view
@login_required
@user_passes_test(lambda user: user.has_perm('main.view_admin_dashboard'))
def admin_dashboard(request):
    try:
        # Get the current time
        current_time = datetime.datetime.now()
        today = date.today()

        # Determine the greeting based on the time of day
        if current_time.hour < 12:
            greeting = "Good Morning"
        elif current_time.hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"

        branches_count = Branch.objects.count()
        products_count = Product.objects.count()
        employee_count = Employee.objects.count()

        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            user_profile = None

        # Calculate the total revenue
        total_revenue = Sale.objects.aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0

        # Count the number of sales
        total_sales = Sale.objects.count()
        

        # Get today's sales list
        today_sales = Sale.objects.filter(date_created__date=today)[:5]
        today_sales_count = Sale.objects.filter(date_created__date=today).count()

        # Get the top products
        top_products = Product.objects.annotate(total_sales=Sum('sale_items__quantity') * F('sale_items__price')).order_by('-total_sales')[:3]

        # Get the month earnings
        month_earnings = Sale.objects.annotate(month=TruncMonth('date_created')).values('month').annotate(earnings=Sum('total_amount')).order_by('month')

        # Create lists for the top products names and quantities
        top_products_names = [product.name for product in top_products]
        top_products_quantity = [product.total_sales for product in top_products]
        low_stock_products = Product.objects.filter(quantity__lt=2)

        # Create lists for the month earnings
        month_earnings_labels = [month['month'].strftime('%b') for month in month_earnings]
        month_earnings_data = [float(month['earnings']) for month in month_earnings]

        # Calculate earnings per month
        today = date.today()
        year = today.year
        monthly_earnings = []
        for month in range(1, 13):
            earning = Sale.objects.filter(date_created__year=year, date_created__month=month).aggregate(
                total_variable=Coalesce(Sum(F('total_amount')), 0.0, output_field=FloatField())).get('total_variable')
            monthly_earnings.append(earning)

        # Calculate annual earnings
        annual_earnings = Sale.objects.filter(date_created__year=year).aggregate(total_variable=Coalesce(
            Sum(F('total_amount')), 0.0, output_field=FloatField())).get('total_variable')
        annual_earnings = format(annual_earnings, '.2f')

        # AVG per month
        avg_month = format(sum(monthly_earnings)/12, '.2f')

        # Get notifications
        notifications = Notification.objects.filter(is_read=False)

        context = {
            'low_stock_products':low_stock_products,
            'today_sales_count':today_sales_count,
            'today_sales':today_sales,
            'today':today,
            'user_profile':user_profile,
            'products_count': products_count,
            'branches_count': branches_count,
            'employee_count': employee_count,
            'greeting': greeting,
            'total_revenue': total_revenue,
            'total_sales': total_sales,
            'top_products': top_products,
            'top_products_names': top_products_names,
            'month_earnings_labels': json.dumps(month_earnings_labels),
            'month_earnings_data': json.dumps(month_earnings_data),
            'top_products_quantity': top_products_quantity,
            'monthly_earnings': monthly_earnings,
            'annual_earnings': annual_earnings,
            'avg_month': avg_month,
            'notifications': notifications,
        }

        return render(request, 'dashboard/admin_dashboard.html', context)
    except Exception as e:
        messages.error(request, 'An error occurred while loading the dashboard')
        return render(request, 'dashboard/admin_dashboard.html')

# branch manager_dashboard view
@login_required
def manager_dashboard(request):
    try:
        employee = Employee.objects.get(user=request.user)
        branch = employee.branch
        today = date.today()
        current_time = datetime.datetime.now()

        # Determine the greeting based on the time of day
        if current_time.hour < 12:
            greeting = "Good Morning"
        elif current_time.hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
        
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            user_profile = None

        if branch:
            employees = Employee.objects.filter(branch=branch)
            products = Product.objects.filter(branch=branch)
            branch_employees_count = employees.count()
            branch_products_count = products.count()

            # Calculate total sales for the branch
            total_sales = Sale.objects.filter(branch=branch).count()

            # Calculate total revenue for the branch
            total_revenue = Sale.objects.filter(branch=branch).aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0

            # Get top products for the branch
            top_products = Product.objects.filter(branch=branch).annotate(total_sales=Sum('sale_items__quantity') * F('sale_items__price')).order_by('-total_sales')[:3]

            # Get top products names and quantities
            top_products_names = [product.name for product in top_products]
            top_products_quantity = [product.total_sales for product in top_products]

            # Calculate earnings per month for the branch
            monthly_earnings = []
            for month in range(1, 13):
                earning = Sale.objects.filter(branch=branch, date_created__year=today.year, date_created__month=month).aggregate(
                    total_variable=Coalesce(Sum(F('total_amount')), 0.0, output_field=FloatField())).get('total_variable')
                monthly_earnings.append(earning)

            # Calculate annual earnings for the branch
            annual_earnings = Sale.objects.filter(branch=branch, date_created__year=today.year).aggregate(total_variable= Coalesce(
                Sum(F('total_amount')), 0.0, output_field=FloatField())).get('total_variable')
            annual_earnings = format(annual_earnings, '.2f')

            # AVG per month
            avg_month = format(sum(monthly_earnings)/12, '.2f')

            context = {
                'greeting':greeting,
                'today':today,
                'branch': branch,
                'employees': employees,
                'products': products,
                'branch_employees_count':branch_employees_count,
                'branch_products_count':branch_products_count,
                'total_sales': total_sales,
                'total_revenue': total_revenue,
                'top_products': top_products,
                'top_products_names': top_products_names,
                'top_products_quantity': top_products_quantity,
                'monthly_earnings': monthly_earnings,
                'annual_earnings': annual_earnings,
                'avg_month': avg_month,
                'user_profile': user_profile,
            }

            return render(request, 'dashboard/manager_dashboard.html', context)
        else:
            # Handle the case where the user doesn't have a branch assigned
            # You might redirect to a different page or display an error message
            messages.error(request, 'You are not assigned to a branch')
            return render(request, 'dashboard/manager_dashboard.html')
    except Exception as e:
        messages.error(request, 'An error occurred while loading the dashboard')
        return render(request, 'dashboard/manager_dashboard.html')


# cashier_dashboard view
@login_required
def cashier_dashboard(request):
    try:
        today = date.today()
        current_time = datetime.datetime.now()
        employee = Employee.objects.get(user=request.user)
        branch = employee.branch

        branch = Branch.objects.get(id=request.user.employee.branch_id)
        products = Product.objects.filter(branch=branch)
        total_sales = Sale.objects.filter(branch=branch).count()
        products_count = products.count()
         # Calculate total sales for the branch
        total_sales = Sale.objects.filter(branch=branch).count()
        # Get today's sales list
        today_sales = Sale.objects.filter(branch=branch, date_created__date=today,)[:5]
        today_sales_count = today_sales.count()
        


            # Calculate total revenue for the branch
        total_revenue = Sale.objects.filter(branch=branch).aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0
       
        
       

        # Determine the greeting based on the time of day
        if current_time.hour < 12:
            greeting = "Good Morning"
        elif current_time.hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
        
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            user_profile = None


        context = {

            'today':today,
            'greeting':greeting,
            'total_sales':total_sales,
            'today_sales_count':today_sales_count,
            'total_revenue':total_revenue,
            "active_icon": "dashboard",
            'products_count':products_count,
            "products": Product.objects.filter(branch=branch).count(),
            'branch': branch,
            'products':products,
            'user_profile':user_profile
        }

        return render(request, 'dashboard/cashier_dashboard.html', context)
    except Exception as e:
        messages.error(request, 'An error occurred while loading the dashboard')
        return render(request, 'dashboard/cashier_dashboard.html')

@login_required
def admin_sale_list(request):
    active_nav_item = 'sales'
    sales = Sale.objects.all()

    # Filtering by date
    date_filter = request.GET.get('date_filter')
    if date_filter == 'today':
        sales = sales.filter(date_created__date=datetime.date.today())
    elif date_filter == 'yesterday':
        sales = sales.filter(date_created__date=datetime.date.today() - datetime.timedelta(days=1))
    elif date_filter == 'last_week':
        sales = sales.filter(date_created__week=datetime.date.today().isocalendar()[1] - 1)
    elif date_filter == 'last_month':
        sales = sales.filter(date_created__month=datetime.date.today().month - 1)

    # Filtering by total amount
    total_amount_filter = request.GET.get('total_amount_filter')
    if total_amount_filter:
        sales = sales.filter(total_amount__gte=int(total_amount_filter))

    # Filtering by sale item
    sale_item_filter = request.GET.get('sale_item_filter')
    if sale_item_filter:
        sales = sales.filter(saleitem__product__name__icontains=sale_item_filter)

    # Filtering by product
    product_filter = request.GET.get('product_filter')
    if product_filter:
        sales = sales.filter(saleitem__product__name__icontains=product_filter)

    # Filtering by cashier
    cashier_filter = request.GET.get('cashier_filter')
    if cashier_filter:
        sales = sales.filter(cashier__name__icontains=cashier_filter)

    # Filtering by branch
    branch_filter = request.GET.get('branch_filter')
    if branch_filter:
        sales = sales.filter(branch__name__icontains=branch_filter)

    # Pagination
    paginator = Paginator(sales, 10)  # Show 10 sales per page
    page_number = request.GET.get('page')
    sales_page = paginator.get_page(page_number)

    return render(request, 'reports/sales.html', {
        'sales': sales_page,
        'active_nav_item': active_nav_item,
        'paginator': paginator,
    })



@login_required
def manager_sales_list_view(request):
    branch = request.user.employee.branch
    sales = Sale.objects.filter(branch=branch)

    active_nav_item = 'branches'
    

    # Filtering by date
    date_filter = request.GET.get('date_filter')
    if date_filter == 'today':
        sales = sales.filter(date_created__date=datetime.date.today())
    elif date_filter == 'yesterday':
        sales = sales.filter(date_created__date=datetime.date.today() - datetime.timedelta(days=1))
    elif date_filter == 'last_week':
        sales = sales.filter(date_created__week=datetime.date.today().isocalendar()[1] - 1)
    elif date_filter == 'last_month':
        sales = sales.filter(date_created__month=datetime.date.today().month - 1)

    # Filtering by total amount
    total_amount_filter = request.GET.get('total_amount_filter')
    if total_amount_filter:
        sales = sales.filter(total_amount__gte=int(total_amount_filter))

    # Filtering by sale item
    sale_item_filter = request.GET.get('sale_item_filter')
    if sale_item_filter:
        sales = sales.filter(saleitem__product__name__icontains=sale_item_filter)

    # Filtering by product
    product_filter = request.GET.get('product_filter')
    if product_filter:
        sales = sales.filter(saleitem__product__name__icontains=product_filter)

    # Filtering by cashier
    cashier_filter = request.GET.get('cashier_filter')
    if cashier_filter:
        sales = sales.filter(cashier__name__icontains=cashier_filter)

    # Filtering by branch
    branch_filter = request.GET.get('branch_filter')
    if branch_filter:
        sales = sales.filter(branch__name__icontains=branch_filter)

    # Pagination
    paginator = Paginator(sales, 10)  # Show 10 sales per page
    page_number = request.GET.get('page')
    sales_page = paginator.get_page(page_number)

    return render(request, 'reports/branch_sales.html', {
        'sales': sales_page,
        'active_nav_item': active_nav_item,
        'paginator': paginator,
    })

