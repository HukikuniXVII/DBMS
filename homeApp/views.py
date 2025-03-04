from django.shortcuts import render
from serviceApp.models import Service,Review
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
def index(request):
    return render(request, 'index.html')

def main_service_list(request):
    services = Service.objects.all()[:3]
    return render(request, 'index.html', {'services': services})

@csrf_exempt
def get_reviews(request):
    if request.method == "GET":
        reviews = Review.objects.select_related("user").order_by("-review_date")[:4]  # ดึง 10 รีวิวล่าสุด
        review_list = [
            {
                "name": review.user.get_full_name(),
                "date": review.review_date.strftime("%d %B %Y"),
                "rating": review.rating,
                "comment": review.comments,
                "profile_img": "https://img.freepik.com/premium-vector/portrait-beautiful-women-round-frame-avatar-female-character-isolated-white-background_559729-210.jpg?w=740"
            }
            for review in reviews
        ]
        return JsonResponse({"reviews": review_list}, safe=False)
    return JsonResponse({"error": "Invalid request method"}, status=405)