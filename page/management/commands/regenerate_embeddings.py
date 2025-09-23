# from django.core.management.base import BaseCommand
# from page.models import Profile
# from sentence_transformers import SentenceTransformer
# import json
# import numpy as np
#
#
# class Command(BaseCommand):
#     help = 'Regenerates embeddings for all user profiles using the correct model.'
#
#     def handle(self, *args, **kwargs):
#         self.stdout.write(self.style.WARNING('Loading the AI model (all-mpnet-base-v2)... This might take a moment.'))
#
#         # Make sure to use the correct model here!
#         model = SentenceTransformer('all-mpnet-base-v2')
#
#         self.stdout.write(self.style.SUCCESS('Model loaded. Starting to process profiles...'))
#
#         profiles = Profile.objects.all()
#         total_profiles = profiles.count()
#
#         if total_profiles == 0:
#             self.stdout.write(self.style.WARNING('No profiles found in the database.'))
#             return
#
#         for i, profile in enumerate(profiles):
#             self.stdout.write(f'Processing profile {i + 1}/{total_profiles}: {profile.user.username}')
#
#             # Combine skills text
#             combined_text = f"Skills offered: {profile.skills_offered or ''}. Skills wanted: {profile.skills_wanted or ''}."
#
#             # Generate new embedding
#             embedding = model.encode(combined_text)
#             embedding_json = json.dumps(embedding.tolist())
#
#             # Save the new embedding to the profile
#             profile.embedding = embedding_json
#             profile.save(update_fields=['embedding'])
#
#         self.stdout.write(self.style.SUCCESS('Successfully regenerated embeddings for all profiles!'))