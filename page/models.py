from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    skills_offered = models.TextField(blank=True, null=True)

    skills_wanted = models.TextField(blank=True, null=True)

    available_hours = models.TextField(blank=True, null=True)

    average_rating = models.FloatField(default=0.0)

    rating_count = models.IntegerField(default=0)

    def _str_(self):
        return f"{self.user.username}'s Profile"

class SwapSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    proposer = models.ForeignKey(User, related_name='proposed_sessions', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_sessions', on_delete=models.CASCADE)
    proposer_skill = models.CharField(max_length=255)
    receiver_skill = models.CharField(max_length=255)
    session_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    #meeting_link = models.URLField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Swap from {self.proposer.username} to {self.receiver.username} is {self.status}"

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Rating(models.Model):
    swap_session = models.ForeignKey(SwapSession, on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])



    class Meta:
        unique_together = ('swap_session', 'rater')

    def __str__(self):
        return f"Rating by {self.rater.username} for {self.rated_user.username} on session {self.swap_session.id}"