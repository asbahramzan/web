from .models import Rating


@receiver(post_save, sender=Rating)
def update_average_rating(sender, instance, created, **kwargs):
    if created:
        rated_user_profile = instance.rated_user.profile

        new_average = Rating.objects.filter(rated_user=instance.rated_user).aggregate(Avg('score'))['score__avg']

        rating_count = Rating.objects.filter(rated_user=instance.rated_user).count()

        rated_user_profile.average_rating = new_average
        rated_user_profile.rating_count = rating_count
        rated_user_profile.save()