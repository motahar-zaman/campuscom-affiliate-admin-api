from rest_framework.response import Response
from rest_framework import viewsets
from campuslibs.shared_utils.data_decorators import ViewDataMixin
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin
from shared_models.models import Profile
from app.serializers import ProfileSerializer

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST
)


class ContactViewSet(viewsets.ModelViewSet, PaginatorMixin, ViewDataMixin, SharedMixin):
    model = Profile
    serializer_class = ProfileSerializer
    http_method_names = ["get", "head"]

    def get_queryset(self):
        fields = self.request.GET.copy()

        try:
            fields.pop("limit")
            fields.pop("page")
        except KeyError:
            pass

        queryset = self.model.objects.filter(**fields.dict())
        scopes = self.get_user_scope()
        if 'store' in scopes and scopes['store']:
            queryset = queryset.filter(profile_stores__store__in=scopes['store'])

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        contact_serializer = self.get_serializer(queryset, many=True)
        return Response(self.paginate(contact_serializer.data), status=HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        contact = self.get_object()
        contact_serializer = self.get_serializer(contact)
        return Response(self.object_decorator(contact_serializer.data))
