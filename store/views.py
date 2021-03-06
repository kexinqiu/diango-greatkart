

# # Create your views here.
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect

from accounts.models import Account
from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category
from orders.models import OrderProduct
from store.models import Product, ReviewRating, ProductGallery
from django.core.paginator import  EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from .forms import ReviewForm




def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        product_count = products.count()
        # page
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)


    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        product_count = products.count()
        #page
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)

    context = {
        'products': paged_products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        # -- is the syntax to get access to the slug of that model
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()

    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    #get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    #get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
    }

    return render(request, 'store/product_detail.html', context)

def search(request):

    if 'keyword' in request.GET:
        #store the value of keyword in the varible keyword
        keyword = request.GET['keyword']

        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()

    return render(request, 'store/store.html', {
        'products': products,
        'product_count':product_count,
    })

def submit_review(request, product_id):
    current_url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            #user__id to access the id of the user
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            #pass request.POST can have all the data about the review
            #passing instance to check if there is already reviews, then we need to update that review,
            #if don't pass the instance, it will create a new review
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated!')
            return redirect(current_url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                #['subject'], ['rating'],['review'] come form html
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted')
                return redirect(current_url)




