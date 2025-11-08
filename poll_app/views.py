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
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import json



@never_cache
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")

@never_cache
def logout_view(request):
    logout(request)
    return redirect("login")




# @never_cache
# @login_required(login_url='login')
# def dashboard(request):
#     # ---- Add District ----
#     if request.method == "POST" and "district_name" in request.POST:
#         name = request.POST.get("district_name", "").strip()
#         if not name:
#             messages.error(request, "Please enter a valid district name.")
#         elif District.objects.filter(name__iexact=name).exists():
#             messages.warning(request, f"District '{name}' already exists.")
#         else:
#             District.objects.create(name=name)
#             messages.success(request, f"District '{name}' added successfully!")
#         return redirect("dashboard")
#
#     # ---- Add Constituency ----
#     if request.method == "POST" and "constituency_name" in request.POST:
#         district_id = request.POST.get("district_id")
#         name = request.POST.get("constituency_name", "").strip()
#         if not district_id or not name:
#             messages.error(request, "Please select a district and enter a constituency name.")
#         elif Constituency.objects.filter(district_id=district_id, name__iexact=name).exists():
#             messages.warning(request, f"'{name}' already exists in this district.")
#         else:
#             Constituency.objects.create(district_id=district_id, name=name)
#             messages.success(request, f"Constituency '{name}' added successfully!")
#         return redirect("dashboard")
#
#     districts = District.objects.all().order_by("name")
#     constituencies = Constituency.objects.select_related("district").order_by("district__name", "name")
#
#     return render(request, "dashboard.html", {
#         "districts": districts,
#         "constituencies": constituencies
#     })


@never_cache
@login_required(login_url='login')
def dashboard(request):
    # ---- Add District ----
    if request.method == "POST" and "district_name" in request.POST:
        name = request.POST.get("district_name", "").strip()
        if not name:
            messages.error(request, "Please enter a valid district name.")
        elif District.objects.filter(name__iexact=name).exists():
            messages.warning(request, f"District '{name}' already exists.")
        else:
            District.objects.create(name=name)
            messages.success(request, f"District '{name}' added successfully!")
        return redirect("dashboard")

    # ---- Add Constituency ----
    if request.method == "POST" and "constituency_name" in request.POST:
        district_id = request.POST.get("district_id")
        name = request.POST.get("constituency_name", "").strip()
        if not district_id or not name:
            messages.error(request, "Please select a district and enter a constituency name.")
        elif Constituency.objects.filter(district_id=district_id, name__iexact=name).exists():
            messages.warning(request, f"'{name}' already exists in this district.")
        else:
            Constituency.objects.create(district_id=district_id, name=name)
            messages.success(request, f"Constituency '{name}' added successfully!")
        return redirect("dashboard")

    # ---- Data Query ----
    districts = District.objects.annotate(total_constituencies=Count('constituencies')).order_by('name')
    constituencies = Constituency.objects.select_related('district').order_by('district__name', 'name')

    candidates = Candidate.objects.select_related("district", "constituency", "party").all()

    candidate_data = [
        {
            "id": c.id,
            "name": c.name,
            "district": c.district.name,
            "district_id": c.district.id,
            "constituency": c.constituency.name,
            "constituency_id": c.constituency.id,
            "party": c.party.name,
            "party_image": c.party.image.url if c.party.image else "",
            "image": c.image.url if c.image else "",
            "votes": c.votes.count(),
        }
        for c in candidates
    ]

    # ---- Pagination ----
    paginator = Paginator(candidate_data, 15)  # 10 candidates per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "districts": districts,
        "constituencies": constituencies,
        "page_obj": page_obj,
    }
    return render(request, "dashboard.html", context)


