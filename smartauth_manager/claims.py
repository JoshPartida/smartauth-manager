from oidc_provider.models import Client
from smartauth_provider.claims import SmartauthScopeClaims
from .models import GroupClient, Profile, Role, Permission

class ManagerScopeClaims(SmartauthScopeClaims):
    info_applications = (
        'Aplicaciones',
        'Aplicaciones registradas a las que el usuario tiene acceso.',
    )

    def scope_applications(self):
        dic = {}
        user_clients = list(GroupClient.objects.filter(group__in=self.user.groups).values_list('client__client_id', flat=True))
        if user_clients:
            dic = {'applications': [client_id for client_id in user_clients]}
        return dic

    info_permissions = (
        'Permisos',
        'Objetos de permisos que el usuario tiene asignados en las aplicaciones.'
    )

    def scope_permissions(self):
        dic = {}
        if 'applications' in self.scopes:
            user_clients = list(GroupClient.objects.filter(group__in=self.user.groups.all()).values_list('client__client_id', flat=True))
        else:
            user_clients = [self.client.client_id]
        for client_id in user_clients:
            try:
                permissions = Profile.objects.get(user=self.user, client__client_id=client_id).permissions
            except Profile.DoesNotExist:
                roles = Role.objects.filter(group__in=self.user.groups.all(), client__client_id=client_id)
                permissions = Permission.objects.filter(role__in=roles)
            if permissions:
                dic.update({client_id: [permission.code for permission in permissions]})
        return {'permissions':  dic}