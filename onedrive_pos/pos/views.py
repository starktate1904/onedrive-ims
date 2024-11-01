from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from .models import Sale, SaleItem
from products.models import Product,Category
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.template.loader import get_template
from django.http import HttpResponse
from datetime import date, datetime, timedelta
from staff.models import *
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from xhtml2pdf import pisa
from io import BytesIO
from django.contrib import messages
import logging





@cache_page(60 * 1)
@login_required
def sale_list(request):
    active_nav_item = 'pos'
    branch = request.user.employee.branch
    sales = Sale.objects.filter(branch=branch)

    # Filter by product
    product_query = request.GET.get('product', '').strip()
    if product_query:
        sales = sales.filter(saleitem__product__name__icontains=product_query)

    # Filter by date created
    date_query = request.GET.get('date_created', '').strip()
    if date_query:
        try:
            sales = sales.filter(date_created__date=date_query)
        except ValueError:
            messages.error(request, "Invalid date format. Please enter a valid date.")

    # Filter by total amount
    total_query = request.GET.get('total_amount', '').strip()
    if total_query:
        try:
            total_query = float(total_query)  # Ensure it's a float
            # You can change this logic based on your requirement
            sales = sales.filter(total_amount=total_query)  # Exact match
            # Or for a range, you can use:
            # sales = sales.filter(total_amount__gte=total_query)  # Greater than or equal to
            # sales = sales.filter(total_amount__lte=total_query)  # Less than or equal to
        except ValueError:
            messages.error(request, "Invalid total amount. Please enter a valid number.")

    # Order the sales before pagination
    sales = sales.order_by('-date_created')  # Order by date_created or any other field

    # Pagination
    paginator = Paginator(sales, 10)  # Show 10 sales per page
    page_number = request.GET.get('page')
    sales_page = paginator.get_page(page_number)

    if not sales_page:
        messages.info(request, "No sales found with the given filters.")

    return render(request, 'pos/sale_list.html', {
        'sales': sales_page,
        'product_query': product_query,
        'date_created': date_query,
        'total_amount': total_query,
        'active_nav_item': active_nav_item,
    })

@cache_page( 60 * 1)
@login_required
def view_sale(request, sale_id):
    active_nav_item = 'pos'
    sale = Sale.objects.get(id=sale_id)
    return render(request, 'pos/view_sale.html', {'sale': sale,'active_nav_item':active_nav_item})

@cache_page( 60 * 1)
@login_required
def create_sale(request):
    active_nav_item = 'pos'
    today = date.today()
    employee = Employee.objects.get(user=request.user)
    products = Product.objects.filter(branch=request.user.employee.branch)
    branch = request.user.employee.branch

    if request.method == 'POST':
        # Create a new sale
        sale = Sale.objects.create(branch=branch, total_amount=0, cashier_id=request.user.id)

        # Render the updated sale table and total amount as HTML
        sale_table_html = render_to_string('pos/sale_table.html', {'sale': sale})

        return JsonResponse({'sale_table': sale_table_html, 'total_amount': 0, 'sale_id': sale.id})

    else:
        # Handle GET request
        sale_id = request.GET.get('sale_id')
        sale_items = []
        total_amount = 0

        if sale_id:
            # Use the all_objects manager to get the sale
            try:
                sale = Sale.all_objects.get(id=sale_id)
                sale_items = SaleItem.objects.filter(sale=sale)  # Get the sale items for the current sale

                # Calculate the total for each sale item
                for item in sale_items:
                    item.total = item.quantity * item.product.price
                    item.save()

                # Calculate the total amount
                total_amount = sum(item.total for item in sale_items)

            except Sale.DoesNotExist:
                messages.error(request, "Sale not found.")
                return redirect('pos:create_sale')  # Redirect to create sale page or handle as needed

        else:
            # Create a new sale if no sale_id is provided
            sale = Sale.objects.create(branch=branch, total_amount=0, cashier_id=request.user.id)

        return render(request, 'pos/create_sale.html', {
            'products': products,
            'sale_items': sale_items,
            'sale': sale,
            'sale_id': sale.id,
            'total_amount': total_amount,
            'today': today,
            'employee': employee,
            'branch': branch,
            'active_nav_item': active_nav_item,
            'categories': products.values('category__name').distinct(),  # Get categories for filtering
        })


