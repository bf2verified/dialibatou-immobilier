#!/usr/bin/env python3
"""
Backend API Testing for DIALIBATOU BTP IMMOBILIER
Tests tous les endpoints de l'API FastAPI + PostgreSQL (dialibatou-backend/)

Prerequis :
    cd dialibatou-backend && uvicorn main:app --reload --port 8001
Puis, a la racine du depot :
    python backend_test.py

Identifiants admin : lus depuis dialibatou-backend/.env (fichier NON versionne)
ou depuis la variable d'environnement ADMIN_PASSWORD. Aucun secret dans le code.
"""

import io
import os
import sys
import json
from pathlib import Path

import requests

# Identifiants admin : lus depuis l'environnement, sinon depuis
# dialibatou-backend/.env (fichier NON versionne). Aucun secret dans le code.
ROOT = Path(__file__).resolve().parent
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def _load_password_from_env_file() -> str:
    env_file = ROOT / "dialibatou-backend" / ".env"
    if not env_file.exists():
        return ""
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("ADMIN_PASSWORD="):
            return line.split("=", 1)[1].strip()
    return ""


if not ADMIN_PASSWORD:
    ADMIN_PASSWORD = _load_password_from_env_file()

# Les emojis du rapport plantent sur la sortie redirigee (cp1252 sous Windows) :
# on force l'UTF-8 pour que `python backend_test.py > log.txt` fonctionne aussi.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # Python < 3.7
    pass

# Nombre MINIMUM de proprietes attendues en base (seed : 60, seuil dynamique : >= 13)
MIN_PROPERTIES = 13
MIN_LOTS = 1
BASE_URL = "http://localhost:8001"

# 1x1 pixel PNG valide pour les tests d'upload
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6360000002000100ffff03000006000557bfabd400"
    "00000049454e44ae426082"
)


