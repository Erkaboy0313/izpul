from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from openpyxl import Workbook
from django.http import HttpResponse
from django.db.models import Q, CharField, TextField , ForeignKey, DateTimeField
from django.contrib.auth.decorators import login_required
from django.apps import apps
from .forms import MaterialCreateForm, MaterialTarqatishForm
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Material, Remont_Bolimi, CustomUser, Kafedra, Fakultet, Remont_Talab
from django.utils.timezone import is_aware
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4,landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib import colors

def home_page(request):
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        if username and password:
            user: CustomUser = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if not user.role == CustomUser.Role.ADMIN:
                    return redirect(user.role)
                else:
                    return redirect('/admin')
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

    fakultet = Fakultet.objects.filter(foydalanuvchilar=request.user).first()

    if fakultet:
        materiallar = Material.objects.filter(kafedra__fakultet=fakultet)

    else:
        materiallar = None


    return render(request, 'html/bolim.html', {'material': materiallar})

@login_required(login_url='home')
def hisobchi_view(request):
    if request.user.role != CustomUser.Role.XISOBCHI:
        return redirect(request.user.role)

    materials = Material.objects.all()

    return render(request, 'html/hisobchi.html', {'materials': materials})

@login_required(login_url='home')
def kafedra_view(request):
    if request.user.role != CustomUser.Role.KAFEDRA:
        return redirect(request.user.role)

    kafedra = Kafedra.objects.filter(foydalanuvchilar=request.user).first()

    if kafedra:
        materiallar = Material.objects.filter(kafedra = kafedra)

    else :
        materiallar = None

    return render(request, 'html/kafedra.html', {'materiallar': materiallar})

@login_required(login_url='home')
def omborchi_view(request):
    if request.user.role != CustomUser.Role.OMBORCHI:
        return redirect(request.user.role)
    materials = Material.objects.filter(
        Q(status=Material.Status.YANGI) | Q(status=Material.Status.REMONT) | Q(status=Material.Status.QAYTGAN))
    return render(request, 'html/omborchi.html', {'materials': materials})

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

    """
    pk = yangilanadigan Material ID sini oladi
    """

    if request.method == "POST":
        material_id = request.POST.get('maxsulot')
        material = get_object_or_404(Material, id=material_id)
        form = MaterialTarqatishForm(request.POST, instance=material)
        if form.is_valid():
            updated_material = form.save(commit=False)
            # tarqatilgan_sana hozirgi vaqtga teng bo'lsin
            updated_material.tarqatilgan_sana = timezone.localtime()
            updated_material.status = "BIRIKTIRILGAN"  # Django settings.TIME_ZONE ga mos
            updated_material.save()

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

    resurs = Material.objects.filter(Q(status=Material.Status.CHIQQAN) | Q(status=Material.Status.QAYTGAN))

    return render(request, 'html/qorovul.html', {'resurs': resurs})

@login_required(login_url='home')
def remont_bolimi_view(request):
    if request.user.role != CustomUser.Role.USTA:
        return redirect(request.user.role)

    remont = Remont_Bolimi.objects.filter(status_new = "REMONT")
    sorov = Remont_Talab.objects.filter(status = "YANGI")

    return render(request, 'html/remont_bolimi.html', {'remont': remont, 'sorov': sorov})

def bekor_qilish(request, pk):
    obj = Remont_Talab.objects.get(pk=pk)
    obj.status = Remont_Talab.Status.BEKOR_QILINGAN
    obj.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))

def tasdiqlash(request, pk):

    talab = Remont_Talab.objects.get(pk=pk)

    Remont_Bolimi.objects.create(
        material=talab.material,
        remont_qilish_xodimi=request.user,
        remontga_berilgan_sana=timezone.now(),
        remontdan_oldingi_xolati=talab.izoh,
        remontdan_kiyingi_xolati="",
        foydalanuvchi = ''
    )

    talab.status = Remont_Talab.Status.TASDIQLANGAN
    talab.save()

    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='home')
