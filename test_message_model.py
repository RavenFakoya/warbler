"""Message model tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.user_id = 11111
        user = User.signup("test_user", "testuser@test.com", "password", None)
        user.id = self.user_id
        db.session.commit()

        self.user = User.query.get(self.user_id)

        self.client = app.test_client()
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    
    def test_message_model(self):
        """Test posting a message"""

        message = Message( text = "This is a warble", user_id=self.user_id)

        db.session.add(message)
        db.session.commit()

        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, "This is a warble")
    
    def test_likes(self):
        message1 = Message(text="This is a warble", user_id = self.user_id)

        message2 = Message(text="Cool test bro", user_id = self.user_id)

        user = User.signup("TestUser2", "tester2@test.com", "password", None)

        user_id = 2222
        user.id = user_id

        db.session.add_all([message1, message2, user])
        db.session.commit()

        user.likes.append(message1)

        db.session.commit()

        like = Likes.query.filter(Likes.user_id == user_id).all()
        self.assertEqual(len(like), 1)
        self.assertEqual(like[0].message_id, message1.id)