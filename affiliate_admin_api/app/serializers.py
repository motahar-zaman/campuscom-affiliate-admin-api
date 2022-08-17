from rest_framework import serializers

from shared_models.models import (Store, StoreConfiguration, Product, Profile, ImportTask, CourseProvider, Permission, CustomRole)


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