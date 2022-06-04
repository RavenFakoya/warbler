"""User View tests."""


# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py
import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

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

class UserViewTestCase(TestCase):

    """Test views for users"""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()
        
        self.client = app.test_client()

        self.testuser = User.signup(username="testUser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        self.testuser_id = 8765
        self.testuser.id = self.testuser_id

        self.user1 = User.signup("testUser1", "test1@test.com", "password", None)
        self.user1_id = 1111
        self.user1.id = self.user1_id

        self.user2 = User.signup("testUser2", "test2@test.com", "password", None)
        self.user2_id = 2222
        self.user2.id = self.user2_id

        self.user3 = User.signup("User3", "test3@test.com", "password", None)
        self.user4 = User.signup("User4", "test4@test.com", "password", None)
        
        db.session.commit()
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_index(self):
        """Test show user index"""
        with self.client as client:
            resp = client.get("/users")

            self.assertIn("@testUser", str(resp.data))
            self.assertIn("@testUser1", str(resp.data))
            self.assertIn("@testUser2", str(resp.data))
            self.assertIn("@User3", str(resp.data))
            self.assertIn("@User4", str(resp.data))

    def test_user_search(self):
        """Test searching for a user"""
        with self.client as client:
            resp = client.get("/users?q=test")

            self.assertIn("@testUser", str(resp.data))
            self.assertIn("@testUser1", str(resp.data))
            self.assertIn("@testUser2", str(resp.data))

            self.assertNotIn("@User3", str(resp.data))
            self.assertNotIn("@User4", str(resp.data))
            
    def test_user_show(self):
        """Test showing user homepage"""

        with self.client as client:
            resp = client.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testUser", str(resp.data))

    def likes(self):

        """Add likes to users for test"""
       
        message1 = Message(text="test1", user_id=self.testuser_id)
        message2 = Message(text="test2", user_id = self.user2_id)
        message3 = Message(id = 444 ,text="test3", user_id = self.user2_id)

        db.session.add_all([message1, message2, message3])
        db.session.commit()

        like = Likes(user_id=self.testuser_id, message_id = 444)

        db.session.add(like)
        db.session.commit()
    
    def test_show_likes(self):
        """Test user homepage with likes"""

        with self.client as client:

            resp = client.get(f"/users/{self.testuser_id}")
            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testUser", str(resp.data))
            self.assertIn("1", str(resp.data))

    
    def test_add_likes(self):
        """Test adding likes"""

        message = Message(id=777, text="test message", user_id= self.user2_id)
        db.session.add(message)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id

            
            resp = client.post("/messages/777/like", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==777).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)


    def test_unlike(self):
        """Test unliking a message"""

        self.likes()

        message = Message.query.filter(Message.text == "test3").one()
        self.assertIsNotNone(message)
        self.assertNotEqual(message.user_id, self.testuser_id)

        like = Likes.query.filter(Likes.user_id == self.testuser_id and Likes.message_id == message.id).one()

        self.assertIsNotNone(like)

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id

            resp = client.post(f"/messages/{message.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id == message.id).all()

            self.assertEqual(len(likes), 0)
    
    def test_unauthenticated_likes(self):
        """Test liking a message if a user is not authenticted """
        self.likes()

        message = Message.query.filter(Message.text == "test3").one()
        self.assertIsNotNone(message)

        like_count = Likes.query.count()

        with self.client as client:
            resp = client.post(f"/messages/{message.id}/like", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            
            self.assertIn("Access unauthorized", str(resp.data))

            self.assertEqual(like_count, Likes.query.count())
        
    def followers(self):
        """Set up followers for tests"""

        follow1 = Follows(user_being_followed_id = self.user1_id, user_following_id = self.testuser_id)
        follow2 = Follows(user_being_followed_id = self.user2_id, user_following_id = self.testuser_id)
        follow3 = Follows(user_being_followed_id = self.testuser_id, user_following_id = self.user1_id)

        db.session.add_all([follow1, follow2, follow3])
        db.session.commit()

    
    def test_user_show_with_followers(self):
        """Test user homepage with followers"""

        self.followers()
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id
            
            resp = client.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testUser", str(resp.data))
            self.assertIn("2", str(resp.data))

    def test_show_following(self):
        """Test user_following view function"""

        self.followers()
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id
            
            resp = client.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testUser1", str(resp.data))
            self.assertIn("@testUser2", str(resp.data))
            self.assertNotIn("@User3", str(resp.data))
            self.assertNotIn("@User4", str(resp.data))
        
    def test_show_followers(self):
        """Test user_follower view function"""

        self.followers()
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id

            resp = client.get(f"/users/{self.testuser_id}/followers")

            self.assertIn("@testUser1", str(resp.data))
            self.assertNotIn("@testUser2", str(resp.data))
            self.assertNotIn("@User3", str(resp.data))
            self.assertNotIn("@User4", str(resp.data))
    
    def test_unathorize_following(self):
        """Test access to following page when user is not signed in"""

        self.followers()
        with self.client as client:

            resp = client.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
    
    def test_uanthorized_followers(self):
        """Test access to followers page when not signed in"""

        self.followers()
        with self.client as client:
            resp = client.get(f"/users/{self.testuser_id}/followers", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


