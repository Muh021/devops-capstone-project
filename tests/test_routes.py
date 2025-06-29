"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase

from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/accounts"
HTTPS_ENVIRON = {"wsgi.url_scheme": "https"}


class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

        # Disable HTTPS enforcement in tests
        tal = getattr(app, "talisman", None)
        if tal:
            tal.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once after all tests"""
        pass

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        """Runs after each test"""
        db.session.remove()

    def _create_accounts(self, count):
        """Factory method to create multiple accounts"""
        accounts = []
        for _ in range(count):
            acct = AccountFactory()
            resp = self.client.post(BASE_URL, json=acct.serialize())
            self.assertEqual(
                resp.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new = resp.get_json()
            acct.id = new["id"]
            accounts.append(acct)
        return accounts

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        acct = AccountFactory()
        resp = self.client.post(
            BASE_URL,
            json=acct.serialize(),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Location header must be set
        self.assertIsNotNone(resp.headers.get("Location"))
        new = resp.get_json()
        self.assertEqual(new["name"], acct.name)
        self.assertEqual(new["email"], acct.email)
        self.assertEqual(new["address"], acct.address)
        self.assertEqual(new["phone_number"], acct.phone_number)
        self.assertEqual(new["date_joined"], str(acct.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        resp = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        acct = AccountFactory()
        resp = self.client.post(
            BASE_URL,
            json=acct.serialize(),
            content_type="test/html",
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_account(self):
        """It should Read a single Account"""
        acct = self._create_accounts(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{acct.id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], acct.name)

    def test_get_account_not_found(self):
        """It should not Read an Account that is not found"""
        resp = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_account_list(self):
        """It should List all Accounts"""
        self._create_accounts(5)
        resp = self.client.get(BASE_URL, content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    def test_list_accounts_empty(self):
        """It should return [] when no accounts exist"""
        resp = self.client.get(BASE_URL, content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json(), [])

    def test_update_account(self):
        """It should Update an existing Account"""
        acct = self._create_accounts(1)[0]
        payload = acct.serialize()
        payload["name"] = "UpdatedName"
        resp = self.client.put(
            f"{BASE_URL}/{acct.id}",
            json=payload,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        updated = resp.get_json()
        self.assertEqual(updated["name"], "UpdatedName")

    def test_update_account_not_found(self):
        """It should not Update a non-existent Account"""
        resp = self.client.put(
            f"{BASE_URL}/0",
            json={"name": "X"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account(self):
        """It should Delete an Account"""
        acct = self._create_accounts(1)[0]
        resp = self.client.delete(f"{BASE_URL}/{acct.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        # Verify it’s really gone
        resp2 = self.client.get(f"{BASE_URL}/{acct.id}")
        self.assertEqual(resp2.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account_not_found(self):
        """It should not Delete a non-existent Account"""
        resp = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_security_headers(self):
        """It should return security headers when served over HTTPS"""
        resp = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected = {
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'self'; object-src 'none'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        for header, val in expected.items():
            self.assertEqual(resp.headers.get(header), val)
