from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .models import Kurs, TestBlock, Savol, TestNatija
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
    return render(request, 'testapp/blocks_list.html', {'kurs': kurs, 'blocks': blocks})

@login_required
def start_test(request, block_id):
    block = get_object_or_404(TestBlock, id=block_id)
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
        
        for savol in savollar:
            javob = request.POST.get(f'savol_{savol.id}')
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
            vaqt_sekund=vaqt
        )
        
        return redirect('test_result', natija_id=natija.id)
    
    return redirect('select_kurs')

@login_required
def test_result(request, natija_id):
    natija = get_object_or_404(TestNatija, id=natija_id, user=request.user)
    jami = natija.togri_javoblar + natija.xato_javoblar
    foiz = (natija.togri_javoblar / jami * 100) if jami > 0 else 0
    
    minutes = natija.vaqt_sekund // 60
    seconds = natija.vaqt_sekund % 60
    
    return render(request, 'testapp/result.html', {
        'natija': natija,
        'jami': jami,
        'foiz': round(foiz, 2),
        'minutes': minutes,
        'seconds': seconds
    })