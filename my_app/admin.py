from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import Kurs, TestBlock, Savol, TestNatija, RetestRequest

@admin.register(Kurs)
class KursAdmin(admin.ModelAdmin):
    list_display = ['raqami', 'nomi']
    search_fields = ['nomi', 'raqami']

@admin.register(TestBlock)
class TestBlockAdmin(admin.ModelAdmin):
    list_display = ['nomi', 'kurs', 'block_turi', 'vaqt_turi', 'boshlash_vaqti', 'tugash_vaqti', 'is_active']
    list_filter = ['block_turi', 'vaqt_turi', 'kurs']
    search_fields = ['nomi']
    filter_horizontal = ['tanlangan_userlar']

    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('nomi', 'kurs')
        }),
        ('Test sozlamalari', {
            'fields': ('block_turi', 'vaqt_turi', 'savol_vaqti')
        }),
        ('Vaqt sozlamalari', {
            'fields': ('boshlash_vaqti', 'tugash_vaqti'),
            'description': 'Yopiq testlar uchun boshlanish va tugash vaqtini belgilang'
        }),
        ('Ruxsatlar', {
            'fields': ('tanlangan_userlar',),
            'description': 'Yopiq testlar uchun ruxsat berilgan foydalanuvchilarni tanlang'
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard-redirect/', self.admin_site.admin_view(self.dashboard_redirect), name='dashboard_redirect'),
        ]
        return custom_urls + urls
    


@admin.register(Savol)
class SavolAdmin(admin.ModelAdmin):
    list_display = ['matn_qisqa', 'block', 'togri_javob']
    list_filter = ['block']
    search_fields = ['matn']
    readonly_fields = ['rasm_preview']
    
    fieldsets = (
        ('Savol', {
            'fields': ('block', 'matn')
        }),
        ('Rasm (majburiy emas)', {
            'fields': ('rasm', 'rasm_preview'),
            'description': "Savolga rasm qo'shish ixtiyoriy"
        }),
        ('Variantlar', {
            'fields': ('variant_a', 'variant_b', 'variant_c', 'variant_d')
        }),
        ("To'g'ri javob", {
            'fields': ('togri_javob',)
        }),
    )
    
    def matn_qisqa(self, obj):
        return obj.matn[:50] + '...' if len(obj.matn) > 50 else obj.matn
    matn_qisqa.short_description = 'Savol'
    
    def has_image(self, obj):
        if obj.rasm:
            return format_html('<span style="color: green;">✓ Bor</span>')
        return format_html('<span style="color: gray;">✗ Yuq</span>')
    has_image.short_description = 'Rasm'
    
    def rasm_preview(self, obj):
        if obj.rasm:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px; border: 1px solid #ddd;" />',
                obj.rasm.url
            )
        return "Rasm yuklanmagan"
    rasm_preview.short_description = 'Rasm ko\'rinishi'

@admin.register(TestNatija)
class TestNatijaAdmin(admin.ModelAdmin):
    list_display = ['user', 'block', 'togri_javoblar', 'xato_javoblar', 'jami_savollar', 'foiz', 'vaqt_format', 'topshirilgan_vaqt']
    list_filter = ['block', 'topshirilgan_vaqt']
    search_fields = ['user__username', 'block__nomi']
    readonly_fields = ['javoblar']
    
    def vaqt_format(self, obj):
        minutes = obj.vaqt_sekund // 60
        seconds = obj.vaqt_sekund % 60
        return f"{minutes}:{seconds:02d}"
    vaqt_format.short_description = 'Vaqt'

@admin.register(RetestRequest)
class RetestRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'block', 'status', 'yuborilgan_vaqt', 'korilgan_vaqt']
    list_filter = ['status', 'yuborilgan_vaqt']
    search_fields = ['user__username', 'block__nomi', 'sabab']
    readonly_fields = ['yuborilgan_vaqt']
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='tasdiqlandi', korilgan_vaqt=timezone.now())
        self.message_user(request, f"{queryset.count()} ta so'rov tasdiqlandi.")
    approve_requests.short_description = "Tanlangan so'rovlarni tasdiqlash"
    
    def reject_requests(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='rad_etildi', korilgan_vaqt=timezone.now())
        self.message_user(request, f"{queryset.count()} ta so'rov rad etildi.")
    reject_requests.short_description = "Tanlangan so'rovlarni rad etish"
