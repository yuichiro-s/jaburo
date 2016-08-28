from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^acl_search/', include('acl_search.urls')),
    url(r'^admin/', admin.site.urls),
]