@cache_page( 60 * 1)
@login_required
def search_products(request):
    active_nav_item = 'pos'
    search_term = request.GET.get('search_term', '')
    category = request.GET.get('category', '')
    branch = request.user.employee.branch
    page = request.GET.get('page', 1)

    if category:
        products = Product.objects.filter(category__name=category, branch=branch).order_by('id')  # Add order_by
    else:
        products = Product.objects.filter(branch=branch).order_by('id')  # Add order_by

    if search_term:
        products = products.filter(
            Q(name__icontains=search_term) |
            Q(location__icontains=search_term) |
            Q(make__icontains=search_term) |
            Q(model__icontains=search_term) |
            Q(price__icontains=search_term)
        )

    paginator = Paginator(products, 10)  # Show 10 products per page
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'location': product.location,
            'make': product.make,
            'model': product.model,
            'quantity': product.quantity,
            'price': product.price,
            'category': product.category.name,
        })

    return JsonResponse({
        'active_nav_item': active_nav_item,
        'results': results,
        'has_previous': products.has_previous(),
        'has_next': products.has_next(),
        'previous_page_number': products.previous_page_number() if products.has_previous() else None,
        'next_page_number': products.next_page_number() if products.has_next() else None,
        'current_page_number': products.number,  # Add current page number
    }, safe=False)


@cache_page( 60 * 1)
@login_required
def complete_sale(request):
    today = date.today()

    if request.method == 'POST':
        sale_id = request.POST.get('sale_id')
        amount_paid = float(request.POST.get('amount_paid'))
        

        try:
            sale = Sale.all_objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return JsonResponse({'error': 'Sale does not exist'})

        # Calculate the total amount of the sale
        total_amount = sum(item.quantity * item.price for item in SaleItem.objects.filter(sale=sale))

        # Update the product quantity
        for item in sale.saleitem_set.all():
            product = item.product
            print("Before update:", product.quantity)
            product.quantity -= item.quantity
            print("Product quantity after calculation:", product.quantity)
            product.save()
            print("After update:", product.quantity)

        # Calculate the change
        change = amount_paid - float(total_amount)

        # Create a new sale
        new_sale = Sale.objects.create(branch=request.user.employee.branch, total_amount=0, cashier_id=request.user.id)

        # Render the receipt as HTML
        receipt_html = render_to_string('pos/receipt.html', {'sale': sale, 'sale_items': sale.saleitem_set.all(), 'amount_paid': amount_paid, 'change': change,'today':today})

        return JsonResponse({'message': 'Sale completed successfully', 'change': change, 'new_sale_id': new_sale.id, 'receipt_html': receipt_html})
    else:
        return HttpResponse('Invalid request method')


