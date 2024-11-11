from django.urls import path
from restapp.views import *
from restapp import views
from django.conf.urls.static import static
urlpatterns = [
    path('',views.home,name="home"),
    path('users/register/',views.registerUser,name="register"),
    path('users/login/',views.loginUser,name="login"),
    # path('activate/<uidb64>/<token>',views.ActivateAccountView.as_view(),name='activate'),
    path('activate/<uidb64>/<token>',views.activateAccount,name='activate'),

    path('media/<path:path>', protected_media, name='protected_media'),
    path('upload-file/', FileUploadView.as_view(), name='upload-file'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)