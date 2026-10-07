from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from django.contrib.auth.models import User, Group
from oidc_provider.models import Client
from smartauth_provider.models import Scope, Claim

# Create your models here.
class Permission(models.Model):
    client = models.ForeignKey(Client, verbose_name="Aplicación Cliente", on_delete=models.CASCADE)
    code = models.CharField(max_length=100, verbose_name="Código del permiso")
    description = models.TextField(verbose_name="Descripción del permiso")

    def __str__(self):
        return f'{self.client.name} : {self.code}'

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("code"), "client", name="unique_client_permission")
        ]

class GroupClient(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='+', verbose_name="Grupo")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='+', verbose_name="Aplicación Cliente")

    @classmethod
    def get_client_ids_by_group(cls, group):
        return cls.objects.filter(group=group).values_list('client__client_id', flat=True).distinct()

    @classmethod
    def get_client_names_by_group(cls, group):
        return cls.objects.filter(group=group).values_list('client__name', flat=True).distinct()

    class Meta:
        constraints = [
            models.UniqueConstraint("group", "client", name="unique_group_client")
        ]

class UserProfilePicture(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuario", related_name='profile_picture')
    picture = models.ImageField(verbose_name="Imagen de Perfil", upload_to="auth/profile_pics/")

class ClaimCatalog(models.Model):
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="catalog_values", verbose_name="Claim")
    value = models.CharField(verbose_name="Valor", max_length=255)
    description = models.CharField(verbose_name="Nombre o Descripción", max_length=255)
    parent_value = models.CharField(verbose_name="Valor de Claim Padre", max_length=255, blank=True)

    def __str__(self):
        str = f'{self.claim.description}: {self.value} - {self.description}'
        if self.claim.parent_claim:
            str = f'{self.claim.parent_claim.description}: {self.parent_value} -> {str}'
        return str

    class Meta:
        constraints = [
            models.UniqueConstraint("claim","value","parent_value", name="unique_claim_catalog_Value")
        ]

class Profile(models.Model):
    user = models.ForeignKey(User, verbose_name="Usuario", on_delete=models.CASCADE)
    client = models.ForeignKey(Client, verbose_name="Aplicación Cliente", on_delete=models.CASCADE)
    permissions = models.ManyToManyField(Permission, verbose_name="Permisos de usuario", blank=True)

    def __str__(self):
        return f'{self.client}:{self.user}'

class Role(models.Model):
    group = models.ForeignKey(Group, verbose_name="Grupo", on_delete=models.CASCADE)
    client = models.ForeignKey(Client, verbose_name="Aplicación Cliente", on_delete=models.CASCADE)
    name = models.CharField(verbose_name="Rol", max_length=150)
    permissions = models.ManyToManyField(Permission, verbose_name="Permisos de grupo", blank=True)

    def __str__(self):
        return f'{self.client}:{self.group} - {self.name}'
