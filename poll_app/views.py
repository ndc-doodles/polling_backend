import re
from django.shortcuts import render, redirect
from django.contrib import messages
from . models import *
from itertools import groupby
import random
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from twilio.rest import Client
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
from django.views.decorators.http import require_POST
from django.utils.html import escape
from django.shortcuts import render, get_object_or_404
import wikipediaapi
import requests

def index(request):
    candidates = Candidate.objects.all()
    districts = District.objects.all()

    # Fetch latest news; fallback to all if none
    news_list = News.objects.filter(latest=True).order_by('-created')[:6]
    if not news_list.exists():
        news_list = News.objects.all().order_by('-created')[:6]

    if request.method == 'POST':
        form_type = request.POST.get('form-type')  # hidden field identifier

        # Security patterns
        sql_pattern = re.compile(r"(?:--|\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|UNION|TABLE|DATABASE)\b)", re.IGNORECASE)
        link_pattern = re.compile(r"(https?:\/\/|www\.)", re.IGNORECASE)
        script_pattern = re.compile(r"<.*?>", re.IGNORECASE)

        def is_invalid(value):
            """Return True if the input contains potentially malicious content."""
            return bool(sql_pattern.search(value) or link_pattern.search(value) or script_pattern.search(value))

        # ---- Opinion Form ----
        if form_type == 'opinion':
            first_name = escape(request.POST.get('first-name', '').strip())
            last_name = escape(request.POST.get('last-name', '').strip())
            email = escape(request.POST.get('email', '').strip())
            message = escape(request.POST.get('message', '').strip())

            if not all([first_name, last_name, email, message]):
                messages.error(request, "⚠️ Please fill out all fields.")
                return redirect(f"{request.path}#opinion-section")

            if any(is_invalid(field) for field in [first_name, last_name, email, message]):
                messages.error(request, "🚫 Invalid content detected — links or SQL terms are not allowed.")
                return redirect(f"{request.path}#opinion-section")

            Opinion.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                message=message
            )
            messages.success(request, "✅ Thank you! Your opinion has been submitted.")
            return redirect(f"{request.path}#opinion-section")

        # ---- Contact Form ----
        elif form_type == 'contact':
            name = escape(request.POST.get('name', '').strip())
            email = escape(request.POST.get('email', '').strip())
            message = escape(request.POST.get('message', '').strip())

            if not all([name, email, message]):
                messages.error(request, "⚠️ Please fill out all contact fields.")
                return redirect(f"{request.path}#contact-section")

            if any(is_invalid(field) for field in [name, email, message]):
                messages.error(request, "🚫 Invalid content detected — links or SQL terms are not allowed.")
                return redirect(f"{request.path}#contact-section")

            Contact.objects.create(
                name=name,
                email=email,
                message=message
            )
            messages.success(request, "📨 Your message has been sent successfully.")
            return redirect(f"{request.path}#contact-section")

    return render(request, "index.html", {
        "candidates": candidates,
        "districts": districts,
        "news_list": news_list,
    })

# ✅ AJAX endpoint for fetching constituencies under a district
def get_constituencies(request, district_id):
    constituencies = Constituency.objects.filter(district_id=district_id)
    data = [{"id": c.id, "name": c.name} for c in constituencies]
    return JsonResponse({"constituencies": data})

