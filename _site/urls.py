"""
URL configuration for appenv project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import TemplateView
from smartauth_manager.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('provider/', include('oidc_provider.urls', namespace='oidc_provider')),
    path("provider/login/", auth_views.LoginView.as_view(template_name='oidc_main.html'), name='login'),
    path('client/', include('mozilla_django_oidc.urls')),
    path('', MainView.as_view(), name='home'),
    path('aplicaciones/', ApplicationCatalogView.as_view(), name='application_catalog'),
    path('aplicaciones/<application_code>/', ApplicationDetailModalView.as_view(), name='application_detail'),
    path('oidc/proveedor/rsa/', RSAKeyCatalog.as_view(), name="rsakeycatalog"),
    path('oidc/proveedor/rsa/capturar/', RsaKeyModalView.as_view(), name="rsakeycapture"),
    path('oidc/proveedor/rsa/subir/', RsaKeyUploadModal.as_view(), name="rsakeyupload"),
    path('oidc/proveedor/rsa/<int:pk>/', RsaKeyModalView.as_view(), name="rsakeyedit"),
    path('oidc/proveedor/rsa/<int:pk>/descargar/', rsaDownloadPem, name="rsakeydownload"),
    path('oidc/proveedor/clientes/', ClientCatalog.as_view(), name="client_catalog"),
    path('oidc/proveedor/clientes/agregar/', ClientFormModal.as_view(), name="client_add"),
    path('oidc/proveedor/clientes/<int:pk>/modificar/', ClientFormModal.as_view(), name="client_edit"),
    path('auth/grupos/', GroupCatalog.as_view(), name="group_catalog"),
    path('auth/grupos/agregar/', GroupFormModal.as_view(), name="group_add"),
    path('auth/grupos/<int:pk>/modificar/', GroupFormModal.as_view(), name="group_edit"),
    path('auth/usuarios/', UserCatalogView.as_view(), name='user_catalog'),
    path('auth/usuarios/agregar/', UserFormModal.as_view(), name='user_add'),
    path('auth/usuarios/cambiarEstatus/', toggleUserStatus, name='user_toggle_status'),
    path('auth/usuarios/<username>/', UserDetailModalView.as_view(), name='user_view'),
    path('auth/usuarios/<username>/modificar/', UserFormModal.as_view(), name='user_edit'),
    path('auth/usuarios/<username>/parametros/', UserClaimsManager.as_view(), name='user_claims'),
    path('auth/usuarios/<username>/pwd/', SetPasswordFormModal.as_view(), name='user_set_pwd'),
    path('oidc/administrador/usuarios/<username>/claims/', UserClaimsManager.as_view(), name='user_claim_manager'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns