from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer

print("Initializing SkillBot...")
skill_bot = ChatBot(
    'SkillBot',
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    database_uri='sqlite:///db.sqlite3',
    logic_adapters=[
        {
            'import_path': 'chatterbot.logic.BestMatch',
            'default_response': "I'm sorry, I can only answer questions related to the Skill Swap platform. How can I help you with that?",
            'maximum_similarity_threshold': 0.90
        }
    ]
)
print("SkillBot Initialized.")
print("Training SkillBot on general conversations...")
corpus_trainer = ChatterBotCorpusTrainer(skill_bot)
corpus_trainer.train(
    "chatterbot.corpus.english.greetings"
)

print("Training SkillBot on platform-specific topics...")
skill_swap_training_data = [

    "What is this website for?",
    "This is a skill-sharing platform where you can exchange your skills with other users for free.",
    "How does it work?",
    "You create a profile, list the skills you can offer and the skills you want to learn. Our system will help you find a match. You can then propose a swap, chat, and meet online!",
    "Is it free?",
    "Yes, using the Skill Swap platform is completely free.",

    "How do I create my profile?",
    "After signing up, go to the 'Profile' section to add your skills and other details.",
    "How does the search work?",
    "The search is automatic! Just go to the 'Search' page, and our system will find the best matches for you based on your profile.",
    "Can I update my profile?",
    "Yes, you can update your profile at any time from the 'Profile' page using the PUT method.",

    "How do I send a swap request?",
    "When you find a user you want to swap with, you can propose a session directly from their profile. You just need to select a time.",
    "How can I see my requests?",
    "You can see all your sent and received requests on the 'My Sessions' page.",
    "How do I accept a request?",
    "Go to 'My Sessions', find the request you received, and use the 'accept' option.",

    "How does the chat work?",
    "Once a swap request is accepted, a private chat room is automatically created for both users.",
    "How can I rate a user?",
    "After a session is completed, you can go to that session in 'My Sessions' and give a rating from 1 to 5 stars.",


    "Thanks",
    "You're welcome! Is there anything else I can help you with?"
]

list_trainer = ListTrainer(skill_bot)
list_trainer.train(skill_swap_training_data)

print("SkillBot training complete.")


def get_bot_response(user_message):
    response = skill_bot.get_response(user_message)
    return str(response)