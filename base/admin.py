from django.contrib import admin

# Register your models here.
from base.models import Member, Message, Conversation

admin.site.register(Member)
admin.site.register(Message)
admin.site.register(Conversation)