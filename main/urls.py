from django.urls import path
from .views import home_page, bulim_view, hisobchi_view, kafedra_view, omborchi_view, qorovul_view, \
    remont_bolimi_view, export_model_to_excel, search, add_material_view, tarqatish_material_view, tasdiqlash, \
    bekor_qilish, ariza_create,resource_pdf

urlpatterns = [
    path('', home_page, name='home'),
    path('bulim/', bulim_view, name='bulim'),
    path('hisobchi/', hisobchi_view, name='xisobchi'),
    path('qorovul/', qorovul_view, name='qorovul'),
    path('omborchi/', omborchi_view, name='omborchi'),
    path("ariza_create/", ariza_create, name="talaba"),
    path('malumot-kiritish/', add_material_view, name='add_material_view'),
    path('malumot-tarqatish/', tarqatish_material_view, name='tarqatish_material'),
    path('kafedra/', kafedra_view, name='kafedra'),
    path("remont_bolimi/", remont_bolimi_view, name="usta"),
    path("fakultet/", bulim_view, name="fakultet"),
    path('search/', search, name='search'),
    path(
        "export/<str:app_name>/<str:model_name>/",
        export_model_to_excel,
        name="export_model_excel",
    ),
    path('remont/bekor/<int:pk>/', bekor_qilish, name='remont_bekor_qilish'),
    path('remont/tasdiq/<int:pk>/', tasdiqlash, name='remont_tasdiqlash'),
    path('pdf/', resource_pdf, name='pdf'),


]
