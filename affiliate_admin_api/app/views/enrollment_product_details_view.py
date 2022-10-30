from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from campuslibs.shared_utils.data_decorators import ViewDataMixin
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from shared_models.models import Store, Product
from campuslibs.enrollment.common import Common


class EnrollmentProductDetailsView(APIView, SharedMixin, ViewDataMixin):
    http_method_names = ["head", "post"]

    def post(self, request, *args, **kwargs):
        product_ids = request.data.get('product_ids', None)
        store_id = request.data.get('store', '')

        try:
            store = Store.objects.get(pk=store_id)
        except Store.DoesNotExist:
            return Response(
                {
                    "error": {"message": "Store does not exists"},
                    "status_code": 404,
                },
                status=HTTP_404_NOT_FOUND,
            )

        products = None
        try:
            products = Product.objects.filter(id__in=product_ids, active_status=True)
        except Exception as e:
            pass

        common = Common()
        data = common.enrollment_products_extra_info(store, products)

        return Response(self.object_decorator(data), status=HTTP_200_OK)
