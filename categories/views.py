from django.shortcuts import render,redirect
from .forms import CategoryForm
from .models import Category
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q



# Create your views here.

def create_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_category')
    else:
        form = CategoryForm()
    return render(request,"category/category_create.html",{'form':form})

def edit_category(request,id):
    category = Category.objects.get(id=id)
    if request.method == 'POST':
        form = CategoryForm(request.POST,instance=category)
        if form.is_valid():
            form.save()
            return redirect('list_category')
    else:
        form = CategoryForm(instance=category)
    return render(request,"category/category_update.html",{'form':form})

def delete_category(request,id):
    del_category = Category.objects.get(id=id)
    del_category.delete()

    messages.success(request, "Category deleted successfully.")

    return redirect('list_category')
    
def list_category(request):
    category_list = Category.objects.all().order_by('-id')
    paginator = Paginator(category_list, 5)  

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request,"category/category_list.html",{'page_obj':page_obj})

def search(request):
    query = request.GET.get("search", "").strip()

    categories = Category.objects.none()

    if query:
        categories = Category.objects.filter(
            Q(category__icontains=query) |
            Q(description__icontains=query)
        ).order_by("-id")

    return render(
        request,
        "category/category_search.html",
        {
            "categories": categories,
            "query": query,
        },
    )