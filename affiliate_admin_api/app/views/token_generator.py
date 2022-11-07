from rest_framework import exceptions

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from shared_models.models import Store, CourseProvider

from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.settings import api_settings

from shared_models.models import Permission, CustomRole, StoreCompany
from app.serializers import CustomRoleSerializer, PermissionSerializer


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['email'] = user.email

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # validate app_permissions
        custom_roles = self.user.custom_roles
        if CustomRole.objects.filter(pk__in=custom_roles, app_permissions__contains=['AFFILIATE']).exists():
            pass
        else:
            raise exceptions.AuthenticationFailed(
                "User don't have permission on this application",
                'app_permission',
            )

        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['role'] = {}
        data['permissions'] = {}
        data['menu_permissions'] = {}
        data['context'] = []
        data['mfa_enabled'] = self.user.mfa_enabled

        custom_roles = CustomRole.objects.filter(id__in=self.user.custom_roles)
        custom_role_serializer = CustomRoleSerializer(custom_roles, many=True)
        data['custom_roles'] = custom_role_serializer.data

        permission_ids = []
        menu_permissions = []
        for role in custom_roles:
            permission_ids = permission_ids + role.permissions
            if role.menu_permissions is not None:
                menu_permissions = menu_permissions + role.menu_permissions
        permission_serializer = PermissionSerializer(Permission.objects.filter(id__in=permission_ids), many=True)
        data['permissions'] = permission_serializer.data
        data['menu_permissions'] = list(set(menu_permissions))
        data['is_superuser'] = self.user.is_superuser
        data['preferences'] = self.user.preference

        if self.user.db_context:
            if 'Store' in self.user.db_context.keys() and len(self.user.db_context['Store']):
                context = {
                    'type': 'Store',
                    'values': []
                }
                stores = self.user.db_context['Store']
                for store in stores:
                    try:
                        s = Store.objects.get(pk=store)
                    except Store.DoesNotExist:
                        pass
                    else:
                        if s.primary_course_provider:
                            primary_course_provider = {
                                "id": str(s.primary_course_provider.id),
                                "name": s.primary_course_provider.name
                            }
                        else:
                            primary_course_provider = None
                        context['values'].append({
                            "id": str(s.id),
                            "name": s.name,
                            "primary_course_provider": primary_course_provider
                        })
                data['context'].append(context)

            if 'CourseProvider' in self.user.db_context.keys() and len(self.user.db_context['CourseProvider']):
                context = {
                    'type': 'CourseProvider',
                    'values': []
                }

                course_providers = self.user.db_context['CourseProvider']
                for cp in course_providers:
                    try:
                        c = CourseProvider.objects.get(pk=cp)
                    except CourseProvider.DoesNotExist:
                        pass
                    else:
                        context['values'].append({
                            'id': str(c.id),
                            'name': c.name
                        })
                data['context'].append(context)

            if 'Company' in self.user.db_context.keys() and len(self.user.db_context['Company']):
                context = {
                    'type': 'Company',
                    'values': []
                }

                companies = self.user.db_context['Company']
                for cp in companies:
                    try:
                        c = StoreCompany.objects.get(pk=cp)
                    except CourseProvider.DoesNotExist:
                        pass
                    else:
                        context['values'].append({
                            'id': str(c.id),
                            'name': c.company_name,
                            'store': str(c.store.id)
                        })
                data['context'].append(context)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
