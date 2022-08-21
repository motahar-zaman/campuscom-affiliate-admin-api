from rest_framework.response import Response
from rest_framework import viewsets

from shared_models.models import Profile, ProfileStore, StudentProfile

from rest_framework.status import HTTP_200_OK


from campuslibs.shared_utils.data_decorators import ViewDataMixin
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin

from app.serializers import (
    ProfileSerializer,
    ProfileCommunicationMediumSerializer,
    ProfileLinkSerializer,
    ProfilePreferenceSerializer,
    ProfileEnrollmentSerializer,
)


class StudentViewSet(viewsets.ModelViewSet, PaginatorMixin, SharedMixin, ViewDataMixin):
    model = Profile
    serializer_class = ProfileSerializer
    http_method_names = ["get", "head"]

    def get_queryset(self):
        fields = self.request.GET.copy()
        try:
            fields.pop("limit")
        except KeyError:
            pass
        try:
            fields.pop("page")
        except KeyError:
            pass
        try:
            fields.pop("store")
        except KeyError:
            pass

        return self.model.objects.filter(**fields.dict())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer_profile_communication_mediums = ProfileCommunicationMediumSerializer(
            instance.profile_communication_mediums.all(),
            many=True,
            context={"request": request},
        ).data
        serializer_profile_links = ProfileLinkSerializer(
            instance.profile_links.all(), many=True, context={"request": request}
        ).data
        serializer_profile_preferences = ProfilePreferenceSerializer(
            instance.profile_preferences.all(), many=True, context={"request": request}
        ).data
        serializer_enrollments = ProfileEnrollmentSerializer(
            instance.enrollments.all(), many=True, context={"request": request}
        ).data

        serializer = ProfileSerializer(instance, context={"request": request}).data

        serializer[
            "profile_communication_mediums"
        ] = serializer_profile_communication_mediums
        serializer["profile_links"] = serializer_profile_links
        serializer["profile_preferences"] = serializer_profile_preferences
        serializer["enrollments"] = serializer_enrollments

        return Response(self.object_decorator(serializer), status=HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        # issues:
        # 1. what happends if user does not have store in db context
        # 2. what happends if a user is enrolled in multiple stores, stores those are in db context. probably there are some more issues.
        fields = self.request.GET.copy()

        admin_stores = request.user.db_context.get('Store', [])  # list of store ids of login admin
        profiles = self.get_queryset()
        student_profile = StudentProfile.objects.all()
        profiles = profiles.filter(id__in=student_profile.values('profile'))

        if not request.user.is_superuser and not request.user.is_scope_disabled:
            profile_stores = ProfileStore.objects.filter(store__id__in=admin_stores)
            profiles = profiles.filter(id__in=profile_stores.values('profile'))

        if 'store' in fields:
            profile_stores = ProfileStore.objects.filter(store__id=fields['store'])
            profiles = profiles.filter(id__in=profile_stores.values('profile'))


        serializer = ProfileSerializer(profiles, many=True)

        return Response(self.paginate(serializer.data), status=HTTP_200_OK)
