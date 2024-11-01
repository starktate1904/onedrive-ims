from django.urls import path
from . import views

app_name= 'profile'

urlpatterns = [
    path('profile/detail/<int:pk>/', views.profile_detail, name='profile_detail'),
    path('profile/<int:pk>/change-password/',views.change_password, name='change_password'),
    path('profile/<int:pk>/update-user-details/', views.update_user_details, name='update_user_details'),
    
]