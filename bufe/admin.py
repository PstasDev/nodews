from django.contrib import admin
from .models import *


class OpeningHoursInline(admin.TabularInline):
    model = OpeningHours
    extra = 1


@admin.register(Bufe)
class BufeAdmin(admin.ModelAdmin):
    list_display = ['nev', 'rendkivuli_zarva']

    filter_horizontal = ['bufeadmin']

    inlines = [OpeningHoursInline]


@admin.register(OpeningHours)
class OpeningHoursAdmin(admin.ModelAdmin):
    list_display = ['bufe', 'weekday', 'from_hour', 'to_hour']
    list_filter = ['weekday', 'bufe']


@admin.register(Kategoria)
class KategoriaAdmin(admin.ModelAdmin):
    list_display = ['nev', 'bufe']
    list_filter = ['bufe']
    search_fields = ['nev']


@admin.register(Termek)
class TermekAdmin(admin.ModelAdmin):
    list_display = ['nev', 'kategoria', 'ar', 'elerheto', 'hutve', 'kisult', 'max_rendelesenkent']
    list_filter = ['kategoria', 'elerheto', 'hutve', 'kisult']
    search_fields = ['nev']
    list_editable = ['elerheto', 'kisult']


@admin.register(Rendeles)
class RendelesAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'allapot', 'vegosszeg', 'leadva', 'idozitve', 'archived']
    list_filter = ['allapot', 'archived', 'leadva']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['leadva']
    date_hierarchy = 'leadva'
    actions = ['archive_selected', 'dearchive_selected']
    
    @admin.action(description='Archív kijelölt rendelések')
    def archive_selected(self, request, queryset):
        count = queryset.update(archived=True)
        self.message_user(request, f'{count} rendelés archiválva.')
    
    @admin.action(description='Dearchív kijelölt rendelések')
    def dearchive_selected(self, request, queryset):
        count = queryset.update(archived=False)
        self.message_user(request, f'{count} rendelés dearchiválva.')

# Később lesz implementálva a chat funkció
# @admin.register(Chatszoba)
# class ChatszobaAdmin(admin.ModelAdmin):
#     list_display = ['id', 'rendeles', 'created_at']
#     readonly_fields = ['created_at']


# @admin.register(Uzenet)
# class UzenetAdmin(admin.ModelAdmin):
#     list_display = ['id', 'chatszoba', 'szerzo', 'sent', 'uzenet_preview']
#     list_filter = ['sent']
#     search_fields = ['szerzo__username', 'uzenet']
#     readonly_fields = ['sent']
#     date_hierarchy = 'sent'
    
#     def uzenet_preview(self, obj):
#         return obj.uzenet[:50] + '...' if len(obj.uzenet) > 50 else obj.uzenet
#     uzenet_preview.short_description = 'Üzenet előnézet'

