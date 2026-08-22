from django.shortcuts import render, HttpResponse, redirect
from django.contrib import admin, messages
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from openpyxl import Workbook
from django.contrib.auth.decorators import login_required
from django.apps import apps
from .forms import MaterialCreateForm, MaterialTarqatishForm
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from main.models import MaterialHistory
from main.models import Material, Remont_Bolimi, CustomUser, Kafedra, Fakultet, Remont_Talab
from django.db.models import ForeignKey, DateTimeField
from django.utils.timezone import is_aware
from django.http import HttpResponse
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.db.models import (
    Q, CharField, TextField, EmailField, SlugField, URLField,
    IntegerField, FloatField, DecimalField, PositiveIntegerField, BigIntegerField,
)

SEARCHABLE_FIELD_TYPES = (
    CharField, TextField, EmailField, SlugField, URLField,
    IntegerField, FloatField, DecimalField, PositiveIntegerField, BigIntegerField,
)


def filter_by_query(queryset, query):
    """
    Berilgan queryset'ning modeliga qarab, matn/son maydonlari bo'yicha
    avtomatik qidiradi. Har bir sahifa o'zining ALLAQACHON filtrlangan
    querysetini shu funksiyaga berib, ustiga qidiruvni qo'shadi.
    """
    if not query:
        return queryset

    model = queryset.model
    q_object = Q()
    for field in model._meta.fields:
        if isinstance(field, SEARCHABLE_FIELD_TYPES):
            q_object |= Q(**{f"{field.name}__icontains": query})

    if not q_object:
        return queryset

    return queryset.filter(q_object)


def home_page(request):
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        if username and password:
            user: CustomUser = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if not user.role == CustomUser.Role.ADMIN:
                    print(user.role, CustomUser.Role.ADMIN)
                    return redirect(user.role)
                else:
                    return redirect('all_material_history')
            else:
                messages.info(request, "Login yoki parol noto'g'ri")
        else:
            messages.info(request, "Login yoki parol kiritilmadi")

    return render(request, 'html/index.html')


def logout_page_view(request):
    logout(request)
    return redirect('/home')


@login_required(login_url='home')
def bulim_view(request):
    if request.user.role != CustomUser.Role.FAKULTET:
        return redirect(request.user.role)

    query = request.GET.get('q', '').strip()
    fakultet = Fakultet.objects.filter(foydalanuvchilar=request.user).first()

    if fakultet:
        materiallar = Material.objects.filter(kafedra__fakultet=fakultet)
        materiallar = filter_by_query(materiallar, query)
    else:
        materiallar = None

    return render(request, 'html/bolim.html', {'material': materiallar, 'query': query})


@login_required(login_url='home')
def hisobchi_view(request):
    if request.user.role != CustomUser.Role.XISOBCHI:
        return redirect(request.user.role)

    query = request.GET.get('q', '').strip()
    materials = Material.objects.all()
    materials = filter_by_query(materials, query)

    return render(request, 'html/hisobchi.html', {'materials': materials, 'query': query})


@login_required(login_url='home')
def kafedra_view(request):
    if request.user.role != CustomUser.Role.KAFEDRA:
        return redirect(request.user.role)

    query = request.GET.get('q', '').strip()
    kafedra = Kafedra.objects.filter(foydalanuvchilar=request.user).first()

    if kafedra:
        materiallar = Material.objects.filter(kafedra=kafedra)
        materiallar = filter_by_query(materiallar, query)
    else:
        materiallar = None

    return render(request, 'html/kafedra.html', {'materiallar': materiallar, 'query': query})


@login_required(login_url='home')
def omborchi_view(request):
    if request.user.role != CustomUser.Role.OMBORCHI:
        return redirect(request.user.role)

    query = request.GET.get('q', '').strip()
    materials = Material.objects.filter(
        Q(status=Material.Status.YANGI) | Q(status=Material.Status.REMONT) | Q(status=Material.Status.QAYTGAN)
    )
    materials = filter_by_query(materials, query)

    return render(request, 'html/omborchi.html', {'materials': materials, 'query': query})


