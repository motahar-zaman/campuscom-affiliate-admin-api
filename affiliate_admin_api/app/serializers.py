from rest_framework import serializers

from shared_models.models import (Store, StoreConfiguration, Product, Profile, ImportTask, CourseProvider, Permission,
                                  CustomRole, CourseEnrollment, Course, Section, CartItem, ProfileCommunicationMedium,
                                  ProfileLink, IdentityProvider, ProfilePreference)

from django_scopes import scopes_disabled


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'name', 'action', 'operation', 'group')


class CustomRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomRole
        fields = ('id', 'name', 'permissions', 'menu_permissions')


class GetStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name', 'url_slug', 'is_active', 'store_logo_uri', 'template')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class CartStoreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Store
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        store_configurations = StoreConfiguration.objects.filter(store=instance)
        data['configurations'] = []

        for store_config in store_configurations:
            config = {}

            config['entity_name'] = store_config.external_entity.entity_name
            config['entity_type'] = store_config.external_entity.entity_type
            config['config_value'] = store_config.config_value

            data['configurations'].append(config)

        return data


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id', 'store', 'external_id', 'product_type', 'title', 'content', 'image', 'limit_applicable',
            'total_quantity', 'quantity_sold', 'available_quantity', 'tax_code', 'fee', 'currency_code', 'ref_id',
            'minimum_fee', 'active_status'
        )
        depth = 1


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'first_name', 'last_name', 'date_of_birth', 'profile_picture_uri',
                  'primary_email', 'primary_contact_number', 'terms_accepted')


class ImportTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportTask
        fields = (
            'id', 'ref_id', 'course_provider', 'store', 'import_type', 'filename', 'status', 'status_message',
            'queue_processed'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        course_provider_id = instance.course_provider.id if instance.course_provider else None
        try:
            course_provider = CourseProvider.objects.get(pk=course_provider_id)
        except CourseProvider.DoesNotExist:
            pass
        else:
            data['course_provider'] = {'id': str(course_provider.id), 'name': course_provider.name}

        try:
            store = Store.objects.get(pk=instance.store.id if instance.store else None)
        except Store.DoesNotExist:
            pass
        else:
            data['store'] = {'id': str(store.id), 'name': store.name}
        return data


class CreateImportTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportTask
        fields = (
            'id', 'course_provider', 'store', 'import_type', 'filename', 'status', 'status_message', 'queue_processed'
        )


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = ('id', 'profile', 'course', 'section', 'enrollment_time', 'application_time',
                  'status', 'store', 'cart_item', 'expiry_date', 'ref_id')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['profile'] = ProfileSerializer(Profile.objects.get(id=data['profile'])).data
        with scopes_disabled():
            data['course'] = GetCourseDetailSerializer(Course.objects.get(id=data['course'])).data
            try:
                data['section'] = GetSectionSerializer(Section.objects.get(id=data['section'])).data
            except Section.DoesNotExist:
                data['section'] = None
            try:
                data['product_id'] = str(CartItem.objects.get(id=data['cart_item']).product.id)
            except CartItem.DoesNotExist:
                data['product_id'] = None

        data['store'] = GetStoreNameIdSerializer(Store.objects.get(id=data['store'])).data

        return data


class GetCourseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'title')


class GetSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ('id', 'course', 'name', 'fee', 'seat_capacity', 'available_seat',
                  'execution_mode', 'registration_deadline', 'content_db_reference', 'is_active', 'active_status')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        with scopes_disabled():
            data['course'] = GetCourseDetailSerializer(
                Course.objects.get(id=data['course'])).data
        return data


class GetStoreNameIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name')


class ProfileCommunicationMediumSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileCommunicationMedium
        fields = ('id', 'medium_type', 'medium_value')


class ProfileLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileLink
        fields = ('id', 'identity_provider', 'provider_profile_identity')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['identity_provider'] = ProfileIdentityProviderSerializer(
            IdentityProvider.objects.get(id=data['identity_provider'])).data
        data['name'] = data['identity_provider']['name']
        del data['identity_provider']
        return data


class ProfileIdentityProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityProvider
        fields = ('id', 'name', 'slug')


class ProfilePreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePreference
        fields = ('id', 'preference_type', 'preference_value')


class ProfileEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = (
            'id', 'profile', 'course', 'section', 'enrollment_time', 'application_time', 'status', 'expiry_date',\
            'ref_id'
        )