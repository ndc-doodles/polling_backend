from django.db import models
from cloudinary.models import CloudinaryField
from django.db.models import ForeignKey


class Party(models.Model):
    name = models.CharField(max_length=100)
    image = CloudinaryField('party_image')

    def __str__(self):
        return self.name


class AlignedParty(models.Model):
    name = models.CharField(max_length=100)
    parties = models.ManyToManyField(Party, related_name='aligned_parties')  # ✅ Many-to-many relationship
    image = CloudinaryField('aligned_party_image')

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Constituency(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='constituencies')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Candidate(models.Model):
    name = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    constituency = models.CharField(max_length=100)
    party = models.ForeignKey('Party', on_delete=models.CASCADE, related_name='candidates')
    image = CloudinaryField('candidate_image')

    def __str__(self):
        return f"{self.name} ({self.party.name})"

    @property
    def party_image(self):
        return self.party.image.url  # ✅ easy access


class News(models.Model):
    headline = models.CharField(max_length=100)
    news = models.TextField()
    image = CloudinaryField('news_image')
    category = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    top_rated = models.BooleanField(default=False)
    slide = models.BooleanField(default=False)
    latest = models.BooleanField(default=False)
    upcoming = models.BooleanField(default=False)


    def __str__(self):
        return self.headline


class Vote(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    phone = models.CharField(max_length=15)
    voted_at = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} voted for {self.candidate.name}"

class Opinion(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"