def ariza_create(request):
    if request.method == 'POST':
        Remont_Talab.objects.create(
            material_id=request.POST.get('material'),
            talaba = request.user,
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

def search(request):
    query = request.GET.get('q', '')
    models = apps.get_models()
    results = {}

    if query:
        for model in apps.get_models():
            q_object = Q()

            for field in model._meta.fields:
                if isinstance(field, (CharField, TextField)):
                    q_object |= Q(**{f"{field.name}__icontains": query})

            if q_object:
                qs = model.objects.filter(q_object)
                if qs.exists():
                    results[model.__name__] = qs

    return render(request, 'html/hisobchi.html', {'results': results, 'query': query})

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

    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),  # ✅ horizontal for wide tables
        rightMargin=20,
        leftMargin=20,
        topMargin=30,
        bottomMargin=30
    )

    elements = []
    styles = getSampleStyleSheet()

    # ===== TITLE =====
    title_style = ParagraphStyle(
        name="title",
        fontSize=14,
        leading=18,
        alignment=1,
        spaceAfter=10,
        bold=True
    )
    elements.append(Paragraph("MODDIY BOYLIKLARNI TOPSHIRISH-QABUL QILISH TALABNOMASI", title_style))
    elements.append(Spacer(1, 10))

    # ===== INFO BLOCK =====
    info_data = [
        ["Talabnoma raqami:", "__________", "Sana:", "__________"],
        ["Kafedra / bo'lim:", "__________", "Resurs shartnomasi:", "__________"],
        ["", "", "Ro'yxatdan kirish sanasi:", "__________"],
    ]

    info_table = Table(info_data, colWidths=[120,120,150,120])
    elements.append(info_table)
    elements.append(Spacer(1, 20))


    table_style_text = styles["Normal"]
    table_style_text.fontSize = 8  # smaller font for wide tables

    table_data = get_table_data(request.user,table_style_text)
    col_widthes = get_flexible_col_widths(table_data, font_size=8, min_width=10, max_width=60, padding=3)
    
    
    table = Table(
        table_data,
        repeatRows=1,
        colWidths=col_widthes
    )
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAEAEA")),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
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
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ]))
    elements.append(sign_table)

    # ===== PAGE FOOTER (optional page number) =====
    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        page_num = f"{doc.page}"
        canvas.drawRightString(landscape(A4)[0] - 20, 15, page_num)
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    return response

