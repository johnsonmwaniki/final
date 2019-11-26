import operator
from functools import reduce
import django_filters
from django.core.mail import send_mail
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from datetime import datetime
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from django.utils import timezone
from django.urls import reverse
import requests
from django.http import request, HttpResponse
from requests.auth import HTTPBasicAuth
from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm, mpesaform,categories
from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund, UserProfile , mpesapayment
import base64
import random
import string
import stripe
from django.http import HttpResponse
stripe.api_key = settings.STRIPE_SECRET_KEY

def about(request):

    return render(request, 'about.html')

def filtering(request, categories):
    items = Item.objects.filter(categories=categories)
    # items=Item.objects.all()
    print(categories)

    # if 'toilet' in request.GET:
    #     items = items.filter(categories='toilet')
    #
    # if 'cater' in request.GET:
    #     items = items.filter(categories='cater')
    #
    # if 'seat' in request.GET:
    #     items = items.filter(categories='seat')
    print(items)
    # items =Item.objects.all()
    search_term = ''
    # if 'text' in request.GET:
    #     items = items.order_by('title')
    # if 'pub_date' in request.GET:
    #     items = items.order_by('price')
    # if 'price' in request.GET:
    #     items = items.filter(discount_price=0)

    context = {'items': items}

    return render(request, 'filtering.html', context)

class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home.html"
    ordering = ['title']
    form_class = categories
    # items=Item.objects.all()
    # print(items)


    def get_queryset(self):
        result = super(HomeView, self).get_queryset()

        query = self.request.GET.get('q')

        if query:
            query_list = query.split()
            result = result.filter(
                reduce(operator.and_,
                       (Q(title__icontains=q) for q in query_list))
                # reduce(operator.and_,
                #        (Q(description__icontains=q) for q in query_list))
            )



        return result


