from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # This is the magic line that connects your main project to your app!
    path('', include('approvals.urls')), 
    path('accounts/', include('django.contrib.auth.urls')),
]