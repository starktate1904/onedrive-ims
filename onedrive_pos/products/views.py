from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import cache_page
from django.urls import reverse
from .models import Product, Category
from branches.models import Branch
from django.contrib import messages
from django.core.exceptions import ValidationError
import csv
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

# Soft deleting a product after it reaches 0 on quantity
@user_passes_test(lambda user: user.has_perm('main.view_product_list'))
@receiver(post_save, sender=Product)
def soft_delete_product(sender, instance, **kwargs):
    if isinstance(instance.quantity, int) and instance.quantity <= 0:
        instance.is_deleted = True
        instance.save()

# Helper function to handle messages and context
def get_context_with_messages(active_nav_item, request, additional_context=None):
    context = {
        'active_nav_item': active_nav_item,
        'messages': messages.get_messages(request)
    }
    if additional_context:
        context.update(additional_context)
    return context

# Carpart / product management CRUD views
@cache_page(60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.view_product_list'))
def product_list(request):
    active_nav_item = 'products'
    branch = Branch.objects.all()
    categories = Category.objects.all()
    products = Product.objects.filter(is_deleted=False)

    # Get the search query from the GET parameters
    search_query = request.GET.get('search')
    category_query = request.GET.get('category')

    # Filter products based on the search query
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(make__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(price__icontains=search_query)
        )
    if category_query:
        products = products.filter(category_id=category_query)

    # Paginate the filtered products
    page_size = 10
    paginator = Paginator(products, page_size)

    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = get_context_with_messages(active_nav_item, request, {
        'products': products,
        'paginator': paginator,
        'search_query': search_query,
        'branch': branch,
        'categories': categories,
        'category_query': category_query
    })
    return render(request, 'products/products.html', context)


@cache_page(60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.view_product_list'))
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
@user_passes_test(lambda user: user.has_perm('main.add_product'))
def upload_products_csv(request):
    active_nav_item = 'products'
    products = Product.objects.filter(is_deleted=False)
    categories = Category.objects.all()

    context = get_context_with_messages(active_nav_item, request, {
        'products': products,
        'categories': categories
    })

    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if csv_file and csv_file.name.endswith('.csv'):
            decoded_file = csv_file.read().decode('utf-8')
            reader = csv.DictReader(decoded_file.splitlines())

            for row in reader:
                try:
                    name = row['name']
                    make = row['make']
                    model = row['model']
                    location = row['location']
                    price = row['price']
                    quantity = int(row['quantity'])  # Convert quantity to integer
                    branch_id = int(row['branch_id'])  # Convert branch ID to integer
                    category_id = int(row['category_id'])

                    # Get the branch and category objects based on ID
                    branch = get_object_or_404(Branch, pk=branch_id)
                    category = get_object_or_404(Category, id=category_id)

                    product = Product(
                        name=name,
                        make=make,
                        model=model,
                        location=location,
                        price=price,
                        quantity=quantity,
                        branch=branch,
                        category=category,
                    )
                    product.save()
                except (KeyError, ValueError) as e:  # Handle missing or invalid data
                    message = f"Error processing row: {row}. Missing or invalid data ({e})"
                    messages.error(request, message)  # Display error message
                except ValidationError as e:  # Handle validation errors
                    message = f"Error saving product: {e}"
                    messages.error(request, message)  # Display validation error message
            messages.success(request, 'Products uploaded successfully!')
            return HttpResponseRedirect(reverse('products:product_list'))
        else:
            messages.error(request, 'Invalid file format. Please upload a CSV file.')
            return render(request, 'products/products.html', context)  # Re-render form

    return render(request, 'products/products.html', context)  # Render upload form


@cache_page(60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.add_product'))
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
def product_create(request):
    active_nav_item = 'products'
    if request.method == 'POST':
        name = request.POST.get('name')
        make = request.POST.get('make')
        model = request.POST.get('model')
        location = request.POST.get('location')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        branch_id = request.POST.get('branch')
        category_id = request.POST.get('category')

        # Validate input
        if not make or not name or not model or not location or not price or not quantity or not branch_id or not category_id:
            messages.error(request, 'Please fill in all fields')
            return render(request, 'products/products.html')

        # Get the branch and category objects based on ID
        branch = get_object_or_404(Branch, pk=branch_id)
        category = get_object_or_404(Category, id=category_id)

        # Create the product object
        Product.objects.create(name=name, make=make, model=model, location=location, price=price, branch=branch, quantity=quantity, category=category)
        messages.success(request, 'Product created successfully!')
        return redirect('products:product_list')  # Redirect to branch list after success

    branch = Branch.objects.all()
    categories = Category.objects.all()
    context = get_context_with_messages(active_nav_item, request, {
        'branch': branch,
        'categories': categories
    })
    return render(request, 'products/products.html', context)


@cache_page(60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.view_product_list'))
@user_passes_test(lambda user: user.has_perm('main.view_branch_list'))
@user_passes_test(lambda user: user.has_perm('main.update_product'))
def product_update(request, product_id):
    active_nav_item = 'products'
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        make = request.POST.get('make')
        model = request.POST.get('model')
        location = request.POST.get('location')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        branch_id = request.POST.get ('branch')
        category_id = request.POST.get('category')

        # Get the branch and category objects based on ID
        branch = get_object_or_404(Branch, id=branch_id)
        category = get_object_or_404(Category, id=category_id)

        try:
            product.name = name  # update the product name
            product.make = make  # update the product make
            product.model = model  # Update the products model
            product.location = location  # Update the products descriptiom
            product.price = price  # Update the prodct's price
            product.quantity = quantity
            product.branch = branch  # Update the product's branch
            product.category = category  # Update the product's category
            product.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('products:product_list')
        except Product.DoesNotExist:
            messages.error(request, 'Product Does not Exist.')
    else:
        branch = Branch.objects.all()
        categories = Category.objects.all()
        context = get_context_with_messages(active_nav_item, request, {
            'product': product,
            'branch': branch,
            'categories': categories
        })
        return render(request, 'products/products.html', context)


@cache_page(60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.delete_product'))
@user_passes_test(lambda user: user.has_perm('main.view_product_list'))
def product_delete(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product.delete()  # Use the custom delete method
    messages.success(request, 'Product deleted successfully!')
    return redirect('products:product_list')



@cache_page(60 * 1)
@login_required
@user_passes_test(lambda user: user.has_perm('main.restore_product'))
@user_passes_test(lambda user: user.has_perm('main.view_product_list'))
def product_restore(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product.restore()
    messages.success(request, 'Product restored successfully!')
    return redirect('products:product_list')