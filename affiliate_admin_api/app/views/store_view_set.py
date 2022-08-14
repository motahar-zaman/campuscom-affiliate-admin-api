from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin

from rest_framework.response import Response
from rest_framework import viewsets

from shared_models.models import Store

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
)

from app.serializers import GetStoreSerializer


class StoreViewSet(viewsets.ModelViewSet, PaginatorMixin, SharedMixin):
    model = Store
    serializer_class = GetStoreSerializer
    http_method_names = ["get", "head"]

    def get_queryset(self):
        fields = self.request.GET.copy()
        try:
            fields.pop("limit")
            fields.pop("page")
        except KeyError:
            pass

        return self.model.objects.filter(**fields.dict())

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user_scopes = self.get_user_scope()

        # getting only those stores which are allowed by current users scope
        if 'store' in user_scopes:
            if user_scopes['store'] is None:
                pass
            else:
                queryset = queryset.filter(id__in=user_scopes['store'])
        else:
            queryset = queryset.none()

        serializer = GetStoreSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(self.paginate(serializer.data), status=HTTP_200_OK)
