from datetime import datetime, timedelta
from io import BytesIO
from openpyxl import load_workbook
from campuslibs.shared_utils.data_decorators import ViewDataMixin
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin
from rest_framework.response import Response
from rest_framework import viewsets

from shared_models.models import ImportTask

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST
)

from app.serializers import ImportTaskSerializer, CreateImportTaskSerializer

from django_scopes import scopes_disabled

from campuslibs.enrollment.tasks import Tasks


class ImportTaskViewSet(viewsets.ModelViewSet, PaginatorMixin, SharedMixin, ViewDataMixin):
    model = ImportTask
    serializer_class = ImportTaskSerializer
    http_method_names = ["get", "head", "post"]
    tasks = Tasks()

    def get_queryset(self):
        fields = self.request.GET.copy()

        if 'created_at__lte' in fields.keys():
            to_date = datetime.strptime(fields['created_at__lte'], "%Y-%m-%d")
            to_date = to_date + timedelta(days=1)
            fields['created_at__lte'] = to_date.strftime("%Y-%m-%d")

        try:
            fields.pop("limit")
            fields.pop("page")
        except KeyError:
            pass

        return self.model.objects.filter(**fields.dict())

    def list(self, request, *args, **kwargs):
        with scopes_disabled():
            queryset = self.get_queryset()

            # getting only those stores import_tasks which are allowed by current users scope
            user_scopes = self.get_user_scope()
            if 'store' in user_scopes:
                if user_scopes['store'] is None:
                    pass
                else:
                    queryset = queryset.filter(store__in=user_scopes['store'])
            else:
                queryset = queryset.none()

        import_task_serializer = self.get_serializer(queryset, many=True)
        return Response(self.paginate(import_task_serializer.data), status=HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        headers = []
        data = request.data.dict()
        data['status'] = ImportTask.STATUS_IN_PROGRESS
        import_task_serializer = CreateImportTaskSerializer(data=data)
        with scopes_disabled():
            import_task_serializer.is_valid(raise_exception=True)
            obj = import_task_serializer.save()

        wb = load_workbook(filename=BytesIO(obj.filename.read()))

        try:
            worksheet = wb[obj.import_type]
        except KeyError:
            return Response(
                {
                    'error': {'message': f'Spreadsheet file does not have a sheet called {obj.import_type}'},
                    'status_code': 400
                },
                status=HTTP_400_BAD_REQUEST
            )

        if obj.import_type == 'contact':
            headers = [
                'first_name', 'last_name', 'primary_email', 'date_of_birth', 'primary_contact_number'
            ]
            routing_key = 'profile_postgres.import'

        row1 = worksheet[1]
        if not set(headers) == set([cell.value.strip() for cell in row1]):
            obj.delete()
            return Response(
                {
                    'error': {'message': 'Incorrect headers in worksheet'},
                    'status_code': 400
                },
                status=HTTP_400_BAD_REQUEST
            )

        self.tasks.generic_task_enqueue(routing_key, import_task_id=str(obj.id))
        return Response(self.object_decorator(import_task_serializer.data), status=HTTP_201_CREATED)