def filter_candidates(request):
    district_id = request.GET.get('district')
    constituency_id = request.GET.get('constituency')
    search = request.GET.get('search', '').strip().lower()

    candidates = Candidate.objects.all()

    # 🔹 Filter by district dropdown
    if district_id:
        try:
            district_name = District.objects.get(id=district_id).name
            candidates = candidates.filter(district__iexact=district_name)
        except District.DoesNotExist:
            pass

    # 🔹 Filter by constituency dropdown
    if constituency_id:
        try:
            constituency_name = Constituency.objects.get(id=constituency_id).name
            candidates = candidates.filter(constituency__iexact=constituency_name)
        except Constituency.DoesNotExist:
            pass

    # 🔹 Search filter: match candidate name, party name, district, or constituency
    if search:
        candidates = candidates.filter(
            Q(name__icontains=search) |
            Q(party__name__icontains=search) |
            Q(district__icontains=search) |
            Q(constituency__icontains=search)
        )

    # 🔹 Serialize candidates for the frontend
    data = []
    for cand in candidates:
        data.append({
            'id': cand.id,
            'name': cand.name,
            'district': cand.district,
            'constituency': cand.constituency,
            'party': cand.party.name,
            'party_image': cand.party.image.url if cand.party.image else '',
            'image': cand.image.url if cand.image else '',
        })

    return JsonResponse({'candidates': data})


# Load .env variables
load_dotenv()

# Initialize Twilio client
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
verify_service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")

client = Client(account_sid, auth_token)

otp_storage = {}

@csrf_exempt
def send_otp(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        if not phone:
            return JsonResponse({"error": "Phone number required"}, status=400)

        otp = str(random.randint(100000, 999999))
        otp_storage[phone] = otp

        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"Your OTP for voting is {otp}",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )
        except Exception as e:
            return JsonResponse({"error": f"Failed to send OTP: {str(e)}"}, status=500)

        return JsonResponse({"message": f"OTP sent to {phone}"})

@csrf_exempt
def verify_vote(request):
    if request.method == "POST":
        candidate_id = request.POST.get("candidate_id")
        name = request.POST.get("name")
        age = request.POST.get("age")
        phone = request.POST.get("phone")
        otp = request.POST.get("otp")

        if not all([candidate_id, name, age, phone, otp]):
            return JsonResponse({"error": "All fields are required"}, status=400)

        if otp_storage.get(phone) != otp:
            return JsonResponse({"error": "Invalid OTP"}, status=400)

        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return JsonResponse({"error": "Candidate not found"}, status=404)
        except Exception as e:
            print("Error:", e)
            return JsonResponse({"error": str(e)}, status=500)

        Vote.objects.create(candidate=candidate, name=name, age=age, phone=phone)
        otp_storage.pop(phone, None)

        return JsonResponse({"message": "Vote successfully recorded"})


@csrf_exempt
@require_POST
def submit_vote(request):
    try:
        candidate_id = request.POST.get("candidate_id")
        name = request.POST.get("name")
        age = request.POST.get("age")
        phone = request.POST.get("phone")

        if not all([candidate_id, name, age, phone]):
            return JsonResponse({"error": "Missing required fields."}, status=400)

        # ✅ your vote logic here (save to DB)
        # Example:
        # Vote.objects.create(candidate_id=candidate_id, voter_name=name, age=age, phone=phone)

        return JsonResponse({"success": True, "message": "Vote submitted successfully"})
    except Exception as e:
        print("❌ Submit vote error:", e)
        return JsonResponse({"error": str(e)}, status=500)










def news(request):
    # Slide news (for story slider)
    slide_news = News.objects.filter(slide=True).order_by('category', '-created')

    # Other news (normal list)
    other_news = News.objects.filter(slide=False).order_by('-created')
    top_rated_news = News.objects.filter(top_rated=True).order_by('-created')
    latest_news = News.objects.filter(latest=True).order_by('-created')
    upcoming_news = News.objects.filter(upcoming=True).order_by('-created')

    # Group and randomize slide news
    grouped = {}
    for category, items in groupby(slide_news, key=lambda n: n.category):
        grouped[category] = list(items)

    random_categories = random.sample(list(grouped.keys()), min(3, len(grouped))) if grouped else []

    selected_news = []
    seen_ids = set()

    for cat in random_categories:
        news_items = grouped.get(cat, [])
        random.shuffle(news_items)
        for item in news_items[:5]:
            if item.id not in seen_ids:
                selected_news.append(item)
                seen_ids.add(item.id)

    random.shuffle(selected_news)

    # ✅ Get the last 3 news for the small “other news” sidebar or section
    last_three_news = News.objects.order_by('-created')[:3]

    # Render the template
    return render(request, 'news.html', {
        'grouped_news': selected_news,    # For slider
        'other_news': other_news,         # For full list
        'top_rated_news': top_rated_news, # For sidebar
        'latest_news': latest_news,       # For latest section
        'upcoming_news': upcoming_news,   # For upcoming section
        'last_three_news': last_three_news,  # ✅ New context variable
    })

