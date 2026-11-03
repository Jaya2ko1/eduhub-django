from django.shortcuts import render,redirect,get_object_or_404
from .forms import CategoryForm
from .models import Category
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST



def can_manage_categories(user):
    return user.role in (user.ADMIN, user.TEACHER)


# Create your views here.

@login_required
def create_category(request):
    if not can_manage_categories(request.user):
        messages.error(request, "Only teachers and admins can create categories.")
        return redirect('list_category')
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_category')
    else:
        form = CategoryForm()
    return render(request,"category/category_create.html",{'form':form})

@login_required
def edit_category(request,id):
    if not can_manage_categories(request.user):
        messages.error(request, "Only teachers and admins can edit categories.")
        return redirect('list_category')
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        form = CategoryForm(request.POST,instance=category)
        if form.is_valid():
            form.save()
            return redirect('list_category')
    else:
        form = CategoryForm(instance=category)
    return render(request,"category/category_update.html",{'form':form})

@login_required
@require_POST
def delete_category(request,id):
    if request.user.role != request.user.ADMIN:
        messages.error(request, "Only admins can delete categories.")
        return redirect('list_category')
    del_category = get_object_or_404(Category, id=id)
    # Course.category uses CASCADE, so deleting a used category would also delete
    # its courses, lessons, enrollments and progress. Block it here instead.
    if del_category.courses.exists():
        messages.error(request, "Cannot delete a category that still has courses. Move or delete its courses first.")
        return redirect('list_category')
    del_category.delete()

    messages.success(request, "Category deleted successfully.")

    return redirect('list_category')
    
@login_required
def list_category(request):
    categories = Category.objects.all().order_by('-id')
    paginator = Paginator(categories, 5)  

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request,"category/category_list.html",{'page_obj':page_obj,'categories':categories})

@login_required
def search(request):
    query = request.GET.get("search", "").strip()
    category = request.GET.get("category","")
    status = request.GET.get("status","")

    categories = Category.objects.all()

    if query:
        categories =categories.filter(
            Q(category__icontains=query) |
            Q(description__icontains=query)
        ).order_by("-id")

    # Ignore invalid filter values instead of crashing with a 500.
    if category.isdigit():
        categories = categories.filter(id = category)

    if status in ("True", "False"):
        categories = categories.filter(status = status)

    paginator = Paginator(categories, 5)  
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "category/category_search.html",
        {
            "page_obj": page_obj,
            "query": query,
            'category':category,
            'categories':categories,
            'status':status,

        },
    )