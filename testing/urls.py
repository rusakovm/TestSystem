
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.device_list, name="device_list"),
    path("testing/", views.test_session, name="test_session"),
    path("testing/start/", views.start_testing, name="start_testing"),
    path("testing/plan/", views.plan_settings, name="plan_settings"),
    path("testing/plan/add-test/",views.add_plan_test,name="add_plan_test"),
    path("testing/plan/delete-test/",views.delete_plan_test,name="delete_plan_test"),
    path("testing/plan/add-phase/",views.add_plan_phase,name="add_plan_phase"),
    path("testing/plan/delete-phase/",views.delete_plan_phase,name="delete_plan_phase"),
    path("testing/plan/reorder-phases/",views.reorder_phases,name="reorder_phases"),
    path("testing/plan/reorder-tests/",views.reorder_tests,name="reorder_tests"),
    path("testing/update-status/",views.update_test_status,name="update_test_status"),
    path("devices/add/", views.add_device, name="add_device"),
    path("devices/", views.device_list, name="devices"),
    path("history/", views.history, name="history"),
    path("models/", views.models_page, name="models_page"),
    path("settings/", views.settings_page, name="settings_page"),
    path("models/add/", views.add_device_model, name="add_device_model"),
    path("history/<int:session_id>/", views.history_detail, name="history_detail"),
    path("login/",auth_views.LoginView.as_view(template_name="testing/login.html"),name="login"),
    path("logout/",auth_views.LogoutView.as_view(),name="logout"),
]
