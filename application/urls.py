
from application import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('filter_data/', views.filter_data, name='filter_data'),
    path('upload/', views.upload, name='upload'),
    path('tables/', views.tables, name='tables'),
    path('workouts/', views.workouts, name='workouts'),
    path('charts/', views.charts, name='charts'),
    path('workouts/<int:workout_id>/', views.workout_detail, name='workout_detail'),
    path('register/', views.register_request, name='register'),
    path('login/', views.login_request, name="login"),
    path('logout/', views.logout_request, name='logout'),
]
from . import views


# This is only a temporary method to store the file locally
# Launch version will upload file to SQL DB
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
