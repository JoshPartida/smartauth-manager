import json
from hashlib import sha224
from Cryptodome.PublicKey import RSA
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.views.generic import TemplateView
from django.views.decorators.http import require_POST
from django import urls
from oidc_provider.models import Client, CLIENT_TYPE_CHOICES, RSAKey, ResponseType
from smartcloud.applications.models import Application
from smartcloud.ux.dashboard.views import *
from smartcloud.ux.views import SearchMode, SelectMode
from smartauth_provider.models import Claim, UserClaim
from .models import GroupClient, UserProfilePicture, ClaimCatalog
from .forms import *

# Create your views here.
class MainView(TemplateView):
    template_name = "ux/dashboard/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class GroupCatalogView(CatalogView):
    module_code = "groupcatalog"
    actions = [
        ModuleAction(label="Nuevo Grupo", target="grupos/agregar", target_type=ActionTargetType.MODAL, id="add_group", icon="plus", permissions=["auth.add_group"])
    ]
    item_actions = [
        ItemAction(label="Modificar", target="grupos/${pk}/", target_type=ActionTargetType.MODAL, icon="edit", permissions=["auth.change_group"], reference_fields=["pk"]),
        ItemAction(label="Eliminar", target="deleteGroup", target_type=ActionTargetType.FUNCTION, icon="trash alternate", permissions=["auth.remove_group"], reference_fields=["pk", "name"]),
    ]
    item_fields = [
        ItemField(reference_field="group", label="Grupo"),
        ItemField(reference_field="clients", label="Aplicaciones Cliente"),
    ]

    def get_queryset(self):
        qs = []
        for group in Group.objects.all():
            clients = GroupClient.get_client_names_by_group(group)
            qs.append({"pk": group.pk, "group": group.name, "clients": ', '.join(clients)})
        return qs

class ApplicationCatalogView(CatalogView):
    model = Application
    module_code = "catalogapplications"
    detail_action = ItemAction("Detalle", target="aplicaciones/${code}/", target_type=ActionTargetType.MODAL, reference_fields=["code"], icon="info circle")

    item_fields = [
        ItemField(reference_field="code", label="Clave"),
        ItemField(reference_field="name", label="Nombre"),
        ItemField(reference_field="version", label="Versión", permissions=['application.edit_module'])
    ]

class ApplicationDetailModalView(ModalView):
    template_name = "manager/application/detail_modal.html"
    content_classes = ["image"]

    def get_context_data(self, **kwargs):
        application_code = kwargs.get("application_code", None)
        try:
            application = Application.objects.get(code=application_code)
            self.name = application.name
            message = ""
        except Application.DoesNotExist:
            application = None
            message = "No se encontró la aplicación especificada"
        context = super().get_context_data(**kwargs)
        context["application"] = application
        context["message"] = message
        return context

class UserCatalogView(CatalogView):
    module_code = 'usercatalog'
    icon = 'user'
    item_fields = [
        ItemField(reference_field='username', label="Usuario"),
        ItemField(reference_field='first_name', label="Nombre"),
        ItemField(reference_field='last_name',label="Apellidos"),
        ItemField(reference_field="groups",label="Grupos"),
        ItemField(reference_field='is_active', label="Activo", format=ItemFieldFormat.BOOL),
        ItemField(reference_field='is_superuser', label="Es Administrador", format=ItemFieldFormat.BOOL, permissions=["superuser"]),
    ]
    actions = [
        ModuleAction("Agregar Usuario", target="auth/usuarios/agregar/", target_type=ActionTargetType.MODAL, icon="plus", classes=["positive"])
    ]
    detail_action = ItemAction(label="Detalles", target="auth/usuarios/${username}/", target_type=ActionTargetType.MODAL, icon="info circle", reference_fields=["username"])
    item_actions = [
        ItemAction(label="Modificar", target="auth/usuarios/${username}/modificar/", target_type=ActionTargetType.MODAL, icon="edit", reference_fields=["username"]),
        ItemAction(label="Mantto. Parámetrps", target="auth/usuarios/${username}/parametros/", target_type=ActionTargetType.MODAL, icon="cogs", reference_fields=["username"]),
        ItemAction(label="Establecer Contraseña", target="auth/usuarios/${username}/pwd/", target_type=ActionTargetType.MODAL, icon="key", reference_fields=["username"]),
        ItemAction(label="Habilitar/Deshabilitar", target="toggleUserStatus", target_type=ActionTargetType.FUNCTION, icon="user slash", reference_fields=["username", "is_active"], require_csrf=True)
    ]
    static_scripts = ["js/modules/users.js"]

    def get_queryset(self):
        users = []
        user_model = get_user_model()
        user_objects = user_model.objects.all()
        if not self.request.user.is_superuser:
            user_objects = user_objects.filter(is_superuser = False)
        for user in user_objects:
            groups = ", ".join([group.name for group in user.groups.all()])
            users.append({'pk': user.pk,'username': user.username,'first_name': user.first_name, 'last_name': user.last_name, 'is_superuser': user.is_superuser, 'groups': groups, 'is_active': user.is_active})
        return users

