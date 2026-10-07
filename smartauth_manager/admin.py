from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(ClaimCatalog)
admin.site.register(Permission)
admin.site.register(GroupClient)
admin.site.register(Profile)
admin.site.register(Role)