@login_required(login_url='home')
def add_material_view(request):
    if request.method == 'POST':
        form = MaterialCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("omborchi")
        else:
            messages.info(request, "ma'lumotlar xato kiritildi")

    return render(request, 'html/material_crete_form.html')



@login_required(login_url='home')
def tarqatish_material_view(request):
    materials = Material.objects.filter(Q(status=Material.Status.YANGI) | Q(status=Material.Status.QAYTGAN))
    kafedra = Kafedra.objects.all()
    users = CustomUser.objects.filter(Q(role='kafedra') | Q(role='fakultet'))

    if request.method == "POST":
        material_id = request.POST.get('maxsulot')
        material = get_object_or_404(Material, id=material_id)

        # Tarix uchun ESKI holatni saqlab qolamiz — form.is_valid() dan keyin
        # material obyekti allaqachon yangi qiymatlar bilan almashtirilgan bo'ladi
        old_status = material.status
        old_to_user = material.foydalanuvchi_shaxs

        form = MaterialTarqatishForm(request.POST, instance=material)
        if form.is_valid():
            updated_material = form.save(commit=False)
            updated_material.tarqatilgan_sana = timezone.localtime()
            updated_material.status = "BIRIKTIRILGAN"
            updated_material.save()

            MaterialHistory.objects.create(
                material=updated_material,
                action=MaterialHistory.Action.BIRIKTIRISH,
                from_user=old_to_user,
                to_user=updated_material.foydalanuvchi_shaxs,
                kafedra=updated_material.kafedra,
                old_status=old_status,
                new_status=updated_material.status,
                created_by=request.user,
            )
        else:
            messages.info(request, "Ma'lumotlar xato kiritildi")

    context = {
        'material': materials,
        'kafedra': kafedra,
        'users': users,
    }
    return render(request, 'html/material_tarqatish_form.html', context)

@login_required(login_url='home')
def qorovul_view(request):
    if request.user.role != CustomUser.Role.QOROVUL:
        return redirect(request.user.role)

    query = request.GET.get('q', '').strip()
    resurs = Material.objects.filter(Q(status=Material.Status.CHIQQAN) | Q(status=Material.Status.QAYTGAN))
    resurs = filter_by_query(resurs, query)

    return render(request, 'html/qorovul.html', {'resurs': resurs, 'query': query})


@login_required(login_url='home')
def remont_bolimi_view(request):
    if request.user.role != CustomUser.Role.USTA:
        return redirect(request.user.role)

    query = request.GET.get('q', '').strip()
    remont = Remont_Bolimi.objects.filter(status_new="REMONT")
    sorov = Remont_Talab.objects.filter(status="YANGI")

    remont = filter_by_query(remont, query)
    sorov = filter_by_query(sorov, query)

    return render(request, 'html/remont_bolimi.html', {'remont': remont, 'sorov': sorov, 'query': query})


@login_required(login_url='home')
@require_POST
def bekor_qilish(request, pk):
    obj = get_object_or_404(Remont_Talab, pk=pk)
    obj.status = Remont_Talab.Status.BEKOR_QILINGAN
    obj.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required(login_url='home')
@require_POST
def tasdiqlash(request, pk):
    talab = get_object_or_404(Remont_Talab, pk=pk)
    material = talab.material
    old_status = material.status

    Remont_Bolimi.objects.create(
        material=material,
        remont_qilish_xodimi=request.user.get_full_name() or request.user.username,
        remontga_berilgan_sana=timezone.now(),
        remontdan_oldingi_xolati=talab.izoh,
        remontdan_kiyingi_xolati="",
        foydalanuvchi=str(talab.talaba),
    )

    # Avval bu qator umuman yo'q edi — shuning uchun material hech qachon
    # "REMONT" statusiga o'tmagan va omborchida ko'rinmagan
    material.status = Material.Status.REMONT
    material.save(update_fields=['status'])

    talab.status = Remont_Talab.Status.TASDIQLANGAN
    talab.save()

    MaterialHistory.objects.create(
        material=material,
        action=MaterialHistory.Action.REMONTGA_BERISH,
        from_user=talab.talaba,
        kafedra=talab.kafedra,
        xona=talab.xona,
        old_status=old_status,
        new_status=material.status,
        izoh=talab.izoh,
        created_by=request.user,
    )

    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='home')
