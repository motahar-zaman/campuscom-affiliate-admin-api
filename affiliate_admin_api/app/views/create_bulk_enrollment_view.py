from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from campuslibs.shared_utils.data_decorators import ViewDataMixin
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin
from rest_framework.views import APIView
from rest_framework.response import Response

from shared_models.models import Store, Profile, ProfileStore
import json

from campuslibs.enrollment.common import Common


class CreateBulkEnrollmentView(APIView, SharedMixin, ViewDataMixin):
    http_method_names = ["head", "post"]

    def post(self, request, *args, **kwargs):
        enroll = Common()

        # special cases:
        # 1. organization data will not provide as purchasing_for in purchaser_info, it will always be company and the
        # company will be from user context
        # 2. purchaser will be logged-in user or in purchaser_info

        status, message, data = enroll.validate_and_format_bulk_enrollment_payload(request)
        if not status:
            return Response({'message': message}, status=HTTP_400_BAD_REQUEST)

        data['admin'] = True
        status, message, processed_data = enroll.create_enrollment(data)

        if not status:
            product = {
                'id': processed_data.id,
                'title': processed_data.title
            }
            return Response({'message': message, 'product': product}, status=HTTP_400_BAD_REQUEST)

        else:
            discount = processed_data.pop('data')
            processed_data.pop('date_time')
            processed_data.update(discount)

        return Response(self.object_decorator(processed_data), status=HTTP_200_OK)
