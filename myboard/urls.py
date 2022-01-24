from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # index myboard page
    path('boards', views.boards, name='boards'),  # index myboard page
    path('<int:room_name>/<int:board_id>/', views.room, name='room'),  # lab PC
    path('api/status/boards/share/', views.GetShareBoardsAPI.as_view(), name = "board_status"),  # shared board for anonymous
    path('api/status/boards/', views.GetBoardsAPI.as_view()),  
    path('api/control/boards/share/', views.SetControlBoardByBoardIDAPI.as_view()),  # control board
    path('api/control/boards/share/lock/', views.SetLockBoardAPI.as_view()),  # set lock board
    path('api/control/boards/share/unlock/', views.SetUnlockBoardAPI.as_view()),  # set unlock board
    path('api/token/', views.GetTokenAPI.as_view()),  # get user token
]