class BackendAPITester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.issues = []
        self.token = None  # JWT admin

    def log_issue(self, endpoint, issue, severity="MEDIUM"):
        """Log an issue found during testing"""
        self.issues.append({
            "endpoint": endpoint,
            "issue": issue,
            "severity": severity
        })

    def _headers(self, with_auth=False):
        headers = {'Content-Type': 'application/json'}
        if with_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        if headers is None:
            headers = self._headers()

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                print(f"❌ Unsupported method: {method}")
                return False, {}

            print(f"   Status: {response.status_code}")
            success = response.status_code == expected_status

            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except json.JSONDecodeError:
                    return success, {"text": response.text}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except Exception:
                    print(f"   Error: {response.text[:300]}")
                self.log_issue(endpoint, f"Expected {expected_status}, got {response.status_code}", "HIGH")
                return False, {}

        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {str(e)}")
            self.log_issue(endpoint, f"Connection error: {str(e)}", "CRITICAL")
            return False, {}
        except requests.exceptions.Timeout:
            print("❌ Timeout Error")
            self.log_issue(endpoint, "Timeout", "HIGH")
            return False, {}
        except Exception as e:
            print(f"❌ Unexpected Error: {str(e)}")
            self.log_issue(endpoint, f"Unexpected error: {str(e)}", "HIGH")
            return False, {}

    def run_upload_test(self, name, endpoint, filename, content, content_type,
                        with_auth=True, expected_status=200):
        """Test d'upload multipart/form-data (image ou video)"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        if with_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url} (fichier: {filename}, {len(content)} octets)")

        try:
            files = {'file': (filename, io.BytesIO(content), content_type)}
            response = requests.post(url, files=files, headers=headers, timeout=30)
            print(f"   Status: {response.status_code}")
            if response.status_code == expected_status:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except Exception:
                    return True, {}
            print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
            try:
                print(f"   Error: {response.json()}")
            except Exception:
                print(f"   Error: {response.text[:300]}")
            self.log_issue(endpoint, f"Upload failed: expected {expected_status}, "
                                     f"got {response.status_code}", "HIGH")
            return False, {}
        except Exception as e:
            print(f"❌ Unexpected Error: {str(e)}")
            self.log_issue(endpoint, f"Upload error: {str(e)}", "HIGH")
            return False, {}

    # ================= TESTS INDIVIDUELS =================

    def test_health_check(self):
        """Test health endpoint + message clair si le backend ne tourne pas"""
        success, response = self.run_test(
            "Health Check", "GET", "/api/health", 200
        )
        if success and 'status' in response:
            print(f"   Health status: {response.get('status')}")
        elif not success:
            print("\n⚠️  Le backend ne repond PAS sur http://localhost:8001")
            print("   Demarrage : cd dialibatou-backend && "
                  "venv\\Scripts\\activate && uvicorn main:app --reload --port 8001")
        return success

    def test_login(self):
        """POST /api/auth/login -> JWT admin (obligatoire pour les ecritures)"""
        if not ADMIN_PASSWORD:
            print("⚠️  ADMIN_PASSWORD introuvable : definissez-le dans "
                  "dialibatou-backend/.env (non versionne) ou en variable d'environnement")
            self.log_issue("/api/auth/login", "ADMIN_PASSWORD non configure", "HIGH")
            return False
        success, response = self.run_test(
            "Login Admin (JWT)", "POST", "/api/auth/login", 200,
            data={"username": ADMIN_USER, "password": ADMIN_PASSWORD}
        )
        if success and response.get('access_token'):
            self.token = response['access_token']
            print(f"   JWT recu pour {response.get('username')} "
                  f"({len(self.token)} caracteres)")
            return True
        print("❌ Pas de JWT — les tests d'ecriture vont echouer")
        self.log_issue("/api/auth/login", "Pas de jeton JWT recu", "CRITICAL")
        return False

    def test_get_properties(self):
        """GET /api/properties — comptage DYNAMIQUE (>= MIN_PROPERTIES)"""
        success, response = self.run_test(
            "Get All Properties", "GET", "/api/properties", 200
        )
        if success and isinstance(response, list):
            count = len(response)
            print(f"   Found {count} properties (seuil dynamique : >={MIN_PROPERTIES})")
            if count >= MIN_PROPERTIES:
                print(f"✅ Property count OK : {count} >= {MIN_PROPERTIES}")
            else:
                print(f"❌ Trop peu de proprietes : {count} < {MIN_PROPERTIES} "
                      f"(lancez : python seed.py)")
                self.log_issue("/api/properties",
                               f"Seulement {count} proprietes (attendu >={MIN_PROPERTIES})",
                               "HIGH")
            if response:
                prop = response[0]
                required_fields = ['id', 'ti', 'tr', 'pr', 'nb', 'ty', 'su']
                missing_fields = [f for f in required_fields if f not in prop]
                if missing_fields:
                    print(f"❌ Missing required fields in properties: {missing_fields}")
                    self.log_issue("/api/properties",
                                   f"Missing required fields: {missing_fields}", "HIGH")
                else:
                    print("✅ Property structure validation passed")
            return success, response
        elif success:
            print(f"❌ Expected list of properties, got: {type(response)}")
            self.log_issue("/api/properties", f"Invalid response type: {type(response)}", "HIGH")
        return success, []

    def test_get_lots(self):
        """GET /api/lots — comptage dynamique"""
        success, response = self.run_test(
            "Get All Lots", "GET", "/api/lots", 200
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} lots (seuil : >={MIN_LOTS})")
            if len(response) >= MIN_LOTS:
                print("✅ Lot count OK")
            else:
                self.log_issue("/api/lots", f"Seulement {len(response)} lots", "MEDIUM")
            if response:
                lot = response[0]
                required_fields = ['id', 'loc', 'lots', 'dispo', 'su', 'pr', 'st']
                missing_fields = [f for f in required_fields if f not in lot]
                if missing_fields:
                    print(f"❌ Missing required fields in lots: {missing_fields}")
                    self.log_issue("/api/lots",
                                   f"Missing required fields: {missing_fields}", "HIGH")
                else:
                    print("✅ Lot structure validation passed")
            return success, response
        elif success:
            print(f"❌ Expected list of lots, got: {type(response)}")
            self.log_issue("/api/lots", f"Invalid response type: {type(response)}", "HIGH")
        return success, []

    def test_get_single_property(self, properties):
        """GET /api/properties/{id}"""
        if not properties:
            print("⚠️  Skipping single property test - no properties available")
            return True
        test_id = properties[0]['id']
        success, response = self.run_test(
            f"Get Property {test_id}", "GET", f"/api/properties/{test_id}", 200
        )
        if success and response.get('id') == test_id:
            print(f"✅ Retrieved correct property: {response.get('ti', 'Unknown Title')}")
        elif success:
            print(f"❌ Retrieved property ID mismatch: expected {test_id}, "
                  f"got {response.get('id')}")
            self.log_issue(f"/api/properties/{test_id}",
                           "Property ID mismatch in response", "HIGH")
        return success

    def test_writes_require_auth(self):
        """Securite : une ecriture SANS JWT doit renvoyer 401"""
        payload = {
            "ti": "Test sans auth (doit echouer)", "ty": "Appartement",
            "tr": "Vente", "pr": 1000000, "nb": "Plateau"
        }
        success, _ = self.run_test(
            "Create Property SANS JWT (401 attendu)", "POST", "/api/properties", 401,
            data=payload, headers={'Content-Type': 'application/json'}
        )
        return success

    def test_create_property(self):
        """POST /api/properties avec JWT"""
        test_property = {
            "ti": "Test Property for API Testing",
            "de": "This is a test property created for API testing purposes",
            "ty": "Appartement",
            "tr": "Vente",
            "pr": 50000000,
            "nb": "Plateau",
            "su": 100,
            "ro": 3,
            "be": 2,
            "ba": 1,
            "fe": ["Test"],
            "im": [],
            "vd": [],
            "ft": False
        }
        success, response = self.run_test(
            "Create Property (JWT)", "POST", "/api/properties", 200,
            data=test_property, headers=self._headers(with_auth=True)
        )
        if success and 'id' in response:
            print(f"   Created property with ID: {response['id']}")
            return success, response['id']
        elif success:
            print(f"❌ Expected property with ID, got: {response}")
            self.log_issue("/api/properties", "Property creation didn't return ID", "HIGH")
        return success, None

    def test_update_property(self, property_id):
        """PUT /api/properties/{id} avec JWT"""
        if not property_id:
            print("⚠️  Skipping update test - no property ID")
            return True
        payload = {
            "ti": "Test Property for API Testing (updated)",
            "ty": "Appartement", "tr": "Location", "pr": 600000,
            "nb": "Plateau", "su": 100, "ro": 3, "be": 2, "ba": 1
        }
        success, response = self.run_test(
            f"Update Property {property_id} (JWT)", "PUT",
            f"/api/properties/{property_id}", 200,
            data=payload, headers=self._headers(with_auth=True)
        )
        if success and response.get('tr') == 'Location':
            print("✅ Property updated (Vente -> Location)")
        return success

    def test_add_view(self, property_id):
        """POST /api/properties/{id}/view — compteur global"""
        if not property_id:
            print("⚠️  Skipping view test - no property ID")
            return True
        success, response = self.run_test(
            f"Add View {property_id} (public)", "POST",
            f"/api/properties/{property_id}/view", 200,
            data={}, headers={'Content-Type': 'application/json'}
        )
        if success and isinstance(response.get('views'), int) and response['views'] >= 1:
            print(f"✅ Views incremented: {response['views']}")
        elif success:
            self.log_issue(f"/api/properties/{property_id}/view",
                           "Invalid views counter in response", "MEDIUM")
        return success


    def test_messages_flow(self):
        """Messages de contact : POST public -> GET admin -> PUT lu -> DELETE"""
        payload = {
            "name": "Test API",
            "email": "test@api.dialibatou",
            "phone": "+221 77 000 00 00",
            "subject": "Test backend_test.py",
            "message": "Message de test automatise backend_test.py"
        }
        created_id = None
        ok, response = self.run_test(
            "Create Message (public)", "POST", "/api/messages", 200, data=payload
        )
        if ok and 'id' in response:
            created_id = response['id']
            print(f"   Message cree avec l'id {created_id}")
        elif ok:
            self.log_issue("/api/messages", "Reponse sans id", "HIGH")

        ok_list, messages = self.run_test(
            "Get Messages (JWT)", "GET", "/api/messages", 200,
            headers=self._headers(with_auth=True)
        )
        if ok_list and isinstance(messages, list):
            print(f"   {len(messages)} message(s) en base")
            if created_id and any(m.get('id') == created_id for m in messages):
                print("✅ Message cree retrouve dans la liste admin")
            elif created_id:
                self.log_issue("/api/messages", "Message cree introuvable en liste", "HIGH")

        if created_id:
            self.run_test(
                f"Mark Message {created_id} read (JWT)", "PUT",
                f"/api/messages/{created_id}", 200,
                data={"read": True}, headers=self._headers(with_auth=True)
            )
            self.run_test(
                f"Delete Message {created_id} (JWT)", "DELETE",
                f"/api/messages/{created_id}", 200,
                headers=self._headers(with_auth=True)
            )
        return created_id is not None

    def test_upload_image(self):
        """Upload image multipart -> URL /uploads/images/... puis acces public"""
        ok, response = self.run_upload_test(
            "Upload Image (JWT)", "/api/upload/image",
            "test_pixel.png", TINY_PNG, "image/png"
        )
        url = None
        if ok:
            url = response.get('url', '')
            if url.startswith('/uploads/images/'):
                print(f"✅ URL relative renvoyee : {url}")
            else:
                self.log_issue("/api/upload/image",
                               f"URL inattendue : {url}", "HIGH")
            # Le fichier doit etre servi par le backend (StaticFiles)
            served_ok, served = self.run_test(
                "Fetch Uploaded Image (public)", "GET", url, 200,
                headers={}
            )
            if served_ok:
                print("✅ Fichier servi via /uploads/... (pas de base64)")
        # Securite : upload SANS JWT -> 401
        self.run_upload_test(
            "Upload Image SANS JWT (401 attendu)", "/api/upload/image",
            "test_pixel.png", TINY_PNG, "image/png", with_auth=False,
            expected_status=401
        )
        return ok


    def test_delete_property(self, property_id):
        """DELETE /api/properties/{id} avec JWT (nettoyage des donnees de test)"""
        if not property_id:
            print("⚠️  Skipping delete test - no property ID provided")
            return True
        success, response = self.run_test(
            f"Delete Property {property_id} (JWT)", "DELETE",
            f"/api/properties/{property_id}", 200,
            headers=self._headers(with_auth=True)
        )
        if success and 'message' in response:
            print(f"   Delete response: {response['message']}")
        return success

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Backend API Testing for DIALIBATOU BTP IMMOBILIER")
        print(f"   Base URL: {self.base_url}")
        print(f"   Seuils dynamiques : properties >= {MIN_PROPERTIES}, lots >= {MIN_LOTS}")
        print("=" * 60)

        # Test 1 : Health Check (arrete tout si le backend ne tourne pas)
        if not self.test_health_check():
            print("❌ Health check failed - API may not be running")
            self.log_issue("/api/health",
                           "Health check failed - service not available", "CRITICAL")
            return self.generate_report()

        # Test 2 : Login JWT (obligatoire pour les ecritures)
        has_token = self.test_login()

        # Test 3-4 : Listes (comptage dynamique)
        _, properties = self.test_get_properties()
        self.test_get_lots()

        # Test 5 : Une propriete
        if properties:
            self.test_get_single_property(properties)

        # Test 6 : Securite — ecriture sans JWT refusee
        self.test_writes_require_auth()

        # Tests 7-9 : CRUD propriete avec JWT
        created_id = None
        if has_token:
            create_ok, created_id = self.test_create_property()
            if create_ok:
                self.test_update_property(created_id)
                self.test_add_view(created_id)
        else:
            print("⚠️  Tests d'ecriture properties SAUTES (pas de JWT)")

        # Test 10 : Vue publique sur une propriete existante
        if properties:
            self.test_add_view(properties[0]['id'])

        # Test 11 : Messagerie complete
        self.test_messages_flow()

        # Test 12 : Upload image (+ acces public + refus sans JWT)
        self.test_upload_image()

        # Test 13 : Suppression (nettoyage)
        if created_id:
            self.test_delete_property(created_id)

        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 TEST REPORT")
        print("=" * 60)

        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")

        if self.issues:
            print(f"\n⚠️  ISSUES FOUND ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue['endpoint']}: {issue['issue']} [{issue['severity']}]")
        else:
            print("\n✅ No critical issues found!")

        print("=" * 60)

        # Succes si >= 90% de tests passent et aucun probleme CRITICAL
        critical_issues = [i for i in self.issues if i['severity'] == 'CRITICAL']
        return success_rate >= 90 and len(critical_issues) == 0


def main():
    """Main test function"""
    print("🔧 DIALIBATOU BTP IMMOBILIER - Backend API Testing")
    print(f"Testing against {BASE_URL}")
    print("Assurez-vous que le backend est lance :")
    print("  cd dialibatou-backend && venv\\Scripts\\activate")
    print("  uvicorn main:app --reload --port 8001")

    tester = BackendAPITester(BASE_URL)
    success = tester.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())


