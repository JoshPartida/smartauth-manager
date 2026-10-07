from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.forms import UsernameField as DjangoUsernameField, SetPasswordMixin as DjangoSetPasswordMixin, UserCreationForm as DjangoUserCreationForm
from django.shortcuts import render
from django.forms import forms, widgets, ModelForm
from django.core.validators import validate_unicode_slug
from oidc_provider.models import Client, CLIENT_TYPE_CHOICES
from smartcloud.ux.forms.fields import *
from smartcloud.ux.forms.widgets import ScrollingSize, SelectionDropdown, MultiCheckbox, MultipleSelectionDropdown
from smartcloud.ux.forms.forms import Form, FieldGroup
from smartcloud.applications.models import Application
from smartauth_provider.models import Scope, Claim, UserClaim
from .models import ClaimCatalog

__all__ = (
    "RsaKeyForm",
    "RsaKeyUploadForm",
    "ClientForm",
    "GroupForm",
    "UserCreationForm",
    "UserChangeForm",
    "ClaimCatalogForm",
    "SetPasswordForm",
)

CLAIM_FORMS = {}

class RsaKeyForm(Form):
    key = CharField(label="Llave Privada", help_text="Captura o pega el texto de tu llave privada RSA, en formato PEM", widget=widgets.Textarea)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        data = kwargs.get("data", None)
        if data and data["kid"] and data["public_key"]:
            self.fields["public_key"] = CharField(
                label="Llave Pública", 
                help_text="Llave pública correspondiente a la llave privada RSA", 
                widget=forms.Textarea(attrs={"readonly":""}),
                required=False,
                initial=data["public_key"],
            )
            self.fields["kid"] = CharField(
                label="kid", 
                help_text="Identificador de la llave", 
                widget=forms.TextInput(attrs={"readonly":""}),
                required=False,
                initial=data["kid"],
            )
            self.field_groups = [
                FieldGroup(field_names=["key","public_key"])
            ]

class RsaKeyUploadForm(Form):
    file_extensions=[".pem"]
    file_types=["application/x-pem-file"]
    key_file = DragDropFileField(label="Selecciona un archivo de llave", file_extensions=file_extensions, file_types=file_types)

def client_choices():
    applications = Application.objects.all()
    choices = []
    for application in applications:
        choices.append((application.name, application.name))
    return choices

def scope_choices():
    scopes = Scope.objects.all()
    choices = []
    for scope in scopes:
        choices.append((scope.pk, scope.code))
    return choices

class ClientForm(Form):
    name = CharField(
        label="Nombre", 
        widget=SelectionDropdown(
            attrs={"class": "search"}, 
            choices=client_choices,
            init_params_object={"allowAdditions":True}
        ), 
        columns_width=ColumnsWidth.FOUR
    )
    client_type = DropdownField(label="Tipo de Cliente", choices=CLIENT_TYPE_CHOICES, columns_width=ColumnsWidth.FOUR)
    client_id = CharField(label="Clave", max_length=255, validators=[validate_unicode_slug])
    #client_secret = CharField(label="Secreto", max_length=255, required=False, widget=djangowidgets.TextInput(attrs={"readonly":"readonly"}))
    scope = MultiSelectDropdownField(label="Scopes", choices=scope_choices)
    redirect_uris = CharField(
        label="URIs de redireccionamiento de login", 
        help_text="URLs a las que el servidor enviará la información de identificación del usuario. " \
        "Una por línea.",
        widget=widgets.Textarea
    )
    post_logout_redirect_uris = CharField(
        label="URIs de redireccionamiento de logout", 
        help_text="URLs a las que el servidor redireccionará cuando el usuario cierre sesión. " \
        "Una por línea.",
        widget=widgets.Textarea,
        required=False
    )
    contact_email = EmailField(label="Correo de contacto", required=False)
    website_url = URLField(label="URL Principal", required=False)
    terms_url = URLField(label="URL de Términos y Condiciones", required=False)
    logo = ImageField(label="Imagen de logo", required=False)

    field_groups = [
        FieldGroup(["client_type", "client_id"]), 
        FieldGroup(["redirect_uris","post_logout_redirect_uris"]),
        FieldGroup(["contact_email","website_url","terms_url"]),
    ]