def contact(request):
    return render(request, 'contact.html')

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            items1=OrderItem.objects.all()
            context = {
                'items1':items1,
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})

            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'C':
                    return redirect('/', payment_option='Cash On Delivery')
                elif payment_option == 'M':
                    return redirect('core:payment', payment_option='mpesa')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False
            }
            userprofile = self.request.user.userprofile
            if userprofile.one_click_purchasing:
                # fetch the users card list
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id,
                    limit=3,
                    object='card'
                )
                card_list = cards['data']
                if len(card_list) > 0:
                    # update the context with the default card
                    context.update({
                        'card': card_list[0]
                    })
            return render(self.request, "payment1.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("core:checkout")

    def post(self, request, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        #form = mpesaform(self.request.POST)
        phone = request.POST.get('phone')
        Amountdue = order.get_total()
        print(phone)
        # print(Amountdue)
        try:
            import requests
            import base64
            from datetime import datetime
            unformated = datetime.now()
            formated = unformated.strftime("%Y%m%d%H%M%S")
            shortcode = '174379'
            passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
            datatoencode = shortcode + passkey + formated
            encodedpassword = base64.b64encode(datatoencode.encode())
            decodedpassword = encodedpassword.decode('utf-8')
            consumer_key = "D86MoHnvcqUhyKA0A8IoORP3BbEJOWL9"
            consumer_secret = "UCVHDJWh49453xJA"
            from requests.auth import HTTPBasicAuth
            consumer_key = consumer_key
            consumer_secret = consumer_secret
            api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

            r = requests.get(api_URL, auth=HTTPBasicAuth(
                consumer_key, consumer_secret))
            print(r.json())
            json_response = r.json()
            myaccess_token = json_response['access_token']
            access_token = myaccess_token
            api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            headers = {"Authorization": "Bearer %s" % access_token}
            request = {
                "BusinessShortCode": shortcode,
                "Password": decodedpassword,
                "Timestamp": formated,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": Amountdue,
                "PartyA": phone,
                "PartyB": shortcode,
                "PhoneNumber": phone,
                "CallBackURL": "https://349569cc.ngrok.io/payment-confirmation/",
                "AccountReference": "35664402",
                "TransactionDesc": "Buy shoes",
            }
            response = requests.post(
                api_url, json=request, headers=headers)
            print(response.text)
            remove_from_cart(request)

        except:
            print("Error at Mpesa call")
        messages.info(self.request, "This order was submitted to safaricom")
        return redirect("/")


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")
# def ItemDetailView(request, slug):
#     prod =Item.objects.filter(slug=slug)
#
#     context=\
#         {'prod':prod}
#     return render(request,'product.html',context)
#
class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            order.items.add(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        items = Item.quantity.filter(order_item)
        item = items - order_item.quantity
        Item.quantity = item
        Item.save()
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received.")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("core:request-refund")


@require_POST
@csrf_exempt
def paymentconf(request):

    stk = json.load(request)
    get_stk = stk.get('Body').get('stkCallback')
    get_success_data = get_stk.get("CallbackMetadata")

    if get_stk:
        MerchantRequestID = get_stk.get('MerchantRequestID')
        CheckoutRequestID = get_stk.get('CheckoutRequestID')
        ResultCode = get_stk.get('ResultCode')
        ResultDesc = get_stk.get('ResultDesc')
        if get_success_data:
            get_items = get_success_data.get('Item')
            for i in get_items:
                if i['Name'] == 'Amount':
                    Amount = i.get('Value')
                elif i['Name'] == 'MpesaReceiptNumber':
                    MpesaReceiptNumber = i.get('Value')
                elif i['Name'] == 'PhoneNumber':
                    PhoneNumber = i.get('Value')
                elif i['Name'] == 'Balance':
                    Balance = i.get('Value')
                elif i['Name'] == 'TransactionDate':
                    TransactionDate = i.get('Value')
                else:
                    continue
        else:
            Amount = None
            MpesaReceiptNumber = None
            PhoneNumber = None
            Balance = None
            TransactionDate = None
    
    mpesapayment.objects.create(MerchantRequestID=MerchantRequestID, CheckoutRequestID=CheckoutRequestID, 
    ResultCode=ResultCode, ResultDesc=ResultDesc, Amount=Amount, MpesaReceiptNumber=MpesaReceiptNumber, 
    PhoneNumber=PhoneNumber, Balance=Balance , TransactionDate=TransactionDate)
    #Item.reduceqty(self)
    data = {
        "success": "Called successfully"
    }
    response = json.dumps(data)
    return HttpResponse(response, content_type='application/json')
def report(request):
    items1 = Item.objects.all()
    items2 = Order.objects.all()
    items3=OrderItem.objects.all()
    print(items1)
    print(items2)

    context={'items1':items1,'items2':items2,'items3':items3}

    return render(request,'report.html',context)
# def contact(request):
#     return render(request, 'microsite/contact.html', {})
# """
# Post contact messages to the database
# """
#
#
# def ContactMessages():
#
#     pass
#
#
# @csrf_exempt
# def contact(request):
#     if request.method == 'POST':
#         if request.POST.get('name') and request.POST.get('name'):
#             message = ContactMessages()
#             message.name = request.POST.get('name')
#             message.phone = request.POST.get('phone')
#             message.email = request.POST.get('email')
#             message.message = request.POST.get('message')
#             message.save()
#
#             subject = 'New message from brooms limited website'
#             # message = ' it  means a world to us'
#             message = '''
#                     New message has been submitted on the system: \n
#                         Name: {}; \n
#                         Phone Number: {}; \n
#                         Email: {}; \n
#                         Message: {} \n
#
#                     '''.format(request.POST.get('name'), request.POST.get('phone'), request.POST.get('email'),
#                                request.POST.get('message'))
#             email_from = settings.EMAIL_HOST_USER
#             recipient_list = ['johnsonmwaniki100@gmail.com']
#             send_mail(subject, message, email_from, recipient_list)
#
#             return render(request, 'home.html')
#
#     else:
#         return render(request, 'contact.html')