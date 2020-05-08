import random

from django.shortcuts import render
from .models import Product, Contact, Orders, OrderUpdate
from math import ceil
import json
from django.http import HttpResponse


def index(request):
    prods = Product.objects.all().order_by('pub_date')[:1000]
    prods = [prod for prod in prods]
    """ take the recent 16 items as recommended"""
    recommended = prods
    random.shuffle(recommended)
    recommended = recommended[:16]
    mod_recommended = []
    i = 0
    while (i + 4) <= len(recommended):
        mod_recommended.append(recommended[i:(i + 4)])
        i += 4
    first_slide = mod_recommended[0] if mod_recommended else []
    other_slides = mod_recommended[1:] if mod_recommended else []
    catProds = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catProds}
    allProds = {}
    for cat in cats:
        allProds.update({cat: Product.objects.filter(category=cat)})
    params = {'allProds': allProds, 'other_slides': other_slides,
              'first_slide': first_slide, 'range': range(1, len(mod_recommended))}
    return render(request, 'shop/index.html', params)


def searchMatch(query, item):
    """return true only if query matches the item"""
    if query in item.desc.lower() or query in item.product_name.lower() \
            or query in item.category.lower() or query in item.subcategory.lower():
        return True
    return False


def search(request):
    query = request.GET.get('search').lower()
    if maliciousString(query):
        params = {'msg': "Please make sure to enter relevant search query"}
        return render(request, 'shop/search.html', params)
    prodTemp = Product.objects.all()
    prods = [item for item in prodTemp if searchMatch(query, item)][:100]
    if prods:
        return render(request, 'shop/search.html', {'allProds': prods})
    params = {'msg': "Nothing matched your search"}
    return render(request, 'shop/search.html', params)


def about(request):
    return render(request, 'shop/about.html')


def contact(request):
    thank = False
    if request.method == "POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        sender = Contact(name=name, email=email, phone=phone, desc=desc)
        sender.save()
        thank = True
    return render(request, 'shop/contact.html', {'thank': thank})


def tracker(request):
    if request.method == "POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Orders.objects.filter(order_id=orderId, email=email)
            if len(order) > 0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps({"status": "success", "updates": updates, "itemsJson": order[0].items_json},
                                          default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status":"noitem"}')
        except Exception as e:
            return HttpResponse('{"status":"error"}')

    return render(request, 'shop/tracker.html')


def productView(request, myid):
    # Fetch the product using the id
    product = Product.objects.filter(id=myid)
    return render(request, 'shop/prodView.html', {'product': product[0]})


def checkout(request):
    if request.method == "POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order = Orders(items_json=items_json, name=name, email=email, address=address, city=city,
                       state=state, zip_code=zip_code, phone=phone, amount=amount)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()
        thank = True
        id = order.order_id
        return render(request, 'shop/checkout.html', {'thank': thank, 'id': id})
        # Request paytm to transfer the amount to your account after payment by user
        # param_dict = {
        #
        #     'MID': 'Your-Merchant-Id-Here',
        #     'ORDER_ID': str(order.order_id),
        #     'TXN_AMOUNT': str(amount),
        #     'CUST_ID': email,
        #     'INDUSTRY_TYPE_ID': 'Retail',
        #     'WEBSITE': 'WEBSTAGING',
        #     'CHANNEL_ID': 'WEB',
        #     'CALLBACK_URL': 'http://127.0.0.1:8000/shop/handlerequest/',
        #
        # }
        # param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
        # return render(request, 'shop/paytm.html', {'param_dict': param_dict})

    return render(request, 'shop/checkout.html')


# @csrf_exempt
# def handlerequest(request):
#     # paytm will send you post request here
#     form = request.POST
#     response_dict = {}
#     for i in form.keys():
#         response_dict[i] = form[i]
#         if i == 'CHECKSUMHASH':
#             checksum = form[i]
#
#     verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
#     if verify:
#         if response_dict['RESPCODE'] == '01':
#             print('order successful')
#         else:
#             print('order was not successful because' + response_dict['RESPMSG'])
#     return render(request, 'shop/paymentstatus.html', {'response': response_dict})

def maliciousString(s):
    ranges = [[33, 48], [58, 65], [91, 97], [123, 127]]
    for i in range(len(s)):
        for bad_chars in ranges:
            if ord(s[i]) in range(bad_chars[0], bad_chars[1]):
                return True
    return False
