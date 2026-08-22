from django.db import models
from django.contrib.auth.models import AbstractUser




class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin'
        XISOBCHI = 'xisobchi'
        QOROVUL = 'qorovul'
        OMBORCHI = 'omborchi'
        KAFEDRA = 'kafedra'
        USTA = 'usta'
        FAKULTET = 'fakultet'
        TALABA = 'talaba'

    role = models.CharField(max_length=18, choices=Role.choices, default=Role.ADMIN)
    phone_number = models.CharField(max_length=128)

    def __str__(self):
        return f"{self.username} - {self.role}"

class Fakultet(models.Model):
    name = models.CharField(max_length=128)
    foydalanuvchilar = models.ManyToManyField(CustomUser,blank=True)

    def __str__(self):
        return self.name

class Kafedra(models.Model):
    fakultet = models.ForeignKey(Fakultet, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    foydalanuvchilar = models.ManyToManyField(CustomUser,blank=True)

    def __str__(self):
        return self.name

class Change_reason(models.Model):
    reason = models.CharField(max_length=128)
    def __str__(self):
        return self.reason

    class Meta:
        verbose_name_plural = "O'zgarish sabablari"
        verbose_name = "O'zgarish sababi"

class Material(models.Model):

    class Status(models.TextChoices):
        YANGI = 'YANGI'
        BIRIKTIRILGAN = 'BIRIKTIRILGAN'
        REMONT = 'REMONT'
        XISOBDAN_CHIQARILGAN = 'XISOBDAN CHIQARILGAN'
        CHIQQAN = 'CHIQQAN'
        QAYTGAN = 'QAYTGAN'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.YANGI)
    shartnoma_raqami = models.CharField(max_length=128)
    resurs_nomi = models.CharField(max_length=128)
    ulchov_birligi = models.CharField(max_length=128)
    soni = models.IntegerField(default=0)
    inventor_raqami = models.CharField(max_length=128)
    resurs_xususiyati = models.CharField(max_length=128)
    mac_raqami = models.CharField(max_length=20,null=True,blank=True)

    joylashgan_bino = models.CharField(max_length=128,null=True,blank=True)
    kafedra = models.ForeignKey(Kafedra, on_delete=models.CASCADE,null=True,blank=True)
    javobgar_shaxs = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="javobgar_shaxs",null=True,blank=True)
    uzgarish_sababi = models.ForeignKey(Change_reason, on_delete=models.CASCADE,null=True,blank=True)
    foydalanuvchi_shaxs = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="foydalanuvchi_shaxs",null=True,blank=True)
    qabul_qilgan_javobgar_shaxs = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="qabul_qilgan_javobgar_shaxs",null=True,blank=True)
    royxatdan_chiqarish = models.CharField(max_length=128,null=True,blank=True)

    izoh = models.TextField(blank=True,null=True,)
    xolati = models.CharField(max_length=128,null=True,blank=True)
    oxirgi_xolati = models.CharField(max_length=128,null=True,blank=True)

    kirish_vaqti = models.DateTimeField(auto_now_add=True)
    tarqatilgan_sana = models.DateTimeField(null=True,blank=True)
    joyi_uzgarish_sana = models.DateTimeField(null=True,blank=True)
    royxatdan_chiqarish_sana = models.DateTimeField(null=True,blank=True)
    chiqish_vaqi = models.DateTimeField(null=True,blank=True)


    def __str__(self):
        return self.resurs_nomi

class Remont_Bolimi(models.Model):

    class Status(models.TextChoices):
        REMONT = 'REMONT'
        TAYYOR = 'TAYYOR'

    status_new = models.CharField(max_length=128, choices=Status.choices, default=Status.REMONT)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    remont_qilish_xodimi = models.CharField(max_length=128)
    remontga_berilgan_sana = models.DateTimeField(null=True,blank=True)
    remontdan_qaytgan_sana = models.DateTimeField(null=True,blank=True)
    remontdan_oldingi_xolati = models.CharField(max_length=128)
    remontdan_kiyingi_xolati = models.CharField(max_length=128)
    foydalanuvchi = models.CharField(max_length=128)

    class Meta:
        ordering = ['-id']

class Remont_Talab(models.Model):
    class Status(models.TextChoices):
        YANGI = 'YANGI'
        BEKOR_QILINGAN = 'BEKOR QILINGAN'
        TASDIQLANGAN = 'TASDIQLANGAN'

    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    talaba  = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    kafedra = models.ForeignKey(Kafedra, on_delete=models.CASCADE)
    xona = models.CharField(max_length=50)
    izoh = models.TextField()
    status = models.CharField(max_length=20,choices=Status.choices,default=Status.YANGI)

    class Meta:
        ordering = ['-id']


class MaterialHistory(models.Model):
    """
    Har bir 'berish / qaytarish / remontga yuborish' harakati shu yerda
    alohida qator sifatida saqlanadi — Material ustidagi maydonlar kabi
    ustidan yozilmaydi, shuning uchun to'liq tarix (kim, qachon, kimga)
    saqlanib qoladi.
    """

    class Action(models.TextChoices):
        BIRIKTIRISH = 'BIRIKTIRISH', "Biriktirish (berish)"
        QAYTARISH = 'QAYTARISH', "Qaytarish"
        REMONTGA_BERISH = 'REMONTGA_BERISH', "Remontga berish"
        REMONTDAN_QAYTISH = 'REMONTDAN_QAYTISH', "Remontdan qaytish"
        XISOBDAN_CHIQARISH = 'XISOBDAN_CHIQARISH', "Hisobdan chiqarish"

    material = models.ForeignKey(
        Material, on_delete=models.CASCADE, related_name='history'
    )
    action = models.CharField(max_length=30, choices=Action.choices)

    # kimdan (bo'sh bo'lishi mumkin — masalan omborchi birinchi marta bersa)
    from_user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='material_history_from'
    )
    # kimga berildi
    to_user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='material_history_to'
    )
    kafedra = models.ForeignKey(
        Kafedra, on_delete=models.SET_NULL, null=True, blank=True
    )
    xona = models.CharField(max_length=50, null=True, blank=True)

    old_status = models.CharField(max_length=30, null=True, blank=True)
    new_status = models.CharField(max_length=30, null=True, blank=True)

    izoh = models.TextField(blank=True, null=True)

    # amalni tizimda kim bajardi (masalan omborchi yoki usta akkounti)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='material_history_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Material tarixi"
        verbose_name_plural = "Material tarixi"

    def __str__(self):
        return f"{self.material.resurs_nomi} — {self.get_action_display()} ({self.created_at:%d.%m.%Y %H:%M})"