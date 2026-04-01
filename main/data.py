import random
from django.utils import timezone
from .models import Material, Kafedra, CustomUser, Change_reason


def seed_materials():
    kafedralar = list(Kafedra.objects.all())
    users = list(CustomUser.objects.all())
    reasons = list(Change_reason.objects.all())

    if not users:
        raise Exception("CustomUser table empty")
    if not kafedralar:
        raise Exception("Kafedra table empty")

    resurslar = [
        ("HP ProDesk 600", "dona"),
        ("Dell Latitude 5400", "dona"),
        ("Printer Canon LBP2900", "dona"),
        ("Switch TP-Link 24 port", "dona"),
        ("Monitor LG 24inch", "dona"),
        ("Router Mikrotik hAP", "dona"),
        ("Projector Epson X05", "dona"),
        ("UPS APC 650VA", "dona"),
    ]

    xususiyatlar = [
        "Intel i5, 8GB RAM, SSD 256GB",
        "Intel i7, 16GB RAM, SSD 512GB",
        "WiFi + LAN qo‘llab-quvvatlaydi",
        "Ofis texnikasi",
        "Tarmoq qurilmasi",
    ]

    buildings = ["1-bino", "2-bino", "Bosh bino", "Laboratoriya bino"]

    created = []

    for status in Material.Status.values:
        for i in range(5):
            resurs_nomi, birlik = random.choice(resurslar)

            material = Material.objects.create(
                status=status,
                shartnoma_raqami=f"SH-{random.randint(1000,9999)}/{random.randint(2020,2025)}",
                resurs_nomi=resurs_nomi,
                ulchov_birligi=birlik,
                soni=random.randint(1, 20),
                inventor_raqami=f"INV-{random.randint(10000,99999)}",
                resurs_xususiyati=random.choice(xususiyatlar),
                mac_raqami=f"00:1A:C2:{random.randint(10,99)}:{random.randint(10,99)}:{random.randint(10,99)}",

                joylashgan_bino=random.choice(buildings),
                kafedra=random.choice(kafedralar),
                javobgar_shaxs=random.choice(users),
                foydalanuvchi_shaxs=random.choice(users),
                qabul_qilgan_javobgar_shaxs=random.choice(users),
                uzgarish_sababi=random.choice(reasons) if reasons else None,

                izoh="Test ma'lumot (seed)",
                xolati="Yaxshi",
                oxirgi_xolati=status,

                tarqatilgan_sana=timezone.now(),
                joyi_uzgarish_sana=timezone.now(),
            )

            created.append(material)

    print(f"✅ {len(created)} ta material yaratildi")
    return created