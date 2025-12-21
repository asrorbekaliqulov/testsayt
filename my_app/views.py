from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from .models import Kurs, TestBlock, Savol, TestNatija, RetestRequest
import json

def register_view(request):
    if request.user.is_authenticated:
        return redirect('select_kurs')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Ro'yxatdan muvaffaqiyatli o'tdingiz!")
            return redirect('select_kurs')
    else:
        form = UserCreationForm()
    
    return render(request, 'testapp/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('select_kurs')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Xush kelibsiz, {username}!")
                return redirect('select_kurs')
    else:
        form = AuthenticationForm()
    
    return render(request, 'testapp/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Tizimdan chiqdingiz.")
    return redirect('login')

@login_required
def select_kurs(request):
    if request.method == 'POST':
        kurs_id = request.POST.get('kurs_id')
        return redirect('blocks_list', kurs_id=kurs_id)
    
    kurslar = Kurs.objects.all().order_by('raqami')
    return render(request, 'testapp/select_kurs.html', {'kurslar': kurslar})

@login_required
def blocks_list(request, kurs_id):
    kurs = get_object_or_404(Kurs, id=kurs_id)
    blocks = TestBlock.objects.filter(kurs=kurs)
    
    blocks_data = []
    for block in blocks:
        natija = TestNatija.objects.filter(user=request.user, block=block).first()
        
        retest_request = RetestRequest.objects.filter(
            user=request.user, 
            block=block, 
            status='kutilmoqda'
        ).first()
        
        blocks_data.append({
            'block': block,
            'can_access': block.user_can_access(request.user),
            'is_active': block.is_active(),
            'natija': natija,
            'retest_request': retest_request,
            'savollar_soni': block.savollar.count()
        })
    
    return render(request, 'testapp/blocks_list.html', {
        'kurs': kurs, 
        'blocks_data': blocks_data
    })

@login_required
def start_test(request, block_id):
    block = get_object_or_404(TestBlock, id=block_id)
    
    if not block.user_can_access(request.user):
        messages.error(request, "Siz bu testga kirish huquqiga ega emassiz!")
        return redirect('blocks_list', kurs_id=block.kurs.id)
    
    if not block.is_active():
        messages.error(request, "Test hali boshlanmagan yoki tugagan!")
        return redirect('blocks_list', kurs_id=block.kurs.id)
    
    natija = TestNatija.objects.filter(user=request.user, block=block).first()
    if natija:
        retest = RetestRequest.objects.filter(
            user=request.user, 
            block=block, 
            status='tasdiqlandi'
        ).order_by('-korilgan_vaqt').first()
        
        if not retest:
            messages.warning(request, "Siz allaqachon bu testni ishlagansiz. Qayta ishlash uchun admindan ruxsat so'rang.")
            return redirect('blocks_list', kurs_id=block.kurs.id)
        else:
            retest.delete()
            natija.delete()
    
    savollar = list(block.savollar.all())
    
    return render(request, 'testapp/test.html', {
        'block': block,
        'savollar': savollar,
        'savollar_soni': len(savollar)
    })

@login_required
def submit_test(request, block_id):
    if request.method == 'POST':
        block = get_object_or_404(TestBlock, id=block_id)
        savollar = block.savollar.all()
        
        togri = 0
        xato = 0
        javoblar = {}
        
        for savol in savollar:
            javob = request.POST.get(f'savol_{savol.id}')
            javoblar[str(savol.id)] = {
                'berilgan_javob': javob,
                'togri_javob': savol.togri_javob,
                'togri': javob == savol.togri_javob if javob else False
            }
            
            if javob:
                if javob == savol.togri_javob:
                    togri += 1
                else:
                    xato += 1
        
        vaqt = int(request.POST.get('vaqt', 0))
        
        natija = TestNatija.objects.create(
            user=request.user,
            block=block,
            togri_javoblar=togri,
            xato_javoblar=xato,
            jami_savollar=savollar.count(),
            vaqt_sekund=vaqt,
            javoblar=javoblar
        )
        
        return redirect('test_result', natija_id=natija.id)
    
    return redirect('select_kurs')

@login_required
def test_result(request, natija_id):
    natija = get_object_or_404(TestNatija, id=natija_id, user=request.user)
    
    minutes = natija.vaqt_sekund // 60
    seconds = natija.vaqt_sekund % 60
    
    return render(request, 'testapp/result.html', {
        'natija': natija,
        'minutes': minutes,
        'seconds': seconds,
        'foiz': natija.foiz(),
        'jami': natija.jami_savollar
    })

@login_required
def request_retest(request, block_id):
    block = get_object_or_404(TestBlock, id=block_id)
    
    if request.method == 'POST':
        sabab = request.POST.get('sabab', '').strip()
        
        if not sabab:
            messages.error(request, "Iltimos, sabab kiriting!")
            return redirect('blocks_list', kurs_id=block.kurs.id)
        
        # Avvalgi kutilayotgan so'rov bormi tekshirish
        existing = RetestRequest.objects.filter(
            user=request.user,
            block=block,
            status='kutilmoqda'
        ).first()
        
        if existing:
            messages.warning(request, "Sizning so'rovingiz allaqachon ko'rib chiqilmoqda!")
        else:
            RetestRequest.objects.create(
                user=request.user,
                block=block,
                sabab=sabab
            )
            messages.success(request, "So'rovingiz adminga yuborildi!")
        
        return redirect('blocks_list', kurs_id=block.kurs.id)
    
    return render(request, 'testapp/request_retest.html', {'block': block})

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "Bu sahifaga faqat adminlar kirishi mumkin!")
        return redirect('select_kurs')
    
    # Kutilayotgan so'rovlar
    pending_requests = RetestRequest.objects.filter(status='kutilmoqda').select_related('user', 'block')
    
    # Barcha blocklar
    blocks = TestBlock.objects.all().select_related('kurs')
    
    return render(request, 'testapp/admin_dashboard.html', {
        'pending_requests': pending_requests,
        'blocks': blocks
    })

@login_required
def admin_approve_retest(request, request_id):
    if not request.user.is_staff:
        messages.error(request, "Ruxsat yo'q!")
        return redirect('select_kurs')
    
    retest_request = get_object_or_404(RetestRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        javob = request.POST.get('javob', '')
        
        if action == 'approve':
            retest_request.status = 'tasdiqlandi'
            messages.success(request, f"{retest_request.user.username} uchun qayta test ruxsat berildi!")
        elif action == 'reject':
            retest_request.status = 'rad_etildi'
            messages.info(request, "So'rov rad etildi.")
        
        retest_request.admin_javobi = javob
        retest_request.korilgan_vaqt = timezone.now()
        retest_request.save()
        
        return redirect('admin_dashboard')
    
    return render(request, 'testapp/admin_approve_retest.html', {'retest_request': retest_request})

@login_required
def admin_block_results(request, block_id):
    if not request.user.is_staff:
        messages.error(request, "Ruxsat yo'q!")
        return redirect('select_kurs')
    
    block = get_object_or_404(TestBlock, id=block_id)
    natijalar = TestNatija.objects.filter(block=block).select_related('user').order_by('-topshirilgan_vaqt')
    
    return render(request, 'testapp/admin_block_results.html', {
        'block': block,
        'natijalar': natijalar
    })
