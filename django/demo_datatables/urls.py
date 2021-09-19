"""demo_datatables URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.apps import apps

urlpatterns = [
    path('', include('show_src_code.urls')),
    path('admin/', admin.site.urls),
]

a = apps.get_app_configs()
for c in a:
    if hasattr(c, 'urls'):
        urlpatterns += [path('', include(c.urls))]
