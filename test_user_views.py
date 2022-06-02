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

