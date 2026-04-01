from django import forms
from .models import  Material


class MaterialCreateForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('shartnoma_raqami', 'resurs_nomi', 'ulchov_birligi', 'soni','inventor_raqami','resurs_xususiyati')

class MaterialTarqatishForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('mac_raqami','kafedra','joylashgan_bino','javobgar_shaxs','tarqatilgan_sana')