class UserDetailModalView(ModalView):
    template_name = "manager/auth/user_detail_modal.html"
    content_classes = ["image"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = kwargs.get("username", None)
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=username)
            self.name = f'Detalles de usuario "{user.username}"'
            context['name'] = self.name
            pps = UserProfilePicture.objects.filter(user=user)
            if pps.exists():
                context['profile_picture'] = pps.first().picture.url
        except user_model.DoesNotExist:
            user = None
            context["request_error"] = "No se encontró el usuario especificado"
        context["user"] = user
        return context

class UserFormModal(FormModalView):
    icon = "user"
    name = "Usuario"

    def get(self, request, *args, **kwargs):
        if "username" in kwargs:
            self.form_class = UserChangeForm
            self.form_action = urls.reverse('user_edit', kwargs=kwargs)
            user_model = get_user_model()
            try:
                user = user_model.objects.get(username=kwargs["username"])
                profile_picture = UserProfilePicture.objects.filter(user=user)
                self.name = f'Modificar usuario "{user.username}"'
                self.initForm(request, form_instance=user)
                if profile_picture.exists():
                    self._form.initial["profile_picture"] = profile_picture.first().picture
                request.session["modify_user_username"] = kwargs["username"]
            except user_model.DoesNotExist:
                self.request_error = "Los datos solicitados no existen."
                self.approve_action = None
        else:
            self.form_class = UserCreationForm
            self.form_action = urls.reverse('user_add')
            self.name = "Nuevo usuario"
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if "username" in kwargs:
            if not "modify_user_username" in request.session or kwargs["username"] != request.session.pop("modify_user_username"):
                return JsonResponse({"result": "warning", "message": "Operación no válida.", "close": "true"}, status=400)
            try:
                user_model = get_user_model()
                self._instance = user_model.objects.get(username=kwargs["username"])
                self.form_class = UserChangeForm
                self.form_action = urls.reverse('user_edit', kwargs=kwargs)
            except user_model.DoesNotExist:
                return JsonResponse({"result": "warning", "message": "El usuario especificado no existe.", "close": True}, status=400)
        else:
            self.form_class = UserCreationForm
            self.form_action = urls.reverse('user_add')
        return super().post(request, *args, **kwargs)
    
    def _processPostForm(self, request, *args, **kwargs):
        if self._instance:
            response_message = f'Usuario "{self._instance.username}" modificado con éxito'
        else:
            response_message = f'Usuario "{request.POST["username"]}" creado con éxito'
        try:
            user = self._form.save()
            if request.FILES and request.FILES["profile_picture"]:
                if hasattr(user, 'profile_picture'):
                    user_profile_picture = user.profilePicture
                else:
                    user_profile_picture = UserProfilePicture()
                    user_profile_picture.user = user
                user_profile_picture.picture = request.FILES["profile_picture"]
                user_profile_picture.save()
            elif hasattr(user, 'profile_picture'):
                user.profile_picture.delete()

            return JsonResponse({
                    "result": "success",
                    "message": response_message,
                    "close": True,
                    "refresh": urls.reverse('user_catalog'),
                },
                status=200
            )
        except Exception as ex:
            print(ex)
            return JsonResponse({"result": "error", "message": "Ocurrió un error al procesar la información; favor de intentar más tarde."}, status=500)

