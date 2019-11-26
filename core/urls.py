from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views
app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('report/', views.report, name='report'),
    path('about/', views.about, name='about'),
    path('filtering/<categories>', views.filtering, name='filtering'),
    path('contact/', views.contact, name='contact'),
    path('order-summary/', views.OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>/', views.ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', views.add_to_cart, name='add-to-cart'),
    path('add-coupon/', views.AddCouponView.as_view(), name='add-coupon'),
    path('remove-from-cart/<slug>/', views.remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>/', views.remove_single_item_from_cart,
         name='remove-single-item-from-cart'),
    path('payment/<payment_option>/', views.PaymentView.as_view(), name='payment'),
    path('request-refund/', views.RequestRefundView.as_view(), name='request-refund'),
    path('payment-confirmation/', csrf_exempt(views.paymentconf),
         name='payment-confirmation')
    #path('mpesa/', include('mpesa_api.core.urls', 'mpesa'))
]
