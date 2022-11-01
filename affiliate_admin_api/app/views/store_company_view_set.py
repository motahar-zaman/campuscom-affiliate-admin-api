from shared_models.models import StoreCompany
from rest_framework import viewsets
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin

from campuslibs.shared_utils.data_decorators import ViewDataMixin
from rest_framework.response import Response
from django.db import IntegrityError
from django_scopes import scopes_disabled

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED
)

from app.serializers import StoreCompanySerializer


class StoreCompanyViewSet(viewsets.ModelViewSet, ViewDataMixin, PaginatorMixin, SharedMixin):
    """
    A viewset for viewing and editing store company.
    """
    serializer_class = StoreCompanySerializer
    http_method_names = ["get", "head", "post", "patch", "update"]
    model = StoreCompany

    def get_queryset(self):
        fields = self.request.GET.copy()
        try:
            fields.pop("limit")
            fields.pop("page")
        except KeyError:
            pass

        return self.model.objects.filter(**fields.dict())

    def retrieve(self, request, *args, **kwargs):
        store_company = self.get_object()
        serializer = self.serializer_class(store_company)
        return Response(self.object_decorator(serializer.data))

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # getting only those stores companies which are allowed by current users scope
        user_scopes = self.get_user_scope()
        if 'store' in user_scopes:
            if user_scopes['store'] is None:
                pass
            else:
                queryset = queryset.filter(store__in=user_scopes['store'])
        else:
            queryset = queryset.none()
        serializer = self.serializer_class(queryset, many=True)

        return Response(self.paginate(serializer.data), status=HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        with scopes_disabled():
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                except IntegrityError:
                    return self.custom_error()

        return Response(self.object_decorator(serializer.data), status=HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        with scopes_disabled():
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                except IntegrityError:
                    return self.custom_error()

        return Response(self.object_decorator(serializer.data))
