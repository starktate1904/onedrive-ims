from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    
    path('admin/', admin.site.urls),
    path('', include('auth_pos.urls')),
    path('products/', include('products.urls')),
    path('branches/', include('branches.urls')),
    path('pos/', include('pos.urls')),
    path('staff/', include('staff.urls')),
    path('profile/', include('user_profile.urls'))


]   + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)