import random
import json
import uuid
from typing import Optional, List

from locust import HttpUser, between, task, events


class BarcodeAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.available_barcode_ids: List[int] = []
        self.test_user_data = {
            "username": f"testuser_{random.randint(1000, 9999)}",
            "password": "TestPassword123!",
            "email": f"test{random.randint(1000, 9999)}@example.com",
            "name": f"Test User {random.randint(1, 100)}",
            "information_id": f"STU{random.randint(100000, 999999)}"
        }

    def on_start(self):
        """Initialize user with authentication and data setup"""
        try:
            # Register a new test user
            self.register_user()
            
            # Login to get authentication token
            self.login_user()
            
            # Discover available barcode IDs for testing
            self.discover_barcode_ids()
            
        except Exception as e:
            events.request.fire(
                request_type="setup",
                name="user_initialization",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    def register_user(self):
        """Register a new test user"""
        try:
            response = self.client.post(
                "/api/register/",
                json={
                    "username": self.test_user_data["username"],
                    "password": self.test_user_data["password"],
                    "email": self.test_user_data["email"],
                    "name": self.test_user_data["name"],
                    "information_id": self.test_user_data["information_id"]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                events.request.fire(
                    request_type="POST",
                    name="user_registration",
                    response_time=response.elapsed.total_seconds() * 1000,
                    response_length=len(response.content),
                    exception=None,
                    context=self.context()
                )
            else:
                # If registration fails, try to login with existing user
                self.test_user_data["username"] = f"existing_user_{random.randint(1, 10)}"
                self.test_user_data["password"] = "ExistingPassword123!"
                
        except Exception as e:
            events.request.fire(
                request_type="POST",
                name="user_registration",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    def login_user(self):
        """Login user and get authentication token"""
        try:
            response = self.client.post(
                "/api/token/",
                json={
                    "username": self.test_user_data["username"],
                    "password": self.test_user_data["password"]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access")
                self.user_id = data.get("user_id")
                
                events.request.fire(
                    request_type="POST",
                    name="user_login",
                    response_time=response.elapsed.total_seconds() * 1000,
                    response_length=len(response.content),
                    exception=None,
                    context=self.context()
                )
            else:
                # Fallback: create a test user without authentication
                self.auth_token = None
                
        except Exception as e:
            events.request.fire(
                request_type="POST",
                name="user_login",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    def discover_barcode_ids(self):
        """Discover available barcode IDs for testing"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            response = self.client.get("/api/barcodes/", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.available_barcode_ids = [item.get("id") for item in data if item.get("id")]
                elif isinstance(data, dict) and "results" in data:
                    self.available_barcode_ids = [item.get("id") for item in data["results"] if item.get("id")]
                    
        except Exception as e:
            # Fallback to random IDs if discovery fails
            self.available_barcode_ids = list(range(1, 101))

    def get_auth_headers(self):
        """Get authentication headers"""
        if self.auth_token:
            return {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
        return {"Content-Type": "application/json"}

    def handle_api_error(self, response, operation_name):
        """Handle API errors gracefully"""
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_message = error_data.get("message", error_data.get("detail", "Unknown error"))
            except:
                error_message = f"HTTP {response.status_code}"
                
            events.request.fire(
                request_type=response.request.method,
                name=f"{operation_name}_error",
                response_time=response.elapsed.total_seconds() * 1000,
                response_length=len(response.content),
                exception=Exception(f"{operation_name} failed: {error_message}"),
                context=self.context()
            )

    @task(3)
    def get_barcodes(self):
        """Get barcode list with pagination and filtering"""
        try:
            # Test different query parameters
            params = {}
            if random.choice([True, False]):
                params["page"] = random.randint(1, 5)
            if random.choice([True, False]):
                params["page_size"] = random.choice([10, 20, 50])
            if random.choice([True, False]):
                params["barcode_type"] = random.choice(["Static", "Dynamic", "Others"])
                
            response = self.client.get(
                "/api/barcodes/",
                params=params,
                headers=self.get_auth_headers()
            )
            
            if response.status_code >= 400:
                self.handle_api_error(response, "get_barcodes")
                
        except Exception as e:
            events.request.fire(
                request_type="GET",
                name="get_barcodes",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    @task(2)
    def get_barcode_detail(self):
        """Get barcode detail with UUID support and error handling"""
        try:
            # Use discovered IDs or fallback to random
            if self.available_barcode_ids:
                barcode_id = random.choice(self.available_barcode_ids)
            else:
                barcode_id = random.randint(1, 100)
            
            # Support both integer IDs and UUIDs
            if random.choice([True, False]) and self.auth_token:
                # Try UUID format (if supported)
                barcode_uuid = str(uuid.uuid4())
                response = self.client.get(
                    f"/api/barcodes/{barcode_uuid}/",
                    headers=self.get_auth_headers()
                )
            else:
                # Use integer ID
                response = self.client.get(
                    f"/api/barcodes/{barcode_id}/",
                    headers=self.get_auth_headers()
                )
            
            if response.status_code >= 400:
                self.handle_api_error(response, "get_barcode_detail")
                
        except Exception as e:
            events.request.fire(
                request_type="GET",
                name="get_barcode_detail",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    @task(1)
    def create_barcode(self):
        """Create new barcode with realistic data and validation"""
        try:
            # Generate realistic barcode data
            barcode_types = ["Static", "Dynamic", "Others"]
            barcode_type = random.choice(barcode_types)
            
            # Generate different types of barcode codes
            if barcode_type == "Static":
                code = f"STATIC{random.randint(100000, 999999)}"
            elif barcode_type == "Dynamic":
                code = f"DYNAMIC{random.randint(100000, 999999)}"
            else:
                code = f"CODE{random.randint(100000, 999999)}"
            
            barcode_data = {
                "barcode": code,
                "barcode_type": barcode_type,
                "linked_id": f"LINK{random.randint(10000, 99999)}" if random.choice([True, False]) else None,
                "session": str(uuid.uuid4()) if barcode_type == "Dynamic" and random.choice([True, False]) else None
            }
            
            response = self.client.post(
                "/api/barcodes/",
                json=barcode_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 201:
                # Add new barcode ID to available list
                try:
                    created_data = response.json()
                    if created_data.get("id"):
                        self.available_barcode_ids.append(created_data["id"])
                except:
                    pass
            elif response.status_code >= 400:
                self.handle_api_error(response, "create_barcode")
                
        except Exception as e:
            events.request.fire(
                request_type="POST",
                name="create_barcode",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    @task(2)
    def generate_barcode(self):
        """Generate barcode for authenticated user"""
        try:
            response = self.client.post(
                "/api/generate_barcode/",
                headers=self.get_auth_headers()
            )
            
            if response.status_code >= 400:
                self.handle_api_error(response, "generate_barcode")
                
        except Exception as e:
            events.request.fire(
                request_type="POST",
                name="generate_barcode",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    @task(1)
    def get_user_profile(self):
        """Get user profile information"""
        try:
            response = self.client.get(
                "/api/me/",
                headers=self.get_auth_headers()
            )
            
            if response.status_code >= 400:
                self.handle_api_error(response, "get_user_profile")
                
        except Exception as e:
            events.request.fire(
                request_type="GET",
                name="get_user_profile",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    @task(1)
    def get_barcode_settings(self):
        """Get user barcode settings"""
        try:
            response = self.client.get(
                "/api/barcode_settings/",
                headers=self.get_auth_headers()
            )
            
            if response.status_code >= 400:
                self.handle_api_error(response, "get_barcode_settings")
                
        except Exception as e:
            events.request.fire(
                request_type="GET",
                name="get_barcode_settings",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    @task(1)
    def update_barcode_settings(self):
        """Update user barcode settings"""
        try:
            settings_data = {
                "server_verification": random.choice([True, False]),
                "timestamp_verification": random.choice([True, False]),
                "barcode_pull": random.choice([True, False])
            }
            
            response = self.client.put(
                "/api/barcode_settings/",
                json=settings_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code >= 400:
                self.handle_api_error(response, "update_barcode_settings")
                
        except Exception as e:
            events.request.fire(
                request_type="PUT",
                name="update_barcode_settings",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    @task(1)
    def delete_barcode(self):
        """Delete a barcode (with error handling for non-existent barcodes)"""
        try:
            if self.available_barcode_ids:
                barcode_id = random.choice(self.available_barcode_ids)
                response = self.client.delete(
                    f"/api/barcodes/{barcode_id}/",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 204:
                    # Remove from available list if successfully deleted
                    self.available_barcode_ids.remove(barcode_id)
                elif response.status_code >= 400:
                    self.handle_api_error(response, "delete_barcode")
            else:
                # Try to delete a random ID (will likely fail)
                random_id = random.randint(1, 1000)
                response = self.client.delete(
                    f"/api/barcodes/{random_id}/",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code >= 400:
                    self.handle_api_error(response, "delete_barcode")
                    
        except Exception as e:
            events.request.fire(
                request_type="DELETE",
                name="delete_barcode",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    @task(1)
    def health_check(self):
        """Health check endpoint test"""
        try:
            response = self.client.get("/health/")
            
            if response.status_code >= 400:
                self.handle_api_error(response, "health_check")
                
        except Exception as e:
            events.request.fire(
                request_type="GET",
                name="health_check",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )

    def on_stop(self):
        """Cleanup when user stops"""
        try:
            # Clean up test data if needed
            if self.auth_token and self.user_id:
                # Could add cleanup logic here
                pass
        except Exception as e:
            events.request.fire(
                request_type="cleanup",
                name="user_cleanup",
                response_time=0,
                response_length=0,
                exception=e,
                context=self.context()
            )
