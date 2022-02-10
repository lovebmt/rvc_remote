from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # index myboard page
    path('<int:room_name>/<int:board_id>/', views.room, name='room'),  # lab PC
    path('api/status/boards/share/', views.GetShareBoardsAPI.as_view(), name = "board_status"),  # shared board for anonymous
    path('api/control/boards/share/', views.SetControlBoardAPI.as_view()),  # control board
    path('api/token/', views.GetTokenAPI.as_view()),  # get user token
]

