from django.contrib import admin
from django.urls import path, include
from rest_framework import routers


from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from app.views import MyTokenObtainPairView

from app.views import (PaymentSummaryView, CreateEnrollmentView, EnrollmentProductDetailsView, StoreViewSet,
                       ProductViewSet, ContactViewSet, CartViewSet, ImportTaskViewSet, CreateEnrollmentWithPurchaserView)

router = routers.DefaultRouter()

router.register(r'stores', StoreViewSet, 'stores')
router.register(r'products', ProductViewSet, 'products')
router.register(r'contacts', ContactViewSet, 'contacts')
router.register(r'carts', CartViewSet, 'carts')
router.register(r'import-tasks', ImportTaskViewSet, 'import_csv')


urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # bulk enrollment by affiliate-admin from affiliate admin panel
    path('payment-summary/', PaymentSummaryView.as_view(), name='payment_summary'),
    path('create-enrollment/', CreateEnrollmentView.as_view(), name='create_enrollment'),
    path('create-enrollment-with-purchaser/', CreateEnrollmentWithPurchaserView.as_view(), name='create_enrollment_with_purchaser'),
    path('enrollment-product-details/', EnrollmentProductDetailsView.as_view(), name='enrollment_product_details'),
]