@login_required
def add_product_to_sale(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity'))
        sale_id = request.POST.get('sale_id')

        try:
            sale = Sale.all_objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return JsonResponse({'error': 'Sale does not exist'})

        product = Product.objects.get(id=product_id)

        # Check if product is already in the sale
        if SaleItem.objects.filter(sale=sale, product=product).exists():
            sale_item = SaleItem.objects.get(sale=sale, product=product)
            sale_item.quantity += quantity
            sale_item.save()
        else:
            SaleItem.objects.create(sale=sale, product=product, quantity=quantity, price=product.price)

        # Recalculate the total amount
        sale.total_amount = sum(item.quantity * item.price for item in SaleItem.objects.filter(sale=sale))
        sale.save()

        # Render the updated sale table and total amount as HTML
        sale_items = SaleItem.objects.filter(sale=sale)
        sale_table_html = render_to_string('pos/sale_table.html', {'sale': sale, 'sale_items': sale_items})

        return JsonResponse({'sale_table': sale_table_html, 'total_amount': sale.total_amount})
    else:
        return HttpResponse('Invalid request method')


@login_required
def remove_product_from_sale(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        sale_id = request.POST.get('sale_id')

        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return JsonResponse({'error': 'Sale does not exist'})

        product = Product.objects.get(id=product_id)

        # Check if product is in the sale
        if SaleItem.objects.filter(sale=sale, product=product).exists():
            sale_item = SaleItem.objects.get(sale=sale, product=product)
            sale_item.delete()

            # Recalculate the total amount
            sale.total_amount = sum(item.quantity * item.price for item in SaleItem.objects.filter(sale=sale))
            sale.save()

            # Render the updated sale table and total amount as HTML
            sale_items = SaleItem.objects.filter(sale=sale)
            sale_table_html = render_to_string('pos/sale_table.html', {'sale': sale, 'sale_items': sale_items})

            return JsonResponse({'sale_table': sale_table_html, 'total_amount': sale.total_amount})
        else:
            return JsonResponse({'error': 'Product is not in the sale'})
    else:
        return HttpResponse('Invalid request method')
  
# Set up logging
logger = logging.getLogger(__name__)

@cache_page(60 * 5)
@login_required
def generate_sales_report(request):
    # Initialize the queryset
    sales = Sale.objects.all()

    # Get filter parameters from the request
    date_filter = request.GET.get('date_filter')
    total_amount_filter = request.GET.get('total_amount_filter')
    sale_item_filter = request.GET.get('sale_item_filter')
    branch_filter = request.GET.get('branch_filter')

    # Log the received filter parameters
    logger.debug(f"Received filters - Date: {date_filter}, Total Amount: {total_amount_filter}, Sale Item: {sale_item_filter}, Branch: {branch_filter}")

    # Apply filters based on the parameters
    if date_filter:
        if date_filter == 'today':
            sales = sales.filter(date_created__date=datetime.today())
        elif date_filter == 'yesterday':
            sales = sales.filter(date_created__date=datetime.today() - timedelta(days=1))
        elif date_filter == 'last_week':
            sales = sales.filter(date_created__date__gte=datetime.today() - timedelta(days=7))
        elif date_filter == 'last_month':
            sales = sales.filter(date_created__date__gte=datetime.today() - timedelta(days=30))

    if total_amount_filter:
        try:
            total_amount_filter = float(total_amount_filter)
            sales = sales.filter(total_amount__gte=total_amount_filter)
        except ValueError:
            logger.error("Invalid total amount filter value.")
            pass  # Handle the case where conversion fails

    if sale_item_filter:
        sales = sales.filter(saleitem__product__name__icontains=sale_item_filter)

    if branch_filter:
        sales = sales.filter(branch__name__icontains=branch_filter)

    # Log the final queryset
    logger.debug(f"Filtered sales count: {sales.count()}")

    # Prepare the PDF report
    template = get_template('reports/sales_report.html')
    context = {'sales': sales}
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf, encoding='utf-8', disable_font_loading=False)    
    pdf.seek(0)
    response.write(pdf.read())
    return response

@cache_page( 60 * 5)
@login_required
def branch_generate_sales_report(request):
    try:
        # Get filter parameters from the request
        date_filter = request.GET.get('date_filter')
        total_amount_filter = request.GET.get('total_amount_filter')
        sale_item_filter = request.GET.get('sale_item_filter')
        branch_filter = request.GET.get('branch_filter')

        # Start with sales for the user's branch
        sales = Sale.objects.filter(branch=request.user.employee.branch)

        # Apply filters based on the parameters
        if date_filter == 'today':
            sales = sales.filter(date_created__date=datetime.today())
        elif date_filter == 'yesterday':
            sales = sales.filter(date_created__date=datetime.today() - timedelta(days=1))
        elif date_filter == 'last_week':
            sales = sales.filter(date_created__week=datetime.today().isocalendar()[1] - 1)
        elif date_filter == 'last_month':
            sales = sales.filter(date_created__month=datetime.today().month - 1)

        if total_amount_filter:
            sales = sales.filter(total_amount__gte=int(total_amount_filter))

        if sale_item_filter:
            sales = sales.filter(saleitem__product__name__icontains=sale_item_filter)

        if branch_filter:
            sales = sales.filter(branch__name__icontains=branch_filter)

        if not sales:
            messages.info(request, "No sales found for this branch with the applied filters.")
            return redirect('auth_pos:manager_sale_list')  # Replace with your redirect URL

        # Generate PDF report
        template = get_template('reports/sales_report.html')
        context = {'sales': sales}
        html = template.render(context)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
        pdf = BytesIO()
        pisa.CreatePDF(html, dest=pdf, encoding='utf-8', disable_font_loading=True)
        pdf.seek(0)
        response.write(pdf.read())
        return response
    except Exception as e:
        messages.error(request, "An error occurred while generating the sales report. Please try again.")
        return redirect('auth_pos:manager_sale_list')  # Replace with your redirect URL


@cache_page( 60 * 5)
@login_required
def view_pos_products(request):
    active_nav_item = 'products'
    if request.user.role == 'cashier':
        branch = request.user.employee.branch
        products = Product.objects.filter(branch=branch)
        product_count = products.count()

        # Get the search query from the GET parameters
        search_query = request.GET.get('search', '')

        # Filter products based on the search query
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(location__icontains=search_query) |
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
        }
        return render(request, 'pos/pos_products.html', context)
    else:
        return redirect('auth_pos:login')