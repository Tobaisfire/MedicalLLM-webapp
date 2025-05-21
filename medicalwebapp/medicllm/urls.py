from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/process_patient", views.process_patient_api, name="process_patient_api"),
    path("api/chats", views.chats_api, name="chats_api"),
    path("api/messages", views.messages_api, name="messages_api"),
    path("api/report/<str:chat_id>/view", views.view_patient_report, name="view_patient_report"),
    path("api/report/<str:chat_id>/download", views.download_patient_report_pdf, name="download_patient_report_pdf"),
    path('api/report/<str:chat_id>/figure', views.view_saved_figure, name='view_saved_figure')
]

