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
from service import talisman # Importar Talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
# T E S T C A S E S
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
        init_db(app)
        talisman.force_https = False # Desactivar forzamiento HTTPS para las pruebas

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
    # H E L P E R M E T H O D S
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
    # A C C O U N T T E S T C A S E S
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
    
    def test_security_headers(self):
        """Should return security headers"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)

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
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # T E S T R E A D A C C O U N T
    
    def test_get_account(self):
        """It should Read a single Account"""
        # Crea una cuenta y la guarda usando el helper para obtener un ID válido
        account = self._create_accounts(1)[0]
        resp = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], account.name)

    def test_get_account_not_found(self):
        """It should not Read an Account that is not found"""
        resp = self.client.get(f"{BASE_URL}/0") # El ID 0 nunca debería existir
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    #
    # T E S T L I S T A C C O U N T S
    #

    def test_list_accounts(self):
        """It should Get a list of Accounts"""
        count = 5
        self._create_accounts(count)
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), count)
        
    #
    # T E S T U P D A T E A C C O U N T
    #

    def test_update_account(self):
        """It should Update an existing Account"""
        # 1. Crear una cuenta base
        test_account = self._create_accounts(1)[0]
        original_id = test_account.id

        # 2. Definir los nuevos datos
        new_phone = "555-555-1212"
        test_account.phone_number = new_phone
        new_name = "Gandalf The Gray"
        test_account.name = new_name
        
        # 3. Llamar al endpoint PUT
        resp = self.client.put(
            f"{BASE_URL}/{test_account.id}",
            json=test_account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 4. Verificar que los datos de la respuesta son correctos
        updated_account = resp.get_json()
        self.assertEqual(updated_account["name"], new_name)
        self.assertEqual(updated_account["phone_number"], new_phone)
        self.assertEqual(updated_account["id"], original_id) # El ID no debe cambiar

        # 5. Verificar que el cambio se haya guardado en la BD (usando GET)
        resp = self.client.get(f"{BASE_URL}/{test_account.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], new_name)

    def test_update_account_not_found(self):
        """It should not Update an Account that is not found"""
        account = AccountFactory()
        resp = self.client.put(
            f"{BASE_URL}/0", # ID que no existe
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_account_unsupported_media_type(self):
        """It should not Update an Account when sending the wrong media type"""
        # El test debe fallar con 415 si el tipo de contenido no es JSON
        resp = self.client.put(f"{BASE_URL}/1", data="<xml>data</xml>", content_type="application/xml")
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
