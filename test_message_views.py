"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        self.testuser_id = 1111
        self.testuser.id = self.testuser_id

        db.session.commit()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_message_no_login(self):
        """Test if a message can be posted when you are not signed in"""

        with self.client as client:
            resp = client.post("/messages/new", data={"text": "Hello"}, follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
    
    def test_message_invalid_user(self):
        """Test if a message can be added if a user does not exist"""

        with self.client as client:
            with client.session_transaction() as session:
                    session[CURR_USER_KEY] = 11111111111 
                
            resp = client.post("messages/new", data={"text":"Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
    
    def test_get_message(self):
        """Test posting a message"""
        message = Message(id= 11122, text = "a warbler", user_id = self.testuser_id)

        db.session.add(message)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id
            
            message = Message.query.get_or_404(11122)
            
            resp = client.get(f"/messages/{message.id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn(message.text, str(resp.data))
        
    
    def test_delete_message(self):
        """Test deleting a message"""
        message = Message(id=12345, text = "delete me", user_id=self.testuser_id)

        db.session.add(message)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id
                
            resp = client.post("/messages/12345/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            
            message = Message.query.get(12345)
            self.assertIsNone(message)
    
    def test_delete_message_unauthorized(self):
        """Test deleting message if yhe user is unauthorized"""

        user = User.signup(username="test3", email="test3@test.com", password="password123", image_url=None)
        user.id = 54321

        message = Message(id=12345, text="You can't delete me", user_id = self.testuser_id)
        
        db.session.add_all([user, message])
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = 54321

            resp = client.post("/messages/12345/delete", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            message = Message.query.get(12345)
            self.assertIsNotNone(message)
        
    
    def test_delete_message_no_authentication(self):

        message = Message(id=12345, text="test warbler", user_id = self.testuser_id)
        db.session.add(message)
        db.session.commit()

        with self.client as client:
            resp = client.post("/messages/12345/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            message = Message.query.get(12345)
            self.assertIsNotNone(message)
    
    def test_user_show(self):
        """Test showing user homepage"""

        with self.client as client:
            resp = client.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testUser", str(resp.data))