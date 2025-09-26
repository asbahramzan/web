from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, ProfileSerializer, SwapSessionSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .serializers import EmailLoginSerializer
from django.contrib.auth import authenticate
from .models import Profile, SwapSession, Rating
from rest_framework import status
from datetime import timedelta
from .google_meet_service import create_google_meet_event
import random
from django.core.mail import send_mail
from django.core.cache import cache
from django.conf import settings
from .models import Conversation
from django.shortcuts import render
from django.db.models import Q
from fuzzywuzzy import fuzz
from .serializers import RatingSerializer
import uuid
class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.validated_data
            email = user_data['email']

            otp = random.randint(100000, 999999)
            verification_key = str(uuid.uuid4())

            cache.set(verification_key, {'otp': otp, 'user_data': user_data}, timeout=300)

            subject = 'Your Skill Swap Registration OTP'
            message = f'Your OTP for registration is: {otp}'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]
            send_mail(subject, message, from_email, recipient_list)

            return Response({
                "message": f"OTP has been sent to {email}",
                "verification_key": verification_key
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPAndRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        verification_key = request.data.get('verification_key')
        otp_entered = request.data.get('otp')

        if not verification_key or not otp_entered:
            return Response({"error": "Verification key and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        cached_data = cache.get(verification_key)
        if not cached_data:
            return Response({"error": "OTP expired or invalid key."}, status=status.HTTP_400_BAD_REQUEST)

        if str(cached_data['otp']) == str(otp_entered):
            user_data = cached_data['user_data']

            username = user_data['email'].split('@')[0]
            full_name = user_data.get('full_name', '').split()
            first_name = full_name[0] if full_name else ''
            last_name = ' '.join(full_name[1:]) if len(full_name) > 1 else ''

            if User.objects.filter(username=username).exists():
                username = f"{username}_{random.randint(100, 999)}"

            user = User.objects.create_user(
                username=username,
                email=user_data['email'],
                password=user_data['password'],
                first_name=first_name,
                last_name=last_name
            )

            cache.delete(verification_key)

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'User registered successfully!'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)


# --- Profile and User Info Views ---

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        response_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        }
        return Response(response_data)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request):
        try:
            return Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return None

    def get(self, request):
        profile = self.get_object(request)
        if profile is None:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def post(self, request):
        if Profile.objects.filter(user=request.user).exists():
            return Response({"error": "Profile already exists"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        profile = self.get_object(request)
        if profile is None:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        profile = self.get_object(request)
        if profile is None:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

        profile.delete()
        return Response({"message": "Profile deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


##-------------LOGIN---------

class EmailLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None

            if user and user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })

            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- Search and Swap Session Views ---

class SearchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            user_profile = Profile.objects.get(user=request.user)
            user_skills_offered = user_profile.skills_offered or ''
            user_skills_wanted = user_profile.skills_wanted or ''
        except Profile.DoesNotExist:
            return Response({"error": "Please create your profile first."}, status=status.HTTP_404_NOT_FOUND)

        other_profiles = Profile.objects.exclude(user=request.user)

        if not other_profiles:
            return Response({"message": "No other profiles to compare with."}, status=status.HTTP_200_OK)

        results = []
        for profile in other_profiles:
            score1 = fuzz.token_set_ratio(user_skills_offered, profile.skills_wanted or '')

            score2 = fuzz.token_set_ratio(user_skills_wanted, profile.skills_offered or '')

            if score1 > 60 and score2 > 60:

                match_score = (score1 + score2) / 2
                results.append({'profile': profile, 'match_score': match_score})

        sorted_results = sorted(results, key=lambda x: x['match_score'], reverse=True)

        top_profiles = [res['profile'] for res in sorted_results]

        if not top_profiles:
            return Response({"message": "No good matches found."}, status=status.HTTP_200_OK)

        serializer = ProfileSerializer(top_profiles, many=True)

        return Response(serializer.data)

class ProposeSwapView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        receiver_id = request.data.get('receiver_id')
        session_time = request.data.get('session_time')

        if not receiver_id or not session_time:
            return Response({"error": "Receiver ID and session time are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            proposer_user = request.user
            receiver_user = User.objects.get(id=receiver_id)

            proposer_profile = Profile.objects.get(user=proposer_user)
            receiver_profile = Profile.objects.get(user=receiver_user)

            proposer_skill = proposer_profile.skills_offered
            receiver_skill = receiver_profile.skills_wanted

            session = SwapSession.objects.create(
                proposer=proposer_user,
                receiver=receiver_user,
                proposer_skill=proposer_skill,
                receiver_skill=receiver_skill,
                session_time=session_time
            )
            serializer = SwapSessionSerializer(session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except (User.DoesNotExist, Profile.DoesNotExist):
            return Response({"error": "Invalid user or profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        ####
class MySessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = SwapSession.objects.filter(
            Q(proposer=request.user) | Q(receiver=request.user)
        )
        serializer = SwapSessionSerializer(sessions, many=True)
        return Response(serializer.data)


class RespondToSwapView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, session_id):
        try:
            session = SwapSession.objects.get(id=session_id, receiver=request.user)
        except SwapSession.DoesNotExist:
            return Response({"error": "Session not found or you are not the receiver."},
                            status=status.HTTP_4_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status not in ['accepted', 'rejected']:
            return Response({"error": "Invalid status. Must be 'accepted' or 'rejected'."},
                            status=status.HTTP_400_BAD_REQUEST)

        session.status = new_status
        session.save()

        conversation_id = None
        if new_status == 'accepted':
            proposer = session.proposer
            receiver = request.user

            conversation = Conversation.objects.filter(participants=proposer).filter(participants=receiver).first()
            if not conversation:
                conversation = Conversation.objects.create()
                conversation.participants.add(proposer, receiver)

            conversation_id = conversation.id
            #goole meet

        serializer = SwapSessionSerializer(session)
        response_data = serializer.data
        response_data['conversation_id'] = conversation_id

        return Response(response_data)

class ConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if request.user not in conversation.participants.all():
                return Response({"error": "Not a participant"}, status=status.HTTP_403_FORBIDDEN)

            messages = conversation.messages.order_by('timestamp')
            data = [{'sender': msg.sender.username, 'text': msg.text, 'timestamp': msg.timestamp} for msg in messages]
            return Response(data)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)


class RateSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, session_id):
        try:
            session = SwapSession.objects.get(id=session_id)
        except SwapSession.DoesNotExist:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        if session.status != 'accepted':
            return Response({"error": "You can only rate accepted sessions."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if user != session.proposer and user != session.receiver:
            return Response({"error": "You are not a participant of this session."}, status=status.HTTP_403_FORBIDDEN)

        if user == session.proposer:
            rated_user = session.receiver
        else:
            rated_user = session.proposer

        serializer = RatingSerializer(data=request.data)
        if serializer.is_valid():
            if Rating.objects.filter(swap_session=session, rater=user).exists():
                return Response({"error": "You have already rated this session."}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(
                swap_session=session,
                rater=user,
                rated_user=rated_user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def bot_chat_room(request):
    return
