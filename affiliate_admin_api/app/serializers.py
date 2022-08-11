from rest_framework import serializers

from shared_models.models import (Store, StoreConfiguration, Product)


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
