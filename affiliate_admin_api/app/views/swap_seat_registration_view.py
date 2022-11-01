from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from campuslibs.shared_utils.shared_function import SharedMixin
from campuslibs.shared_utils.data_decorators import ViewDataMixin
from rest_framework.views import APIView
from rest_framework.response import Response

from campuslibs.enrollment.common import Common


class SwapSeatRegistrationView(APIView, SharedMixin, ViewDataMixin):
    http_method_names = ["head", "post"]

    def post(self, request, *args, **kwargs):
        seat_reservation_id = request.data.get('seat_reservation', None)
        enroll = Common()

        status, message, data = enroll.validate_and_format_enrollment_payload(request, swap=True)
        if not status:
            return Response(
                {
                    "error": {'message': message},
                    "status_code": 400,
                },
                status=HTTP_400_BAD_REQUEST,
            )

        # remove previous registration from the seat
        status, message, status_code = enroll.remove_seat_registration(seat_reservation_id)
        if not status:
            return Response(
                {
                    "error": {'message': message},
                    "status_code": 400,
                },
                status=HTTP_400_BAD_REQUEST,
            )

        # add/create new enrollment for the seat
        data['admin'] = True
        status, message, processed_data = enroll.create_enrollment(data)

        if not status:
            product = {
                'id': processed_data.id,
                'title': processed_data.title
            }
            return Response(
                {
                    "error": {'message': message, 'product': product},
                    "status_code": 400,
                },
                status=HTTP_400_BAD_REQUEST,
            )
        else:
            discount = processed_data.pop('data')
            processed_data.pop('date_time')
            processed_data.update(discount)

        return Response(self.object_decorator(processed_data), status=HTTP_200_OK)
