from shared_models.models import (StoreFeaturedCareer, StorePaymentGateway, StoreIdentityProvider,
                                  Section, CourseProvider)
from models.courseprovider.course_provider import CourseProvider as CourseProviderModel
from models.occupation.occupation import Occupation as OccupationModel
from shared_models.models import CourseSharingContract
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from datetime import datetime
from decouple import config
import pytz
import boto3
import uuid
import mimetypes

from django_scopes import scopes_disabled, scope
from inflection import underscore

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings


class SharedMixin(object):
    def get_user_scope(self, user=None, include_contracts=True):
        """
        If user is provided, return the scope of that user. If not provided, try to return the scope of current authenticated user.

        If the context has a store, the sharing contracts with these stores are gathered. Then the course provider in those contracts are included in the scope.
        """

        if user is None:
            user = self.request.user

        if user.is_authenticated:
            if user.is_superuser or user.is_scope_disabled:
                return {'store': None, 'course_provider': None}

            context = {}
            for key, value in user.db_context.items():
                context[underscore(key)] = value.copy()

            # a scenario: suppose a context only has store. that user will not have any access to courses. because courses belong to
            # course providers. in this case, one solution is to provide the course provider as the user context. but since
            # front-end is implemented such that context can not be multiple at this time, so another solution is needed:
            # here, we check if the store inside the context has a contract with any course provider. if found, we add those course
            # provider to the context. this is going to be expensive performance-wise, but what else is possible.

            if include_contracts:
                contracts = CourseSharingContract.objects.none()

                if 'store' in context:
                    contracts = CourseSharingContract.objects.filter(store__id__in=context['store'])

                if contracts.exists():
                    if 'course_provider' in context:
                        course_provider_ids = [str(contract.course_provider.id) for contract in contracts if str(contract.course_provider.id) not in context['course_provider']]
                        context['course_provider'].extend(course_provider_ids)
                    else:
                        context['course_provider'] = [str(contract.course_provider.id) for contract in contracts]

            return context
        return {}

    def get_scoped_queryset(self, model=None, fields={}):
        """
        Returns the scoped queryset of the model provided. If no model is provided, defaults to self.model. If fields are provided, fitler is applied
        """
        if model is None:
            model = self.model

        with scope(**self.get_user_scope()):
            queryset = model.objects.filter(**fields.dict())

        return queryset

    def check_store_payment_gateway(self, request_data):
        with scopes_disabled():
            store_payment_gateway = StorePaymentGateway.objects.filter(
                payment_gateway_config__id=request_data['payment_gateway_config'],
                store__id=request_data['store'],
                payment_gateway__id=request_data['payment_gateway']
            )
        if store_payment_gateway.exists():
            raise serializers.ValidationError({'payment_gateway': 'This payment gateway already exists in your store.'})

    def check_store_identity_provider(self, request_data):
        with scopes_disabled():
            store_identity_providers = StoreIdentityProvider.objects.filter(store__id=request_data['store'], identity_provider__id=request_data['identity_provider'])
        if store_identity_providers.exists():
            raise serializers.ValidationError({'identity_provider': 'This identity provider already exists in your store.'})

    def rename_file(self, file_object, image_name):
        def getsize(f):
            f.seek(0)
            f.read()
            s = f.tell()
            f.seek(0)
            return s
        image_name = image_name.strip()
        content_type, charset = mimetypes.guess_type(image_name)
        size = getsize(file_object)
        new_file_name = str(uuid.uuid4()) + '.' + str(content_type).split('/')[-1]
        return InMemoryUploadedFile(file=file_object, name=new_file_name, field_name=None, content_type=content_type, charset=charset, size=size)

    def prepare_provider_data_for_filter(self, fields):
        provider = CourseProvider.objects.get(id=fields['provider__id'])
        course_provider_model = CourseProviderModel.objects.filter(id=provider.content_db_reference)
        fields['provider__in'] = [str(item.id) for item in course_provider_model]
        del fields['provider__id']
        return fields

    # def prepare_course_provider_site_and_instructor(self, data):
    #     if 'provider' in data and 'id' in data['provider']:
    #         try:
    #             provider = CourseProvider.objects.get(content_db_reference=data['provider']['id'])
    #         except CourseProvider.DoesNotExist:
    #             data['provider'] = {}
    #         else:
    #             data['provider'] = CourseProviderSerializer(provider).data
    #
    #     if 'image' in data and 'original' in data['image']:
    #         data['image'] = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/uploads/{data['image']['original']}"
    #     else:
    #         data['image'] = None
    #
    #     if 'profile_urls' in data and 'urls' in data['profile_urls']:
    #         data['profile_urls'] = data['profile_urls']['urls']
    #     else:
    #         data['profile_urls'] = None
    #
    #     return data

    def get_mongo_obj_or_404(self, model, id):
        try:
            return model.objects.get(id=id)
        except model.DoesNotExist:
            raise Http404

    def prepare_course_provider_data(self, request_data):
        if 'course_provider_logo_uri' in request_data and request_data['course_provider_logo_uri']:
            request_data['course_provider_logo_uri'] = self.rename_file(request_data['course_provider_logo_uri'], request_data['course_provider_logo_uri'].name)
            request_data['logo'] = {'original': request_data['course_provider_logo_uri'].name}
        return request_data

    def merge_course_provider_data(self, course_model_serializer, course_serializer):
        course_model_serializer['id'] = course_serializer['id']
        course_model_serializer['course_provider_logo_uri'] = course_serializer['course_provider_logo_uri']
        course_model_serializer['refund_email'] = course_serializer['refund_email']
        course_model_serializer['configuration'] = course_serializer['configuration']
        return course_model_serializer

    # def create_identity_providers(self, store, request_data):
    #     data = []
    #     store_identity_provider = {}
    #     ids = request_data.split(',')
    #     for identity_provider in ids:
    #         store_identity_provider['identity_provider'] = identity_provider
    #         store_identity_provider['store'] = store
    #         data.append(store_identity_provider)
    #         store_identity_provider = {}
    #
    #     serializer = StoreIdentityProviderSerializer(data=data, many=isinstance(data, list))
    #     serializer.is_valid(raise_exception=True)
    #     with scopes_disabled():
    #         StoreIdentityProvider.objects.filter(store__id=store).delete()
    #     self.perform_create(serializer)

    def get_occupation_model(self, id):
        data = {}
        try:
            career = OccupationModel.objects.get(id=id)
            data['soc_code'] = career.soc_code
            data['career_name'] = career.name
        except OccupationModel.DoesNotExist:
            data['soc_code'] = ''
            data['career_name'] = ''
        return data

    def tagged_careers_skills(self, request_data):
        data = []
        store_career = {}

        if 'careers' not in request_data:
            raise serializers.ValidationError({'careers': 'This field is required.'})

        if 'store' not in request_data:
            raise serializers.ValidationError({'store': 'This field is required.'})

        career_ids = request_data['careers'].split(',')
        with scopes_disabled():
            exists_careers_id = StoreFeaturedCareer.objects.filter(store__id=request_data['store']).values_list('content_db_reference', flat=True)
        career_ids = [career_id for career_id in career_ids if career_id not in exists_careers_id]

        for career_id in career_ids:
            career = self.get_occupation_model(career_id)
            store_career['content_db_reference'] = career_id
            store_career['store'] = request_data['store']
            store_career['soc_code'] = career['soc_code']
            store_career['career_name'] = career['career_name']
            data.append(store_career)
            store_career = {}
        return data

    @staticmethod
    def tagged_careers_skills_data_modify(course_model):
        data = {'careers': [{'id': str(item.id), 'name': str(item.name)} for item in course_model.careers],
                'skills': [{'id': str(item.id), 'name': str(item.name)} for item in course_model.skills]}
        return data

    # def create_store_payment_gateway(self, store, payment_gateways):
    #     data = []
    #     store_payment_gateway = {}
    #
    #     ids = payment_gateways.split(',')
    #     for item in ids:
    #         store_payment_gateway['payment_gateway'] = item
    #         # store_payment_gateway['payment_gateway_config'] = item['config']
    #         store_payment_gateway['store'] = store
    #         data.append(store_payment_gateway)
    #         store_payment_gateway = {}
    #
    #     serializer = StorePaymentGatewaySerializer(data=data, many=isinstance(data, list))
    #     serializer.is_valid(raise_exception=True)
    #     with scopes_disabled():
    #         StorePaymentGateway.objects.filter(store__id=store).delete()
    #     self.perform_create(serializer)

    def get_store_course_modify_data(self, request_data):
        data = []
        data_item = {}
        for item in request_data['data']:
            data_item['course'] = item['course_id']
            data_item['store'] = request_data['store_id']
            data_item['is_featured'] = item['is_featured']
            data.append(data_item)
            data_item = {}
        return data

    def get_instructor_modify_data(self, data):
        print(data)
        new_data = {}
        if 'image' in data and data['image']:
            new_data['image'] = self.image_upload_to_s3(data)

        if 'provider' in data and data['provider']:
            course_provider = get_object_or_404(CourseProvider, pk=data['provider'])
            new_data['provider'] = course_provider.content_db_reference

        if 'name' in data:
            new_data['name'] = data['name']

        if 'external_id' in data:
            new_data['external_id'] = data['external_id']

        if 'short_bio' in data:
            new_data['short_bio'] = data['short_bio']

        if 'detail_bio' in data:
            new_data['detail_bio'] = data['detail_bio']

        if 'profile_urls' in data and data['profile_urls']:
            new_data['profile_urls'] = {'urls': data['profile_urls'].split(',')}

        return new_data

    def image_upload_to_s3(self, request_data):
        image = request_data['image']
        session = boto3.Session(aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        s3 = session.resource('s3')
        content_type, charset = mimetypes.guess_type(image.name)
        new_file_name = str(uuid.uuid4()) + '.' + str(content_type).split('/')[-1]
        s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME).put_object(Key='uploads/%s' % new_file_name, Body=image, ContentType=content_type)
        return {'original': new_file_name}

    def filter_store_course_and_course(self, courses, store_courses):
        fields = self.request.GET.copy()

        store_course_fields = {}
        course_fields = {}

        if 'title' in fields:
            store_course_fields['course__title__icontains'] = fields['title']
            course_fields['title__icontains'] = fields['title']

        if 'store' in fields:
            store_course_fields['store'] = fields['store']

        if 'id' in fields:
            store_course_fields['id'] = fields['id']

        if 'course_provider' in fields:
            store_course_fields['course__course_provider'] = fields['course_provider']
            course_fields['course_provider'] = fields['course_provider']

        if 'active_status' in fields:
            store_course_fields['active_status'] = fields['active_status']
            course_fields['active_status'] = fields['active_status']

        if 'status' in fields:
            if fields['status'] == 'ready/available':
                store_courses = store_courses.none()
                course_fields['content_ready'] = True

            elif fields['status'] == 'published':
                courses = courses.none()
                store_course_fields['is_published'] = True

            elif fields['status'] == 'unpublished':
                courses = courses.none()
                store_course_fields['is_published'] = False

        courses = courses.filter(**course_fields)
        store_courses = store_courses.filter(**store_course_fields)

        return courses, store_courses

    def filter_store_certifcate_and_certifcate(self, certificates, store_certificates):
        fields = self.request.GET.copy()

        store_certificate_fields = {}
        certificate_fields = {}

        if 'title' in fields:
            store_certificate_fields['certificate__title__icontains'] = fields['title']
            certificate_fields['title__icontains'] = fields['title']

        if 'store' in fields:
            store_certificate_fields['store'] = fields['store']

        if 'id' in fields:
            store_certificate_fields['id'] = fields['id']

        if 'course_provider' in fields:
            store_certificate_fields['certificate__course_provider'] = fields['course_provider']
            certificate_fields['course_provider'] = fields['course_provider']

        if 'status' in fields:
            if fields['status'] == 'ready/available':
                store_certificates = store_certificates.none()
                certificate_fields['content_ready'] = True

            elif fields['status'] == 'published':
                certificates = certificates.none()
                store_certificate_fields['is_published'] = True

            elif fields['status'] == 'unpublished':
                certificates = certificates.none()
                store_certificate_fields['is_published'] = False

        certificates = certificates.filter(**certificate_fields)
        store_certificates = store_certificates.filter(**store_certificate_fields)

        return certificates, store_certificates


class PaginatorMixin(object):
    min_limit = 1
    max_limit = 2000

    def paginate(self, object_list, **kwargs):
        page = self.request.GET.get('page', 1)
        limit = self.request.GET.get('limit', 10)

        try:
            page = int(page)
            if page < 1:
                page = 1
        except (TypeError, ValueError):
            page = 1

        try:
            limit = int(limit)
            if limit < self.min_limit:
                limit = self.min_limit
            if limit > self.max_limit:
                limit = self.max_limit
        except (ValueError, TypeError):
            limit = self.max_limit

        paginator = Paginator(object_list, limit)
        try:
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)

        data = {'url': config('API_URL') + self.request.get_full_path(),
                'date_time': datetime.now().replace(tzinfo=pytz.utc), 'page': {
                'previous_page': objects.has_previous() and objects.previous_page_number() or None,
                'page': page,
                'next_page': objects.has_next() and objects.next_page_number() or None,
                'total': len(object_list),
                'limit': limit
            }, 'data': list(objects)}

        return data