def get_table_data(user:CustomUser,table_style_text):
    
    table_data = []
    
    if not user.role in ["xisobchi","omborchi","kafedra","usta","fakultet"]:
        table_data.append([])
        return table_data
    
    
    if user.role == "kafedra":
        kafedra = Kafedra.objects.filter(foydalanuvchilar=user).first()

        if kafedra:
            items = Material.objects.filter(kafedra = kafedra)
        else:
            items = []
        
        table_data.append([
            Paragraph("<b>T/R</b>", table_style_text),
            Paragraph("<b>Inventor raqam</b>", table_style_text),
            Paragraph("<b>MAC raqam</b>", table_style_text),
            Paragraph("<b>Brend nomi</b>", table_style_text),
            Paragraph("<b>O'lchov birligi</b>", table_style_text),
            Paragraph("<b>Resurs xususiyati</b>", table_style_text),
            Paragraph("<b>Joylashgan bino</b>", table_style_text),
            Paragraph("<b>Javobgar shaxs</b>", table_style_text),
            Paragraph("<b>Foydalanuvchi shaxs</b>", table_style_text),
            Paragraph("<b>Sana</b>", table_style_text),
            Paragraph("<b>Xolati</b>", table_style_text),
        ])

        for i, item in enumerate(items, start=1):
            table_data.append([
                Paragraph(str(i), table_style_text),
                Paragraph(item.inventor_raqami or "", table_style_text),
                Paragraph(item.mac_raqami or "", table_style_text),
                Paragraph(item.resurs_nomi or "", table_style_text),
                Paragraph(str(item.ulchov_birligi), table_style_text),
                Paragraph(item.resurs_xususiyati or "", table_style_text),
                Paragraph(item.joylashgan_bino or "", table_style_text),
                Paragraph(item.get_javobgar_shaxs or "", table_style_text),
                Paragraph(item.get_foydalanuvchi_shaxs or "", table_style_text),
                Paragraph(item.kirish_vaqti.strftime("%d-%m-%Y") or "", table_style_text),
                Paragraph(item.status or "", table_style_text),
            ])
    
    elif user.role == "xisobchi":
        items = Material.objects.all()
        
        table_data.append([
            Paragraph("<b>T/R</b>", table_style_text),
            Paragraph("<b>Inventor raqam</b>", table_style_text),
            Paragraph("<b>MAC raqam</b>", table_style_text),
            Paragraph("<b>Shartnoma raqami</b>", table_style_text),
            Paragraph("<b>Brend nomi</b>", table_style_text),
            Paragraph("<b>O'lchov birligi</b>", table_style_text),
            Paragraph("<b>Resurs xususiyati</b>", table_style_text),
            Paragraph("<b>Joylashgan bino</b>", table_style_text),
            Paragraph("<b>Kafedra/Bo'lim</b>", table_style_text),
            Paragraph("<b>Javobgar shaxs</b>", table_style_text),
            Paragraph("<b>Foydalanuvchi shaxs</b>", table_style_text),
            Paragraph("<b>Sana</b>", table_style_text),
            Paragraph("<b>Xolati</b>", table_style_text),
        ])

        for i, item in enumerate(items, start=1):
            table_data.append([
                Paragraph(str(i), table_style_text),
                Paragraph(item.inventor_raqami or "", table_style_text),
                Paragraph(item.mac_raqami or "", table_style_text),
                Paragraph(item.shartnoma_raqami or "", table_style_text),
                Paragraph(str(item.resurs_nomi), table_style_text),
                Paragraph(item.ulchov_birligi or "", table_style_text),
                Paragraph(item.resurs_xususiyati or "", table_style_text),
                Paragraph(item.joylashgan_bino or "", table_style_text),
                Paragraph(item.get_kafedra or "", table_style_text),
                Paragraph(item.get_javobgar_shaxs or "", table_style_text),
                Paragraph(item.get_foydalanuvchi_shaxs or "", table_style_text),
                Paragraph(item.kirish_vaqti.strftime("%d-%m-%Y") or "", table_style_text),
                Paragraph(item.status or "", table_style_text),
            ])
    
    elif user.role == "omborchi":

        items = Material.objects.filter(
            Q(status=Material.Status.YANGI) | Q(status=Material.Status.REMONT) | Q(status=Material.Status.QAYTGAN))
        
        table_data.append([
            Paragraph("<b>T/R</b>", table_style_text),
            Paragraph("<b>Resurs shartnomasi</b>", table_style_text),
            Paragraph("<b>Resurs brand</b>", table_style_text),
            Paragraph("<b>O'lchov birligi</b>", table_style_text),
            Paragraph("<b>Resurs soni</b>", table_style_text),
            Paragraph("<b>Qanday xususiyatdagi resurs bayoni</b>", table_style_text),
            Paragraph("<b>Inventor raqam</b>", table_style_text),
            Paragraph("<b>Sana</b>", table_style_text)
        ])

        for i, item in enumerate(items, start=1):
            table_data.append([
                Paragraph(str(i), table_style_text),
                Paragraph(item.shartnoma_raqami or "", table_style_text),
                Paragraph(item.resurs_nomi or "", table_style_text),
                Paragraph(item.ulchov_birligi or "", table_style_text),
                Paragraph(str(item.soni), table_style_text),
                Paragraph(item.resurs_xususiyati or "", table_style_text),
                Paragraph(item.inventor_raqami or "", table_style_text),
                Paragraph(item.kirish_vaqti.strftime("%d-%m-%Y") or "", table_style_text)
            ])
    
    elif user.role == "fakultet":
        fakultet = Fakultet.objects.filter(foydalanuvchilar=user).first()

        if fakultet:
            items = Material.objects.filter(kafedra__fakultet=fakultet)
        else:
            items = []
        
        table_data.append([
            Paragraph("<b>T/R</b>", table_style_text),
            Paragraph("<b>Inventor raqam</b>", table_style_text),
            Paragraph("<b>MAC raqam</b>", table_style_text),
            Paragraph("<b>Shartnoma raqami</b>", table_style_text),
            Paragraph("<b>Brend nomi</b>", table_style_text),
            Paragraph("<b>O'lchov birligi</b>", table_style_text),
            Paragraph("<b>Resurs xususiyati</b>", table_style_text),
            Paragraph("<b>Joylashgan bino</b>", table_style_text),
            Paragraph("<b>Javobgar shaxs</b>", table_style_text),
            Paragraph("<b>Foydalanuvchi shaxs</b>", table_style_text),
            Paragraph("<b>Sana</b>", table_style_text)
        ])

        for i, item in enumerate(items, start=1):
            table_data.append([
                Paragraph(str(i), table_style_text),
                Paragraph(item.inventor_raqami or "", table_style_text),
                Paragraph(item.mac_raqami or "", table_style_text),
                Paragraph(item.shartnoma_raqami or "", table_style_text),
                Paragraph(item.resurs_nomi or "", table_style_text),
                Paragraph(str(item.ulchov_birligi), table_style_text),
                Paragraph(item.resurs_xususiyati or "", table_style_text),
                Paragraph(item.joylashgan_bino or "", table_style_text),
                Paragraph(item.get_javobgar_shaxs or "", table_style_text),
                Paragraph(item.get_foydalanuvchi_shaxs or "", table_style_text),
                Paragraph(item.kirish_vaqti.strftime("%d-%m-%Y") or "", table_style_text)
            ])
    
    elif user.role == "usta":

        items = Remont_Bolimi.objects.filter(status_new = "REMONT")

        table_data.append([
            Paragraph("<b>T/R</b>", table_style_text),
            Paragraph("<b>Resurs nomi</b>", table_style_text),
            Paragraph("<b>Remont qilish xodim</b>", table_style_text),
            Paragraph("<b>Remontga berilgan sana</b>", table_style_text),
            Paragraph("<b>Remontdan qaytganm sana</b>", table_style_text),
            Paragraph("<b>Remontdan oldingi xolat</b>", table_style_text),
            Paragraph("<b>Remontdan kiyingi xolat</b>", table_style_text),
            Paragraph("<b>Fydalanuvchi</b>", table_style_text),
            Paragraph("<b>Xolati</b>", table_style_text)
        ])

        for i, item in enumerate(items, start=1):
            table_data.append([
                Paragraph(str(i), table_style_text),
                Paragraph(item.material.resurs_nomi or "", table_style_text),
                Paragraph(item.remont_qilish_xodimi or "", table_style_text),
                Paragraph(item.remontga_berilgan_sana.strftime("%d-%m-%Y") or "", table_style_text),
                Paragraph(item.remontdan_qaytgan_sana.strftime("%d-%m-%Y") or "", table_style_text),
                Paragraph(item.remontdan_oldingi_xolati or "", table_style_text),
                Paragraph(item.remontdan_kiyingi_xolati or "", table_style_text),
                Paragraph(item.foydalanuvchi or "", table_style_text),
                Paragraph(item.status_new or "", table_style_text)
            ])
    
    
    
    return table_data

def get_flexible_col_widths(table_data, font_name='Helvetica', font_size=8, min_width=40, max_width=100, padding=5):
    """
    Compute flexible colWidths based on the longest content in each column.
    """
    num_cols = len(table_data[0])
    
    max_width = max_width if num_cols > 8 else 80 if 6 < num_cols < 8 else 100 
    
    col_widths = [min_width] * num_cols  # start with min width

    for col_index in range(num_cols):
        max_content_width = min_width
        for row in table_data:
            cell = row[col_index]
            # if Paragraph, extract text
            if hasattr(cell, 'text'):
                text = cell.text
            else:
                text = str(cell)
            width = stringWidth(text, font_name, font_size) + padding
            if width > max_content_width:
                max_content_width = width
        col_widths[col_index] = min(max_content_width, max_width)

    return col_widths