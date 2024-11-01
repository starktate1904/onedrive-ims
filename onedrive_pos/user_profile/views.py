from django.shortcuts import render, redirect, get_object_or_404
from staff.models import Employee
from auth_pos.models import User
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.views.decorators.cache import cache_page


@cache_page( 60 * 5)
@login_required
def profile_detail(request, pk):
    active_nav_item = 'profile'
    user = get_object_or_404(User, pk=pk)

    # Use get_or_create to simplify user profile retrieval
    user_profile, created = UserProfile.objects.get_or_create(user=user, defaults={'employee': Employee.objects.get(user=user)})

    context = {
        'active_nav_link': active_nav_item,
        'user': user,
        'user_profile': user_profile,
    }
    return render(request, 'profile/profile.html', context)

@cache_page( 60 * 5)
@login_required
def change_password(request, pk):
    user = request.user  # Assuming the logged-in user is the one changing their password

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Keep the user logged in after password change
            messages.success(request, 'Password changed successfully!')
            return redirect('profile:profile_detail', pk=user.pk)  # Redirect to the profile detail view
        else:
            messages.error(request, 'Passwords do not match.')

    return render(request, 'profile/change_password.html', {'messages': messages.get_messages(request), 'user': user})

@cache_page( 60 * 5)
@login_required
def update_user_details(request, pk):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        profile_image = request.FILES.get('profile_pic')
        print(request.FILES)

        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email
        user.save()

        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            user_profile = UserProfile.objects.create(user=user)

        if profile_image:
            user_profile.profile_pic = profile_image
        user_profile.save()

        messages.success(request, 'User  details updated successfully!')
        return redirect('profile:profile_detail', pk=request.user.pk)
    return render(request, 'profile/profile.html', {'messages': messages.get_messages(request)})