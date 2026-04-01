from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Material, Remont_Bolimi, Fakultet, Kafedra, Change_reason,Remont_Talab


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    fieldsets = UserAdmin.fieldsets + (
        ("Custom fields", {
            "fields": ("role", "phone_number"),
        }),
    )


admin.site.register(Material)
admin.site.register(Remont_Bolimi)
admin.site.register(Fakultet)
admin.site.register(Kafedra)
admin.site.register(Change_reason)
admin.site.register(Remont_Talab)