@require_POST
def toggleUserStatus(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            username = data['username']
            status = data['action']
        except KeyError:
            return JsonResponse({'result':'warning','message':'La solicitud no contiene la información correcta'}, status=400)
        try:
            user = get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            return JsonResponse({'result':'warning','message':'Usuario no encontrado'}, status=404)
        if user.is_superuser and not request.user.is_superuser:
            return JsonResponse({'result':'warning','message':'No tiene los permisos necesarios para modificar este usuario'}, status=403)
        try:
            user.is_active = status
            user.save()
            return JsonResponse({'result':'success','message':f'Usuario "{user.username}" {"habilitado" if status else "deshabilitado"} con éxito.'}, status=200)
        except Exception as ex:
            print(ex)
            return JsonResponse({'result':'error','message':'Ocurrió un error al modificar el usuario, intente de nuevo más tarde.'}, status=500)
    return HttpResponse("Ok", status=200)

class RSAKeyCatalog(CatalogView):
    module_code = 'rsakeycatalog'
    icon = "fingerprint"
    model = RSAKey
    static_scripts = ["js/modules/rsakey.js","js/components/file_dragdrop.js"]
    item_fields = [
        ItemField(reference_field='kid', label="Clave")
    ]
    actions = [
        ModuleAction(
            label="Generar Llave", 
            target="generateKey", 
            target_type=ActionTargetType.FUNCTION,
            icon="cogs",
            classes=["primary"],
            permissions=["oidc_provider.add_rsakey"],
            children=[
                ModuleAction(
                    label="Subir Archivo",
                    target="oidc/proveedor/rsa/subir/",
                    target_type=ActionTargetType.MODAL,
                    icon="upload",
                ),
                ModuleAction(
                    label="Capturar Manual",
                    target="oidc/proveedor/rsa/capturar/",
                    target_type=ActionTargetType.MODAL,
                    icon="edit",
                ),
            ]),
    ]
    item_actions = [
        ItemAction(
            label="Descargar",
            target="downloadKey",
            target_type=ActionTargetType.FUNCTION,
            icon="download",
            classes=["primary"],
            reference_fields=["pk"],
        ),
        ItemAction(
            label="Editar",
            target="oidc/proveedor/rsa/${pk}/",
            target_type=ActionTargetType.MODAL,
            icon="edit",
            classes=["primary"],
            reference_fields=["pk"],
        ),
        ItemAction(
            label="Eliminar",
            target="deleteKey",
            target_type=ActionTargetType.FUNCTION,
            icon="trash",
            classes=["negative"],
            reference_fields=["pk"],
        )
    ]
    is_exportable = False

def get_public_key(private_key):
    if not private_key:
        return None
    pk = RSA.importKey(private_key.key).publickey()
    return pk.export_key()

class RsaKeyModalView(ModalView):
    icon = "fingerprint"
    name = "Llave RSA"
    approve_action = ModuleAction(label="Guardar", target="saveKey", target_type=ActionTargetType.FUNCTION, icon="save", classes=["positive"])
    deny_action = ModuleAction(label="Regresar", icon="reply", classes=["negative"], target=None, target_type=None)
    template_name = "manager/rsakey_modal_form.html"
    form = RsaKeyForm
    _private_key = None

    def get(self, request, *args, **kwargs):
        if kwargs and "pk" in kwargs:
            try:
                self._private_key = RSAKey.objects.get(pk=kwargs["pk"])
                public_key = get_public_key(self._private_key)
                self.form = RsaKeyForm(data={
                    "key": self._private_key.key,
                    "public_key": public_key.decode(),
                    "kid": self._private_key.kid,
                })
            except RSAKey.DoesNotExist:
                self.request_error = "La llave privadad especificada no existe"
                self.form = RsaKeyForm()
                self.approve_action = None
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context

def rsaDownloadPem(request, pk):
    try:
        key = RSAKey.objects.get(pk=pk)
        response = HttpResponse(content_type = 'application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{key.kid}.pem"'
        response.content = get_public_key(key)
        return response
    except RSAKey.DoesNotExist:
        return JsonResponse({"response": "warning", "result": "La llave privada especificada no existe"}, status=404)
    except Exception as ex:
        print(ex)
        return JsonResponse({"response": "error", "result": "Ocurrió un error al procesar la solicitud"}, status=500)

class RsaKeyUploadModal(ModalView):
    form = None
    icon = "fingerprint"
    name = "Llave RSA"
    closable = False
    deny_action = ModuleAction(label="Regresar", icon="reply", classes=["negative"], target=None, target_type=None)
    template_name = "manager/rsakey_modal_form.html"

    def get(self, request, *args, **kwargs):
        self.form = RsaKeyUploadForm()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context

CLIENT_TYPE_CHOICES = [
    ("confidential", "Interno"),
    ("public", "Externo"),
]

class ClientCatalog(CatalogView):
    model = Client
    module_code = "clientcatalog"
    icon = "window restore"
    name = "Aplicaciones Cliente"
    is_exportable = False
    static_scripts = ["js/components/modal.js"]
    item_fields = [
        ItemField("name", label="Nombre"),
        ItemField("client_id", label="Clave"),
        ItemField("client_type", label="Tipo", choices=CLIENT_TYPE_CHOICES),
        ItemField("website_url", label="")
    ]
    actions = [
        ModuleAction(label="Nuevo Cliente", target="oidc/proveedor/clientes/agregar/", target_type=ActionTargetType.MODAL, icon="plus", classes=["primary"], permissions="oidc_provider.add_client")
    ]
    item_actions = [
        ItemAction(
            "Modificar", 
            target="oidc/proveedor/clientes/${pk}/modificar/", 
            target_type=ActionTargetType.MODAL, 
            icon="edit", 
            classes=["primary"], 
            reference_fields=["pk"]
        ),
        ItemAction(
            label="Eliminar",
            target="deleteKey",
            target_type=ActionTargetType.FUNCTION,
            icon="trash",
            classes=["negative"],
            reference_fields=["pk"],
        )
    ]

class ClientFormModal(FormModalView):
    icon = "window restore"
    name = "Aplicación Cliente"
    form_class = ClientForm

    def get(self, request, *args, **kwargs):
        if "pk" in kwargs:
            self.form_action = urls.reverse('client_edit', kwargs=kwargs)
            try:
                client = Client.objects.get(pk=kwargs["pk"])
                self.name = client.name
                self.initForm(request, form_instance=client)
                request.session[f"{str_as_id(self.name)}_client_id"] = kwargs["pk"]
            except Client.DoesNotExist:
                self.request_error = "Los datos solicitados no existen."
                self.approve_action = None
        else:
            self.form_action = urls.reverse('client_add')
        return super().get(request, *args, **kwargs)

    def _processPostForm(self, request, *args, **kwargs):
        if "pk" in kwargs:
            if not f"{str_as_id(self.name)}_client_id" in request.session or kwargs["pk"] != request.session.pop(f"{str_as_id(self.name)}_client_id"):
                return JsonResponse({"result": "warning", "message": "Operación no válida.", "close": "true"}, status=400)
            try:
                client = Client.objects.get(pk=kwargs["pk"])
                response_message = f'Aplicación {self._form.cleaned_data["name"]} modificada con éxito'
                self.form_action = urls.reverse('client_edit', kwargs=kwargs)
            except Client.DoesNotExist:
                return JsonResponse({"result": "warning", "message": "La aplicación cliente especificada no existe."}, status=400)
        else:
            client = Client()
            response_message = f'Aplicación {request.POST["name"]} creada con éxito'
            client.secret = sha224(uuid4().hex.encode()).hexdigest()
            self.form_action = urls.reverse('client_add')
        try:
            form_data = self._form.cleaned_data
            client.name = form_data["name"]
            if self.request.user and self.request.user.is_authenticated:
                client.owner = self.request.user
            client.client_type = form_data["client_type"]
            client.client_id = form_data["client_id"]
            client.website_url = form_data["website_url"]
            client.terms_url = form_data["terms_url"]
            client.contact_email = form_data["contact_email"]
            if request.FILES and request.FILES["logo"]:
                client.logo = request.FILES["logo"]
            client.redirect_uris = form_data["redirect_uris"]
            client.post_logout_redirect_uris = form_data["post_logout_redirect_uris"]
            client.scope = form_data["scope"]

            client.jwt_alg = "RS256"
            client.reuse_consent = False
            client.require_consent = True
            client.save()
            client.response_types.set(ResponseType.objects.filter(pk__in = [1,2,3]))

            return JsonResponse({
                    "result": "success",
                    "message": response_message,
                    "close": True,
                    "refresh": urls.reverse('client_catalog'),
                },
                status=200
            )
        except Exception as ex:
            print(ex)
            return JsonResponse({"result": "error", "message": "Ocurrió un error al procesar la información; favor de intentar más tarde."}, status=500)

class GroupCatalog(CatalogView):
    model = Group
    module_code = "groupcatalog"
    icon = "group"
    name = "Grupos de Usuarios"
    is_exportable = False
    static_scripts = ['js/components/multioption.js']
    item_fields = [
        ItemField("name", label="Nombre"),
        ItemField("clients", label="Aplicaciones Cliente"),
    ]
    actions = [
        ModuleAction(label="Nuevo Grupo", target="auth/grupos/agregar/", target_type=ActionTargetType.MODAL, icon="plus", classes=["primary"], permissions="auth.add_group")
    ]
    item_actions = [
        ItemAction(
            "Modificar", 
            target="auth/grupos/${pk}/modificar/", 
            target_type=ActionTargetType.MODAL, 
            icon="edit", 
            classes=["primary"], 
            reference_fields=["pk"]
        ),
        ItemAction(
            label="Eliminar",
            target="deleteKey",
            target_type=ActionTargetType.FUNCTION,
            icon="trash",
            classes=["negative"],
            reference_fields=["pk"],
        )
    ]
    def get_queryset(self):
        qs = []
        for group in Group.objects.all():
            clients = GroupClient.get_client_names_by_group(group)
            qs.append({"pk": group.pk, "name": group.name, "clients": ', '.join(clients)})
        return qs

class GroupFormModal(FormModalView):
    icon = "group"
    name = "Grupo de Usuarios"
    form_class = GroupForm
    template_name = 'manager/auth/group_modal_form.html'
    closable = False

    def get(self, request, *args, **kwargs):
        if "pk" in kwargs:
            self.form_action = urls.reverse('group_edit', kwargs=kwargs)
            try:
                group = Group.objects.get(pk=kwargs["pk"])
                self.name = f'Modificar Grupo "{group.name}"'
                data = {
                    "name": group.name,
                    "permissions": group.permissions.all(),
                    "clients": GroupClient.objects.filter(group=group)
                }
                self.initForm(request, data)
                request.session[f"{str_as_id(self.name)}_group_id"] = kwargs["pk"]
            except Group.DoesNotExist:
                self.request_error = "Los datos solicitados no existen."
                self.approve_action = None
        else:
            self.form_action = urls.reverse('group_add')
            self.name = "Nuevo Grupo de Usuarios"
        return super().get(request, *args, **kwargs)

    def _processPostForm(self, request, *args, **kwargs):
        if "pk" in kwargs:
            if not f"{str_as_id(self.name)}_client_id" in request.session or kwargs["pk"] != request.session.pop(f"{str_as_id(self.name)}_client_id"):
                return JsonResponse({"result": "warning", "message": "Operación no válida.", "close": "true"}, status=400)
            self.form_action = urls.reverse('group_edit', kwargs=kwargs)
            try:
                group = Group.objects.get(pk=kwargs["pk"])
                response_message = f'Grupo "{group.name}" modificado con éxito'
            except Group.DoesNotExist:
                self.request_error = "Los datos solicitados no existen."
                self.approve_action = None
                return super().get(request, *args, **kwargs)
        else:
            group = Group()
            response_message = f'Grupo "{self._form.cleaned_data["name"]}" creado con éxito'
        group.name = self._form.cleaned_data["name"]
        group.save()
        group.permissions.set(self._form.cleaned_data["permissions"])
        GroupClient.objects.filter(group=group).delete()
        group_clients = []
        for client in self._form.cleaned_data["clients"]:
            group_clients.append(GroupClient(group=group, client=client))
        GroupClient.objects.bulk_create(group_clients)
                
        return JsonResponse({
                "result": "success",
                "message": response_message,
                "close": True,
                "refresh": urls.reverse('group_catalog'),
            },
            status=200
        )

class UserClaimsManager(ModalView):
    module_code = "user_claims_manager"
    template_name = "manager/user_claim_manager.html"
    user = None
    claim_forms = {}
    claims = []
    icon = 'cogs'

    def get(self, request, *args, **kwargs):
        self.claim_forms = {}
        self.claims = []
        self.user = get_user_model().objects.get(username=kwargs["username"])
        self.name = f'Modificar parámetros de usuario "{self.user.username}"'
        for claim in Claim.objects.all():
            self.claims.append(claim)
            if ClaimCatalog.objects.filter(claim=claim).exists():
                self.claim_forms[claim.code] = ClaimCatalogForm(claim, self.user)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.user
        profile_picture = UserProfilePicture.objects.filter(user=self.user)
        if profile_picture.exists():
            context["profile_picture"] = profile_picture.first().picture.url
        context["claims"] = {}
        for claim in [claim for claim in self.claims if claim.code in self.claim_forms]:
            context["claims"][claim.code] = {"description": claim.description, "form": self.claim_forms[claim.code]}
        return context

class SetPasswordFormModal(FormModalView):
    icon = "user lock"
    name = "Establecer contraseña"
    form_class = SetPasswordForm
    user = None
    template_name = "manager/auth/user_password_set.html"

    def get(self, request, *args, **kwargs):
        username = kwargs["username"]
        try:
            self.user = get_user_model().objects.get(username=username)
            self.form_action = urls.reverse('user_set_pwd', kwargs=kwargs)
            request.session[f"{str_as_id(self.name)}_username"] = kwargs["username"]
            self.name = f'Establecer contraseña para el usuario: {self.user.username}'
        except get_user_model().DoesNotExist:
            self.request_error = 'Los datos solicitados no existen.'
            self.approve_action = None
        self._form = self.form_class(self.user)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.user or get_user_model().objects.get(username=kwargs["username"])
        return context

    def post(self, request, *args, **kwargs):
        self.form_action = urls.reverse('user_set_pwd', kwargs=kwargs)
        try:
            self.user = get_user_model().objects.get(username=kwargs['username'])
        except get_user_model().DoesNotExist:
            context = self.get_context_data(kwargs)
            return self.render_to_response(context)
        return super().post(request, *args, **kwargs)
    
    def initForm(self, request, form_data=None, form_instance=None, *args, **kwargs):
        if form_data:
            self._form = self.form_class(user=self.user, data=form_data)
        elif form_instance:
            self._form = self.form_class(user=self.user, instance=form_instance)
        else:
            self._form = self.form_class(user=self.user)
    
    def _processPostForm(self, request, *args, **kwargs):
        if not f"{str_as_id(self.name)}_username" in request.session or kwargs["username"] != request.session.pop(f"{str_as_id(self.name)}_username"):
            return JsonResponse({"result": "warning", "message": "Operación no válida.", "close": "true"}, status=400)
        self.form_action = urls.reverse('user_set_pwd', kwargs=kwargs)
        try:
            self.user = get_user_model().objects.get(username=kwargs["username"])
            response_message = f'La contraseña del usuario "{self.user.username}" se estableció con éxito'
        except get_user_model().DoesNotExist:
            return self.get(request, *args, **kwargs)
        try:
            self._form.save()
            return JsonResponse({
                    "result": "success",
                    "message": response_message,
                    "close": True,
                    "refresh": urls.reverse('user_catalog'),
                },
                status=200
            )
        except Exception as ex:
            print(ex)
            return JsonResponse({
                    "result": "error",
                    "message": "Ocurrió un error al procesar la solicitud",
                    "close": True
                },
                status=200
            )