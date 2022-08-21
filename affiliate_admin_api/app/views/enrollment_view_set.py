from campuslibs.shared_utils.data_decorators import ViewDataMixin
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin

from rest_framework.response import Response
from rest_framework import viewsets

from shared_models.models import (
    CourseEnrollment,
)

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND
)

from app.serializers import EnrollmentSerializer


class CourseEnrollmentViewSet(viewsets.ModelViewSet, PaginatorMixin, SharedMixin, ViewDataMixin):
    model = CourseEnrollment
    serializer_class = EnrollmentSerializer
    http_method_names = ["get", "head"]

    def get_queryset(self):
        fields = self.request.GET.copy()
        try:
            fields.pop("limit")
            fields.pop("page")
        except KeyError:
            pass
        return self.model.objects.filter(**fields.dict())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = EnrollmentSerializer(instance, context={"request": request})
        return Response(self.object_decorator(serializer.data), status=HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        db_context = self.get_user_scope()

        try:
            store_ids = db_context["store"]
        except KeyError:
            return Response(self.object_decorator({}), status=HTTP_404_NOT_FOUND)

        enrollments = self.get_queryset()

        if not request.user.is_superuser and not self.request.user.is_scope_disabled:  # platform admin gets all the students, regardless of db_context
            enrollments = enrollments.filter(store__id__in=store_ids)

        serializer = EnrollmentSerializer(enrollments, many=True, context={"request": request})
        return Response(self.paginate(serializer.data), status=HTTP_200_OK)