def news_detail(request, news_id):
    # Fetch the clicked news item
    news_item = get_object_or_404(News, id=news_id)

    # Fetch 3 latest other news (for sidebar)
    related_news = News.objects.exclude(id=news_id).order_by('-created')[:3]

    return render(request, 'blog_detail.html', {
        'news_item': news_item,
        'related_news': related_news,
    })


def overview(request):
    try:
        wiki = wikipediaapi.Wikipedia(
            language='en',
            user_agent='CybeselectApp/1.0 (http://127.0.0.1:8000/; cybeselect@gmail.com)'
        )

        page = wiki.page("Tamil Nadu")

        def collect_sections(sections, result):
            for section in sections:
                if section.text.strip():
                    result.append({
                        "id": section.title.lower().replace(" ", "_"),
                        "title": section.title,
                        "summary": section.text[:2000] + ("..." if len(section.text) > 2000 else ""),
                        "image": None
                    })
                collect_sections(section.sections, result)
            return result

        # Start data list with Introduction
        data = []
        if page.summary.strip():
            data.append({
                "id": "introduction",
                "title": "Introduction",
                "summary": page.summary[:2000] + ("..." if len(page.summary) > 2000 else ""),
                "image": None
            })

        # Add all sections
        data.extend(collect_sections(page.sections, []))

        # ✅ Fetch images using Wikimedia API (smart topic matching)
        def get_image_url(title):
            try:
                search_term = f"Tamil Nadu {title}"
                api_url = (
                    "https://en.wikipedia.org/w/api.php"
                    f"?action=query&titles={search_term.replace(' ', '%20')}"
                    "&prop=pageimages&pithumbsize=800&format=json"
                )
                headers = {
                    "User-Agent": "CybeselectApp/1.0 (http://127.0.0.1:8000/; cybeselect@gmail.com)"
                }
                res = requests.get(api_url, headers=headers, timeout=5)
                res.raise_for_status()
                info = res.json()
                pages = info.get("query", {}).get("pages", {})
                for _, page_data in pages.items():
                    if "thumbnail" in page_data:
                        return page_data["thumbnail"]["source"]
            except Exception:
                return None
            return None

        # 🎨 Assign topic-specific images (with backups)
        fallback_images = [
            "https://upload.wikimedia.org/wikipedia/commons/4/4c/TamilNadu_Collage.png",
            "https://upload.wikimedia.org/wikipedia/commons/1/13/Tamil_Nadu_in_India_%28highlighted%29.svg",
            "https://upload.wikimedia.org/wikipedia/commons/d/d2/Chennai_Central.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/5/5f/Brihadisvara_Temple%2C_Thanjavur.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/b/b9/Kanyakumari_sunset.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/2/2f/Madurai_Meenakshi_Amman_Temple_gopurams.jpg",
        ]

        for i, section in enumerate(data):
            img = get_image_url(section["title"])
            section["image"] = img or fallback_images[i % len(fallback_images)]

        # Remove sections that have no summary text
        data = [d for d in data if d["summary"].strip()]

    except Exception as e:
        data = [{
            "id": "error",
            "title": "Error",
            "summary": f"Unable to fetch Wikipedia data. ({e})",
            "image": "https://upload.wikimedia.org/wikipedia/commons/4/4c/TamilNadu_Collage.png"
        }]

    return render(request, "information.html", {"data": data})














