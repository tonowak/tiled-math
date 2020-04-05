from django.urls import path

from . import views

app_name = 'users'
urlpatterns = [
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('<int:u_id>', views.EditUser.as_view(), name='edit'),
    path('', views.index_view, name='index'),
]