def material_history_view(request, pk):
    material = get_object_or_404(Material, pk=pk)
    history = material.history.select_related('from_user', 'to_user', 'kafedra', 'created_by')
    return render(request, 'html/material_history.html', {
        'material': material,
        'history': history,
    })

@login_required(login_url='home')
def ariza_create(request):
    if request.method == 'POST':
        Remont_Talab.objects.create(
            material_id=request.POST.get('material'),
            talaba=request.user,
            kafedra_id=request.POST.get('kafedra'),
            xona=request.POST.get('xona'),
            izoh=request.POST.get('izoh'),
        )
        return redirect('talaba')  # yoki list page

    context = {
        'materials': Material.objects.all(),
        'kafedralar': Kafedra.objects.all(),
    }
    return render(request, 'html/request.html', context)


def export_model_to_excel(request, app_name, model_name):
    model = apps.get_model(app_name, model_name)

    wb = Workbook()
    ws = wb.active
    ws.title = model_name

    fields = model._meta.fields

    # 🔹 Header
    ws.append([field.verbose_name for field in fields])

    for obj in model.objects.all():
        row = []

        for field in fields:
            value = getattr(obj, field.name)

            if isinstance(field, ForeignKey):
                value = str(value) if value else ""

            elif isinstance(field, DateTimeField) and value:
                if is_aware(value):
                    value = value.replace(tzinfo=None)

            row.append(value)

        ws.append(row)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{model_name}.xlsx"'

    wb.save(response)
    return response


def resource_pdf(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="talabnoma.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)

    styles = getSampleStyleSheet()
    elements = []

    # ===== TITLE =====
    title_style = ParagraphStyle(
        name="title",
        alignment=1,
        fontSize=14,
        spaceAfter=10
    )

    elements.append(Paragraph(
        "MODDIY BOYLIKLARNI TOPSHIRISH-QABUL QILISH TALABNOMASI",
        title_style
    ))

    elements.append(Spacer(1, 10))

    # ===== INFO BLOCK =====
    info_data = [
        ["Talabnoma raqami:", "__________", "Sana:", "__________"],
        ["Kafedra / bo'lim:", "__________", "Resurs shartnomasi:", "__________"],
        ["", "", "Ro'yxatdan kirish sanasi:", "__________"],
    ]

    info_table = Table(info_data, colWidths=[120, 120, 150, 120])
    elements.append(info_table)

    elements.append(Spacer(1, 20))

    # ===== TABLE DATA FROM DB =====
    items = Material.objects.all()

    table_data = [[
        "ID",
        "Resurs shartnomasi",
        "Resurs nomi",
        "O'lchov",
        "Inventar",
        "Xona",
        "Holati"
    ]]

    for i, item in enumerate(items, start=1):
        table_data.append([
            i,
            "-",
            item.resurs_nomi,
            item.ulchov_birligi,
            item.soni,
            item.inventor_raqami,
            item.status
        ])

    table = Table(table_data, repeatRows=1)

    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 25))

    # ===== SIGNATURE BLOCK =====
    sign_data = [
        ["Beruvchi", "Qabul qiluvchi", "Buxgalter"],
        ["F.I.Sh: ________", "F.I.Sh: ________", "F.I.Sh: ________"],
        ["Lavozimi: ________", "Lavozimi: ________", "Lavozimi: ________"],
        ["Imzo: ________", "Imzo: ________", "Imzo: ________"],
        ["Sana: ________", "Sana: ________", "Sana: ________"],
    ]

    sign_table = Table(sign_data, colWidths=[180, 180, 180])

    sign_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT')
    ]))

    elements.append(sign_table)

    doc.build(elements)

    return response


@login_required(login_url='home')
def all_material_history_view(request):
    if request.user.role != CustomUser.Role.ADMIN:
        return redirect(request.user.role)

    query = request.GET.get('q', '').strip()
    history = MaterialHistory.objects.select_related(
        'material', 'from_user', 'to_user', 'kafedra', 'created_by'
    ).all()
    history = filter_by_query(history, query)

    return render(request, 'html/all_history.html', {'history': history, 'query': query})