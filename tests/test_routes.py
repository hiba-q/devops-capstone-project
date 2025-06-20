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
from service import talisman
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        talisman.force_https = False    # to disable https for tests
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...

    def test_read_an_account(self):
        """It should Read a single Account"""
        # Create an account
        account_data = AccountFactory()
        create_response = \
            self.client.post(BASE_URL, json=account_data.serialize())
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        new_account_json = create_response.get_json()
        account_id = new_account_json["id"]

        # Make a GET request to read the account
        response = self.client.get(
            f"{BASE_URL}/{account_id}", content_type="application/json"
        )

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_data = response.get_json()

        # Compare the returned data with the original data sent
        self.assertEqual(returned_data["id"], account_id)
        self.assertEqual(returned_data["name"], account_data.name)
        self.assertEqual(returned_data["email"], account_data.email)
        self.assertEqual(returned_data["address"], account_data.address)
        self.assertEqual
        (returned_data["phone_number"], account_data.phone_number)
        self.assertEqual
        (str(returned_data["date_joined"]), str(account_data.date_joined))

    def test_get_account_not_found(self):
        """It should not Read an Account that is not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_account(self):
        """It should Update an existing Account"""
        # Create an account to update
        account = self._create_accounts(1)[0]
        self.assertIsNotNone(account.id)

        # Update the account's name
        new_name = "New Account Name"
        account.name = new_name

        # Make the PUT request with the updated data
        response = self.client.put(
            f"{BASE_URL}/{account.id}",
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_account_not_found(self):
        """It should return 404 when updating an Account that does not exist"""
        non_existent_id = 999999

        update_data = {
            "name": "NonExistent Account Update",
            "email": "update@example.com",
            "address": "123 Main St",
            "phone_number": "555-123-4567",
            "date_joined": "2023-01-01"
        }

        # Make the PUT request with the updated data
        response = self.client.put(
            f"{BASE_URL}/{non_existent_id}",
            json=update_data,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account(self):
        """It should Delete an Account"""
        # Create an account to delete
        account = self._create_accounts(1)[0]
        # Assert that the account exists before deletion
        response = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Make the DELETE request
        response = self.client.delete(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(       # No content in 204 response
            len(response.data), 0)

        # Verify that the account is no longer found
        response = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account_not_found(self):
        """It should return 204 when deleting an Account that does not exist"""
        non_existent_id = 999999

        # Make the DELETE request
        response = self.client.delete(f"{BASE_URL}/{non_existent_id}")

        # Assersions
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(       # No content in 204 response
            len(response.data), 0)

    def test_list_all_accounts(self):
        """It should List all Accounts"""
        # Create 3 accounts
        accounts = self._create_accounts(3)
        self.assertEqual(len(accounts), 3)

        # Make a GET request to list all accounts
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get the response JSON and verify the count
        data = response.get_json()
        self.assertEqual(len(data), 3)

        # Verify that the names of the created accounts are in the list
        found_names = [account_data["name"] for account_data in data]
        for account in accounts:
            self.assertIn(account.name, found_names)

    def test_list_no_accounts(self):
        """It should return an empty list when no Accounts exist"""
        # Ensure no accounts are present initially
        db.session.query(Account).delete()
        db.session.commit()

        # Make a GET request to list all accounts
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the returned data is an empty list
        data = response.get_json()
        self.assertEqual(len(data), 0)
        self.assertEqual(data, [])

    def test_method_not_allowed(self):
        """It should not allow an unsupported HTTP method on an endpoint"""

        # Attempt to POST to a GET-only endpoint
        response = self.client.post("/health", json={})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try PUT on the /accounts collection endpoint
        response = self.client.put(BASE_URL, json={})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_security_headers(self):
        """It should return security headers"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy':
                'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)

    def test_cors_security(self):
        """It should return a CORS header"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check for the CORS header
        self.assertEqual(
            response.headers.get('Access-Control-Allow-Origin'), '*')
