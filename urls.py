from django.conf.urls import url, include
from rest_framework import routers
from diploma.recsystems import views

router = routers.DefaultRouter()
router.register(r'content-based', views.ContentBasedViewSet)
router.register(r'collaborative', views.CollaborativeViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]