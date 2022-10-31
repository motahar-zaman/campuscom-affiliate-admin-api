from rest_framework.views import APIView
from rest_framework.response import Response

from campuslibs.shared_utils.data_decorators import ViewDataMixin

from rest_framework.status import HTTP_200_OK
from campuslibs.enrollment.common import Common


class RemoveEnrollmentView(APIView, ViewDataMixin):
    http_method_names = ["head", "post"]

    def post(self, request, *args, **kwargs):
        enrollment_id = request.data.get('course_enrollment', None)
        remove = Common()
        status, message, status_code = remove.remove_course_enrollment(enrollment_id)

        if status:
            return Response({"message": message}, status=HTTP_200_OK)
        else:
            return Response(
                {
                    "error": {"message": message},
                    "status_code": 400,
                },
                status=status_code,
            )
