from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router_v1 = SimpleRouter()

auth_patterns_v1 = [
    path('signup/', views.SignUpView.as_view()),
    path('token/', views.TokenView.as_view())
]

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/auth/', include(auth_patterns_v1)),
]