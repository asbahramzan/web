from django.urls import path
from .views import RequestOTPView, VerifyOTPAndRegisterView, EmailLoginView, ProfileView, UserProfileView, SearchView, ProposeSwapView, MySessionsView, RespondToSwapView
from .views import ConversationView
from .views import RateSessionView
from .views import bot_chat_room
urlpatterns = [
    #path('register/', RegisterView.as_view(), name='register'),
    path('signup/request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('signup/verify-otp/', VerifyOTPAndRegisterView.as_view(), name='verify-otp'),
    path( 'login/', EmailLoginView.as_view(),name='email_login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('user-profile/', UserProfileView.as_view(), name='user-profile'),
    path('search/', SearchView.as_view(), name='search'),
    path('sessions/propose/', ProposeSwapView.as_view(), name='propose-swap'),
    path('sessions/my-sessions/', MySessionsView.as_view(), name='my-sessions'),
    path('sessions/respond/<int:session_id>/', RespondToSwapView.as_view(), name='respond-swap'),
    path('chat/start/', ConversationView.as_view(), name='start-conversation'),
    path('chat/history/<int:conversation_id>/', ConversationView.as_view(), name='chat-history'),
    path('sessions/<int:session_id>/rate/', RateSessionView.as_view(), name='rate-session'),
    path('bot-chat/', bot_chat_room, name='bot-chat-room'),
]


