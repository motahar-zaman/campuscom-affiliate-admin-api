from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK,  HTTP_400_BAD_REQUEST

from campuslibs.enrollment.common import Common
from campuslibs.shared_utils.data_decorators import ViewDataMixin
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin


class PaymentSummaryView(APIView, SharedMixin, ViewDataMixin):
    http_method_names = ["head", "post"]

    def post(self, request, *args, **kwargs):
        summary = Common()
        status, message, data = summary.payment_summary(request)
        if not status:
            return Response(
                {
                    "error": message,
                    "status_code": 400,
                },
                status= HTTP_400_BAD_REQUEST,
            )
        return Response(self.object_decorator(data), status=HTTP_200_OK)
