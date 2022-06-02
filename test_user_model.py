"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

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
        
        user1 = User.signup("testUser1", "test1@test.com", "password", None)
        user1_id = 1111
        user1.id = user1_id

        user2 = User.signup("testUser2", "test2@test.com", "password", None)
        user2_id = 2222
        user2.id = user2_id

        db.session.commit()

        user1 = User.query.get(user1_id)
        user2 = User.query.get(user2_id)

        self.user1 = user1
        self.user1_id = user1_id
        self.user2 = user2
        self.user2_id = user2_id

        self.client = app.test_client()
    
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res



    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    
    def test_follows(self):

        """Test if a user is following another user"""
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user1.followers), 0)
        self.assertEqual(len(self.user1.following), 1)
        
        self.assertEqual(len(self.user2.following), 0)
        self.assertEqual(len(self.user2.followers), 1)

        self.assertEqual(self.user2.followers[0].id, self.user1.id)
        self.assertEqual(self.user1.following[0].id, self.user2.id)

    def test_is_following(self):
        """Test is_following function"""

        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_followed_by(self):
        """Test is_followed_by function"""

        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))

    
    def test_signup(self):

        test_user = User.signup("testuser", "testuser@mail.com", "password", None)

        user_id = 11111
        test_user.id = user_id

        db.session.commit()

        test_user = User.query.get(user_id)
        self.assertIsNotNone(test_user)
        self.assertEqual(test_user.username, "testuser")
        self.assertEqual(test_user.email, "testuser@mail.com")
        self.assertNotEqual(test_user.password, "password")
        self.assertTrue(test_user.password.startswith("$2b$"))


    def test_invalid_username(self):
        """Test signup with invalid username"""
        
        invalid_user = User.signup(None, "test@mail.com", "password", None)
        user_id = 111111111
        invalid_user.id = user_id

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_email(self):
        """Test signup with invalid email"""

        invalid_user = User.signup("test", None, "password", None)
        user_id = 111111111
        invalid_user.id = user_id

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password(self):
        """Test signup with invalid password"""
        with self.assertRaises(ValueError) as context:
            User.signup("test", "test@mail.com", None, None)
    
        with self.assertRaises(ValueError) as context:
            User.signup("test", "test@mail.com", "", None)
    
    
    def test_valid_authentication(self):
        """Test authentication with a valid user"""
        user = User.authenticate(self.user1.username, "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user1_id)
    
    def test_wrong_username(self):
        """Test authentication with an invalid username"""
        self.assertFalse(User.authenticate("no_user", "password"))
    
    def test_wrong_password(self):
        """Test authentication with incorrect password"""
        self.assertFalse(User.authenticate(self.user1.username, "wrongpassword"))
