# AdminOneTimePass Model Completion

I have completed the `AdminOneTimePass` model in `src/core/models/admin_onetimepass.py` and integrated it into the Django application.

## Changes

### 1. Model Implementation

Updated `src/core/models/admin_onetimepass.py` to include:

- `user`: ForeignKey to the auth user model.
- `pass_code`: CharField for the OTP code.
- `created_at`: Timestamp of creation.
- `expires_at`: Timestamp of expiration.
- `is_used`: Boolean flag for usage status.
- `is_valid()`: Helper method to check validity.

### 2. Model Exposure

Updated `src/core/models/__init__.py` to export `AdminOneTimePass`.

### 3. Admin Registration

Registered `AdminOneTimePass` in `src/core/admin.py` to make it manageable via the Django Admin interface.

### 4. Migration

Created migration file `core/migrations/0002_adminonetimepass.py` using `makemigrations`.

### 5. Verification

Created `src/core/tests/test_admin_otp.py` and ran tests to verify the model's logic.

## Verification Results

Ran `python manage.py test core.tests.test_admin_otp`:

```
Found 3 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...
----------------------------------------------------------------------
Ran 3 tests in 0.057s

OK
Destroying test database for alias 'default'...
```
