from rest_framework.views import APIView
from rest_framework.response import Response

from campuslibs.enrollment.common import Common
from campuslibs.shared_utils.data_decorators import ViewDataMixin
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin


class PaymentSummaryView(APIView, SharedMixin, ViewDataMixin):
    http_method_names = ["head", "post"]

    def post(self, request, *args, **kwargs):
        summary = Common()
        status, message, data, status_code = summary.payment_summary(request)
        if not status:
            return Response(
                {
                    "error": message
                },
                status= status_code,
            )
        return Response(self.object_decorator(data), status=status_code)
