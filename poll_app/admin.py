from django.contrib import admin
from . models import *
# Register your models here.

admin.site.register(Party)
admin.site.register(AlignedParty)
admin.site.register(Candidate)
admin.site.register(News)
admin.site.register(District)
admin.site.register(Constituency)
admin.site.register(Vote)
admin.site.register(Opinion)
admin.site.register(Contact)