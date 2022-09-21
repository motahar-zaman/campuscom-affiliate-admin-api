from app.serializers import ProductSerializer
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin
from rest_framework import viewsets
from rest_framework.response import Response
from shared_models.models import Product, Store, RelatedProduct, DiscountRule, DiscountProgram
from campuslibs.shared_utils.data_decorators import ViewDataMixin
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST
)


class ProductViewSet(viewsets.ModelViewSet, PaginatorMixin, ViewDataMixin, SharedMixin):
    model = Product
    serializer_class = ProductSerializer
    http_method_names = ["get", "head"]

    def get_queryset(self):
        fields = self.request.GET.copy()
        fields["active_status"] = True
        try:
            fields.pop("limit")
            fields.pop("page")
        except KeyError:
            pass

        queryset = self.model.objects.filter(**fields.dict())
        scopes = self.get_user_scope()
        if 'store' in scopes and scopes['store']:
            queryset = queryset.filter(store__id__in=scopes['store'])

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)

        return Response(self.paginate(serializer.data), status=HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        product = self.get_object()
        product_serializer = self.get_serializer(product)
        return Response(self.object_decorator(product_serializer.data))