@never_cache
@login_required(login_url='login')
def Candidates(request):
    districts = District.objects.all().order_by("name")
    constituencies = Constituency.objects.all().order_by("name")
    parties = Party.objects.all().order_by("name")

    # Fetch all candidates with related data
    candidates_qs = Candidate.objects.select_related("district", "constituency", "party").order_by("name")

    # ✅ Pagination: show 10 candidates per page
    paginator = Paginator(candidates_qs, 10)
    page_number = request.GET.get("page")
    candidates_page = paginator.get_page(page_number)

    # ✅ Handle POST (Add new candidate)
    if request.method == "POST":
        name = request.POST.get("name")
        district_id = request.POST.get("district")
        constituency_id = request.POST.get("constituency")
        party_id = request.POST.get("party")
        image = request.FILES.get("candidate_image")

        if not (name and district_id and constituency_id and party_id):
            messages.error(request, "⚠️ Please fill all required fields.")
            return redirect("candidates")

        # Check for duplicate candidate in same constituency
        if Candidate.objects.filter(name__iexact=name, constituency_id=constituency_id).exists():
            messages.error(request, f"❌ Candidate '{name}' already exists in this constituency.")
            return redirect("candidates")

        try:
            district = District.objects.get(id=district_id)
            constituency = Constituency.objects.get(id=constituency_id)
            party = Party.objects.get(id=party_id)
        except (District.DoesNotExist, Constituency.DoesNotExist, Party.DoesNotExist):
            messages.error(request, "❌ Invalid selection for district, constituency, or party.")
            return redirect("candidates")

        # Create candidate
        Candidate.objects.create(
            name=name,
            district=district,
            constituency=constituency,
            party=party,
            image=image
        )
        messages.success(request, f"✅ Candidate '{name}' added successfully!")
        return redirect("candidates")

    # ✅ Render page with paginated candidates
    return render(request, "candidate.html", {
        "districts": districts,
        "constituencies": constituencies,
        "parties": parties,
        "candidates": candidates_page,  # send paginated candidates
    })

def get_constituencies(request, district_id):
    constituencies = Constituency.objects.filter(district_id=district_id).values('id', 'name')
    return JsonResponse({'constituencies': list(constituencies)})

@never_cache
@login_required(login_url='login')
def opinion(request):
    opinions = Opinion.objects.all().order_by('-created')
    # ✅ Pagination: show 10 candidates per page
    paginator = Paginator(opinions, 15)
    page_number = request.GET.get("page")
    opinions = paginator.get_page(page_number)

    return render(request, "opinion.html", {'opinions': opinions})

@require_POST
def delete_opinion(request, id):
    opinion = get_object_or_404(Opinion, id=id)
    opinion.delete()
    return redirect('opinion')

@require_POST
def delete_selected_opinions(request):
    ids = request.POST.getlist('selected_ids[]')
    Opinion.objects.filter(id__in=ids).delete()
    return redirect('opinion')

@never_cache
@login_required(login_url='login')
def admin_news(request):
    if request.method == "POST":
        headline = request.POST.get("headline")
        category = request.POST.get("category")
        label = request.POST.get("label")
        news_text = request.POST.get("news")
        image = request.FILES.get("image")

        top_rated = bool(request.POST.get("top_rated"))
        slide = bool(request.POST.get("slide"))
        latest = bool(request.POST.get("latest"))
        upcoming = bool(request.POST.get("upcoming"))


        News.objects.create(
            headline=headline,
            category=category,
            label=label,
            news=news_text,
            image=image,
            top_rated=top_rated,
            slide=slide,
            latest=latest,
            upcoming=upcoming,
        )
        return redirect("admin_news")

    news_items = News.objects.all().order_by("-created")
    # ✅ Pagination: show 10 candidates per page
    paginator = Paginator(news_items, 15)
    page_number = request.GET.get("page")
    news_items = paginator.get_page(page_number)

    return render(request, "admin_news.html", {"news_items": news_items})


@require_POST
def delete_news(request, id):
    news = get_object_or_404(News, id=id)
    news.delete()
    return redirect("admin_news")


@csrf_exempt
@require_POST
def delete_selected_news(request):
    try:
        data = json.loads(request.body)
        ids = data.get("ids", [])
        News.objects.filter(id__in=ids).delete()
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

@never_cache
@login_required(login_url='login')
def admin_blog(request):
    if request.method == "POST":
        heading = request.POST.get("heading")
        category_id = request.POST.get("category")
        paragraph = request.POST.get("paragraph")
        image = request.FILES.get("image")

        category = get_object_or_404(Category, id=category_id)
        Blog.objects.create(
            heading=heading,
            category=category,
            paragraph=paragraph,
            image=image
        )
        messages.success(request, "Blog added successfully!")
        return redirect("admin_blog")

    blogs_list = Blog.objects.all().order_by("-created")
    paginator = Paginator(blogs_list, 5)
    page_number = request.GET.get("page")
    blogs = paginator.get_page(page_number)

    categories = Category.objects.all()
    return render(request, "admin_blog.html", {"blogs": blogs, "categories": categories})