class GroupForm(Form):
    name = CharField(label="Grupo", columns_width=ColumnsWidth.FOUR)
    clients = GroupedMultiModelField(queryset=Client.objects, label="Aplicaciones Cliente", widget=MultiCheckbox(scrolling=ScrollingSize.SHORT, attrs={"class":"toggle"}))
    permissions = GroupedMultiModelField(queryset=Permission.objects, label="Permisos Internos", widget=MultiCheckbox(scrolling=ScrollingSize.SHORT, attrs={"class":"toggle"}), required=False)
    field_groups = [FieldGroup(["clients","permissions"])]

class SetPasswordMixin(DjangoSetPasswordMixin):
    @staticmethod
    def create_password_fields(label1 = ..., label2 = ...):
        password1, password2 = DjangoSetPasswordMixin.create_password_fields(label1, label2)
        password1 = CharField(
            help_text_popup=False, 
            label=password1.label,
            required=password1.required,
            strip=password1.strip,
            widget=password1.widget,
            help_text=password1.help_text
        )
        password2 = CharField(
            help_text_popup=False, 
            label=password2.label,
            required=password2.required,
            strip=password2.strip,
            widget=password2.widget,
            help_text=password2.help_text
        )
        return password1, password2

class UsernameField(CharField, DjangoUsernameField):
    pass

class UserCreationForm(Form, DjangoUserCreationForm):
    email = EmailField(label="Dirección de correo electrónico", required=True)
    first_name = CharField(label="Nombre", required=True)
    profile_picture = ImageField(label="Imagen de Perfil", required=False)
    password1, password2 = SetPasswordMixin.create_password_fields("Contraseña", "Confirmar Contraseña")
    field_groups = [
        FieldGroup(["username", "email"]),
        FieldGroup(["first_name", "last_name"]),
        FieldGroup(["password1", "password2"]),
    ]

    class Meta(DjangoUserCreationForm.Meta):
        fields = ["username", "email", "groups", "first_name", "last_name"]
        field_classes = {
            "username": UsernameField,
            "email": EmailField,
            "groups": GroupedMultiModelField,
            "first_name": CharField,
            "last_name": CharField,
        }
        widgets = {
            "groups": MultipleSelectionDropdown,
        }

class UserChangeForm(Form, ModelForm):
    email = EmailField(label="Dirección de correo electrónico", required=True)
    first_name = CharField(label="Nombre", required=True)
    profile_picture = ImageField(label="Imagen de Perfil", required=False)
    field_groups = [
        FieldGroup(["first_name", "last_name"]),
    ]

    class Meta(DjangoUserCreationForm.Meta):
        fields = ["email", "groups", "first_name", "last_name"]
        field_classes = {
            "email": EmailField,
            "groups": GroupedMultiModelField,
            "first_name": CharField,
            "last_name": CharField,
        }
        widgets = {
            "groups": MultipleSelectionDropdown,
        }

class ClaimCatalogForm(Form):
    claim:Claim = None
    user = None

    def __init__(self, claim, user, **kwargs):
        super().__init__(**kwargs)
        self.claim = claim
        self.user = user
        catalog_qs = ClaimCatalog.objects.filter(claim=claim)
        self.fields[f"{claim.code}_enable"] = BooleanField(checkbox_variant=CheckboxVariant.TOGGLE, required=False, label="Asignar claim")
        self.fields[f"{claim.code}_use_all"] = BooleanField(checkbox_variant=CheckboxVariant.TOGGLE, required=False, label="Usar Todos")
        self.fields[f"{claim.code}_catalog"] = GroupedMultiModelField(queryset=catalog_qs, label="Valores Disponibles", widget=MultiCheckbox(scrolling=ScrollingSize.SHORT, attrs={"class":"toggle"}), required=False)
        self.field_groups.append(FieldGroup([f"{claim.code}_enable",f"{claim.code}_use_all"], "inline seven"))
        user_values = UserClaim.objects.filter(user=user, claim=claim).values_list("pk", flat=True).distinct()
        claim_catalog_initial = [pk for pk in user_values]
        if claim_catalog_initial:
            self.fields[f"{claim.code}_catalog"].initial = claim_catalog_initial

class SetPasswordForm(SetPasswordMixin, Form):
    new_password1, new_password2 = SetPasswordMixin.create_password_fields("Contraseña", "Confirmar Contraseña")
    field_groups = [FieldGroup(["new_password1","new_password2"])]

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        self.validate_passwords("new_password1", "new_password2")
        self.validate_password_for_user(self.user, "new_password2")
        return super().clean()

    def save(self, commit=True):
        return self.set_password_and_save(self.user, "new_password1", commit=commit)
