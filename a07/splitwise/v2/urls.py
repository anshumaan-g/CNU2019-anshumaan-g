from django.conf.urls import url
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from v2 import views

router = DefaultRouter()
# router.register(r'api/v2', views.ToDoViewset)

urlpatterns = [
    # url(r'^', include(router.urls)),
    path('', views.ping),
    path('ping', views.ping),
    path('sanitize', views.sanitize),
    path('accounts/signup/', views.signup),
    path('accounts/login/', views.login),
    path('accounts/logout', views.logout_view),
    path('expenses', views.expense),
    path('expenses/<int:expense_id>', views.idexpense),
    path('categories', views.category),
    path('categories/<int:category_id>', views.get_single_category),
    path('balances', views.get_all_balances),
    path('users/<int:friend_id>/balances/', views.get_specific_balance),
    path('settle', views.settle),
    path('profile', views.profile),
    path('report', views.report)
]

handler500 = views.handler500