@never_cache
@login_required(login_url='login')
def add_category(request):
    name = request.POST.get("name")
    if name:
        Category.objects.create(name=name)
        messages.success(request, "Category added successfully!")
    return redirect("admin_blog")



@require_POST
def delete_blog(request, id):
    blog = get_object_or_404(Blog, id=id)
    blog.delete()
    messages.success(request, "Blog deleted successfully!")
    return redirect("admin_blog")

@never_cache
@login_required(login_url='login')
def admin_contact(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_contacts")
        if selected_ids:
            Contact.objects.filter(id__in=selected_ids).delete()
            return redirect("admin_contact")

    contacts = Contact.objects.all().order_by("-created")
    return render(request, "contact.html", {"contacts": contacts})


def delete_contact(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id)
    contact.delete()
    return redirect("admin_contact")

@never_cache
@login_required(login_url='login')
def admin_party(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        # ================= CREATE PARTY =================
        if form_type == "party":
            name = request.POST.get("party_name")
            image = request.FILES.get("party_image")
            if name and image:
                Party.objects.create(name=name, image=image)

        # ================= ADD / EDIT ALIGNED PARTY =================
        elif form_type == "aligned":
            name = request.POST.get("aligned_party_name")
            selected_ids = request.POST.getlist("selected_parties")
            aligned_id = request.POST.get("aligned_id")

            if aligned_id:  # ✅ Edit existing aligned party
                aligned_party = get_object_or_404(AlignedParty, id=aligned_id)
                aligned_party.name = name
                aligned_party.save()
                aligned_party.parties.set(selected_ids)
            else:  # ✅ Create new aligned party
                aligned_party = AlignedParty.objects.create(name=name)
                aligned_party.parties.set(selected_ids)

        return redirect("admin_party")

    # ================= GET DATA =================
    parties = Party.objects.all()
    aligned_parties = AlignedParty.objects.prefetch_related("parties").all()

    # ✅ Collect all party IDs that are already assigned to any aligned group
    assigned_party_ids = list(
        AlignedParty.objects.values_list("parties__id", flat=True).distinct()
    )

    # ✅ Pass all required data to template
    context = {
        "parties": parties,
        "aligned_parties": aligned_parties,
        "assigned_party_ids": assigned_party_ids,
    }

    return render(request, "party.html", context)

@never_cache
@login_required(login_url='login')
def add_party(request):
    if request.method == "POST":
        name = request.POST.get("name")
        image = request.FILES.get("image")
        if name and image:
            Party.objects.create(name=name, image=image)
        return redirect("admin_party")

def delete_party(request, party_id):
    get_object_or_404(Party, id=party_id).delete()
    return redirect("admin_party")

@never_cache
@login_required(login_url='login')
def add_aligned_party(request):
    if request.method == "POST":
        name = request.POST.get("name")
        image = request.FILES.get("image")
        selected_parties = request.POST.getlist("parties")
        aligned = AlignedParty.objects.create(name=name, image=image)
        aligned.parties.set(selected_parties)
        return redirect("admin_party")

def delete_aligned_party(request, aligned_id):
    get_object_or_404(AlignedParty, id=aligned_id).delete()
    return redirect("admin_party")

@never_cache
@login_required(login_url='login')
def admin_votes(request):
    districts = District.objects.all()

    # Selected district & constituency
    selected_district_id = request.GET.get("district")
    selected_constituency_id = request.GET.get("constituency")

    district = District.objects.filter(id=selected_district_id).first() or districts.first()
    constituencies = Constituency.objects.filter(district=district)

    constituency = Constituency.objects.filter(id=selected_constituency_id).first() or constituencies.first()

    # ✅ Overall Votes (for Bar Chart)
    party_votes = list(
        Party.objects.annotate(vote_count=Count('candidates__votes')).values('name', 'vote_count')
    )

    aligned_votes = []
    for aligned in AlignedParty.objects.prefetch_related('parties'):
        total_votes = sum(
            p.candidates.aggregate(total=Count('votes'))['total'] or 0
            for p in aligned.parties.all()
        )
        aligned_votes.append({'name': aligned.name, 'vote_count': total_votes})

    # ✅ District-wise Votes
    district_party_votes = list(
        Party.objects.annotate(
            vote_count=Count('candidates__votes', filter=Q(candidates__district=district))
        ).values('name', 'vote_count')
    )

    district_aligned_votes = []
    for aligned in AlignedParty.objects.prefetch_related('parties'):
        total_votes = sum(
            p.candidates.filter(district=district).aggregate(total=Count('votes'))['total'] or 0
            for p in aligned.parties.all()
        )
        district_aligned_votes.append({'name': aligned.name, 'vote_count': total_votes})

    # ✅ Constituency-wise Votes
    constituency_party_votes = list(
        Party.objects.annotate(
            vote_count=Count('candidates__votes', filter=Q(candidates__constituency=constituency))
        ).values('name', 'vote_count')
    )

    constituency_aligned_votes = []
    for aligned in AlignedParty.objects.prefetch_related('parties'):
        total_votes = sum(
            p.candidates.filter(constituency=constituency).aggregate(total=Count('votes'))['total'] or 0
            for p in aligned.parties.all()
        )
        constituency_aligned_votes.append({'name': aligned.name, 'vote_count': total_votes})

    # ✅ AJAX responses for dynamic updates
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if 'constituency' in request.GET:
            return JsonResponse({
                'constituency_party_votes': constituency_party_votes,
                'constituency_aligned_votes': constituency_aligned_votes,
            })
        elif 'district' in request.GET:
            constituency_data = list(constituencies.values('id', 'name'))
            return JsonResponse({
                'district_party_votes': district_party_votes,
                'district_aligned_votes': district_aligned_votes,
                'constituencies': constituency_data,
            })

    return render(request, 'vote.html', {
        'districts': districts,
        'selected_district': district.id if district else None,
        'constituencies': constituencies,
        'selected_constituency': constituency.id if constituency else None,
        'party_votes': json.dumps(party_votes),
        'aligned_votes': json.dumps(aligned_votes),
        'district_party_votes': json.dumps(district_party_votes),
        'district_aligned_votes': json.dumps(district_aligned_votes),
        'constituency_party_votes': json.dumps(constituency_party_votes),
        'constituency_aligned_votes': json.dumps(constituency_aligned_votes),
    })

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
    search = request.GET.get('search', '').strip()

    candidates = Candidate.objects.all()

    # Filter by district
    if district_id:
        candidates = candidates.filter(district_id=district_id)

    # Filter by constituency
    if constituency_id:
        candidates = candidates.filter(constituency_id=constituency_id)

    # Search
    if search:
        candidates = candidates.filter(
            Q(name__icontains=search) |
            Q(party__name__icontains=search) |
            Q(district__name__icontains=search) |
            Q(constituency__name__icontains=search)
        )

    # Serialize
    data = [{
        "id": c.id,
        "name": c.name,
        "district": c.district.name,
        "constituency": c.constituency.name,
        "party": c.party.name,
        "party_image": c.party.image.url if c.party.image else "",
        "image": c.image.url if c.image else ""
    } for c in candidates]

    return JsonResponse({"candidates": data})

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
    # 🔹 Fetch categorized news
    slide_news = News.objects.filter(slide=True).order_by('category', '-created')
    top_rated_news = News.objects.filter(top_rated=True).order_by('-created')
    latest_news = News.objects.filter(latest=True).order_by('-created')
    upcoming_news = News.objects.filter(upcoming=True).order_by('-created')

    # 🔹 Exclude Top Rated, Slide, Latest, Upcoming
    other_news = News.objects.filter(
        slide=False,
        top_rated=False,
        latest=False,
        upcoming=False
    ).order_by('-created')

    # 🔹 Group slide news by category and randomize
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

    # 🔹 Last 3 recent news
    last_three_news = News.objects.order_by('-created')[:3]

    return render(request, 'news.html', {
        'grouped_news': selected_news,     # For slider
        'other_news': other_news,          # For list excluding top/latest/upcoming
        'top_rated_news': top_rated_news,  # For sidebar
        'latest_news': latest_news,        # For latest section
        'upcoming_news': upcoming_news,    # For upcoming section
        'last_three_news': last_three_news,
    })


def news_detail(request, news_id):
    # Fetch the clicked news item
    news_item = get_object_or_404(News, id=news_id)

    # Fetch 3 latest other news (for sidebar)
    related_news = News.objects.exclude(id=news_id).order_by('-created')[:3]

    return render(request, 'news_detail.html', {
        'news_item': news_item,
        'related_news': related_news,
    })

IMAGE_CACHE = {}

def overview(request):
    try:
        # Initialize Wikipedia API
        wiki = wikipediaapi.Wikipedia(
            language='en',
            user_agent='CybeselectApp/1.0 (http://127.0.0.1:8000/; cybeselect@gmail.com)'
        )

        page = wiki.page("Tamil Nadu")

        # Recursive collector for subsections
        def collect_sections(sections, result):
            for section in sections:
                if section.text.strip():
                    result.append({
                        "id": section.title.lower().replace(" ", "_"),
                        "title": section.title,
                        "summary": section.text[:2000] + ("..." if len(section.text) > 2000 else ""),
                    })
                collect_sections(section.sections, result)
            return result

        data = []

        # Add introduction
        if page.summary.strip():
            data.append({
                "id": "introduction",
                "title": "Introduction",
                "summary": page.summary[:2000] + ("..." if len(page.summary) > 2000 else ""),
            })

        # Add all other sections
        data.extend(collect_sections(page.sections, []))

        # 🎯 Image map for contextual matching
        image_map = {
            "introduction": "https://upload.wikimedia.org/wikipedia/commons/4/4c/TamilNadu_Collage.png",
            "history": "https://upload.wikimedia.org/wikipedia/commons/2/2f/Madurai_Meenakshi_Amman_Temple_gopurams.jpg",
            "geography": "https://upload.wikimedia.org/wikipedia/commons/1/13/Tamil_Nadu_in_India_%28highlighted%29.svg",
            "climate": "https://upload.wikimedia.org/wikipedia/commons/b/b9/Kanyakumari_sunset.jpg",
            "flora": "https://upload.wikimedia.org/wikipedia/commons/0/09/Western_Ghats_Tamil_Nadu.jpg",
            "fauna": "https://upload.wikimedia.org/wikipedia/commons/d/d4/Mudumalai_Tiger_Reserve_elephants.jpg",
            "culture": "https://upload.wikimedia.org/wikipedia/commons/5/5f/Brihadisvara_Temple%2C_Thanjavur.jpg",
            "economy": "https://upload.wikimedia.org/wikipedia/commons/f/f7/Chennai_IT_Park.jpg",
            "politics": "https://upload.wikimedia.org/wikipedia/commons/f/fd/Tamil_Nadu_Legislative_Assembly.jpg",
            "administration": "https://upload.wikimedia.org/wikipedia/commons/f/fd/Tamil_Nadu_Legislative_Assembly.jpg",
            "transport": "https://upload.wikimedia.org/wikipedia/commons/d/d2/Chennai_Central.jpg",
            "education": "https://upload.wikimedia.org/wikipedia/commons/4/4c/IIT_Madras_Campus.jpg",
            "demographics": "https://upload.wikimedia.org/wikipedia/commons/d/d0/Chennai_Skyline.jpg",
        }

        # 🧠 Match sections with image_map (case-insensitive containment)
        for section in data:
            title_key = section["title"].lower()
            matched_image = None
            for key, url in image_map.items():
                if key in title_key:
                    matched_image = url
                    break
            section["image"] = matched_image

        # Remove empty summaries
        data = [d for d in data if d["summary"].strip()]

        # 🪶 Debug: check mapping in console
        print("\n=== IMAGE DEBUG ===")
        for s in data:
            print(f"{s['title']} → {s.get('image')}")
        print("===================\n")

    except Exception as e:
        data = [{
            "id": "error",
            "title": "Error",
            "summary": f"Unable to load Tamil Nadu information. ({e})",
            "image": None
        }]

    return render(request, "information.html", {"data": data})


def blogs(request):
    blogs = Blog.objects.all()
    categories = Category.objects.all()
    context = {
        "blogs": blogs,
        "categories": categories,
    }
    return render(request,'blog.html',context)





