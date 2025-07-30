import json
import base64
import os
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import webauthn
from authn.models import Passkey


# Get default values from environment
DEFAULT_ORIGIN = os.getenv("WEBAUTHN_ORIGIN", "http://localhost:8000")
DEFAULT_RP_ID = os.getenv("WEBAUTHN_RP_ID", "localhost")
RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "Barcode Manager")
RP_ICON = os.getenv("WEBAUTHN_RP_ICON", None)  # Icon is optional


def get_rp_id(request):
    """Get RP ID based on request host"""
    host = request.get_host().split(':')[0]  # Remove port if present
    
    # For local development, handle common cases
    if host in ['localhost', '127.0.0.1', '0.0.0.0']:
        return host
    
    # For production, use the configured RP_ID or the host
    return os.getenv("WEBAUTHN_RP_ID", host)


def get_origin(request):
    """Get origin based on request"""
    # Build origin from request
    scheme = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    origin = f"{scheme}://{host}"
    
    # For production, you might want to use the configured origin
    if os.getenv("WEBAUTHN_ORIGIN"):
        return os.getenv("WEBAUTHN_ORIGIN")
    
    return origin


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def passkey_registration_options(request):
    """Generate registration options for creating a new passkey"""
    try:
        user = request.user
        
        # Get RP ID based on request
        rp_id = get_rp_id(request)
        
        # Create RelyingParty object
        rp = webauthn.types.RelyingParty(
            id=rp_id,
            name=RP_NAME,
            icon=RP_ICON
        )
        
        # Create User object
        user_entity = webauthn.types.User(
            id=str(user.id).encode('utf-8'),
            display_name=getattr(user.userprofile, 'name', user.username) if hasattr(user, 'userprofile') else user.username,
            name=user.username,
            icon=None  # Icon is optional
        )
        
        # Get existing passkey credential IDs to exclude
        existing_keys = []
        user_passkeys = Passkey.objects.filter(user=user)
        for passkey in user_passkeys:
            # Decode the base64 credential ID to bytes
            existing_keys.append(base64.b64decode(passkey.credential_id))
        
        # Generate registration options
        options, challenge = webauthn.create_webauthn_credentials(
            rp=rp,
            user=user_entity,
            existing_keys=existing_keys,
            attachment=None,  # Allow both platform and cross-platform authenticators
            require_resident=False,  # Don't require resident keys for better compatibility
            user_verification=webauthn.types.UserVerification.Preferred,
            attestation_request=webauthn.types.Attestation.NoneAttestation  # More compatible
        )
        
        # Store challenge in session
        request.session['registration_challenge'] = challenge
        
        return Response({
            "success": True,
            "options": options
        })
        
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Failed to generate registration options: {str(e)}"
        }, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def passkey_registration_verify(request):
    """Verify and save a new passkey registration"""
    try:
        user = request.user
        credential = request.data.get('credential')
        
        if not credential:
            return Response({
                "success": False,
                "message": "No credential data provided"
            }, status=400)
        
        # Get challenge from session
        expected_challenge = request.session.get('registration_challenge')
        if not expected_challenge:
            return Response({
                "success": False,
                "message": "No registration challenge found"
            }, status=400)
        
        # Get RP ID based on request
        rp_id = get_rp_id(request)
        
        # Create RelyingParty object
        rp = webauthn.types.RelyingParty(
            id=rp_id,
            name=RP_NAME,
            icon=RP_ICON
        )
        
        # Get origin based on request
        origin = get_origin(request)
        
        # Verify registration
        verification = webauthn.verify_create_webauthn_credentials(
            rp=rp,
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=origin
        )
        
        if verification.verified:
            # Create new passkey
            Passkey.objects.create(
                user=user,
                credential_id=base64.b64encode(verification.credential_id).decode('utf-8'),
                public_key=base64.b64encode(verification.public_key).decode('utf-8'),
                sign_count=verification.sign_count,
                transports=credential.get('response', {}).get('transports', [])
            )
            
            # Clear challenge
            del request.session['registration_challenge']
            
            return Response({
                "success": True,
                "message": "Passkey registered successfully"
            })
        
        return Response({
            "success": False,
            "message": "Passkey verification failed"
        }, status=400)
        
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Failed to verify registration: {str(e)}"
        }, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def passkey_authentication_options(request):
    """Generate authentication options for passkey login"""
    try:
        # Get username if provided (for conditional UI)
        username = request.data.get('username', '')
        
        # Get RP ID based on request
        rp_id = get_rp_id(request)
        
        # Create RelyingParty object
        rp = webauthn.types.RelyingParty(
            id=rp_id,
            name=RP_NAME,
            icon=RP_ICON
        )
        
        # Get credentials based on username
        existing_keys = []
        if username:
            try:
                user = User.objects.get(username=username)
                user_passkeys = Passkey.objects.filter(user=user)
                for passkey in user_passkeys:
                    # Decode the base64 credential ID to bytes
                    existing_keys.append(base64.b64decode(passkey.credential_id))
            except User.DoesNotExist:
                pass
        
        # Generate authentication options
        options, challenge = webauthn.get_webauthn_credentials(
            rp=rp,
            existing_keys=existing_keys if existing_keys else None,
            user_verification=webauthn.types.UserVerification.Preferred
        )
        
        # Store challenge in session
        request.session['authentication_challenge'] = challenge
        
        return Response({
            "success": True,
            "options": options
        })
        
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Failed to generate authentication options: {str(e)}"
        }, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def passkey_authentication_verify(request):
    """Verify passkey authentication and log the user in"""
    try:
        credential = request.data.get('credential')
        
        if not credential:
            return Response({
                "success": False,
                "message": "No credential data provided"
            }, status=400)
        
        # Get challenge from session
        expected_challenge = request.session.get('authentication_challenge')
        if not expected_challenge:
            return Response({
                "success": False,
                "message": "No authentication challenge found"
            }, status=400)
        
        # Find the passkey by credential ID
        credential_id = credential.get('id')
        if not credential_id:
            return Response({
                "success": False,
                "message": "No credential ID provided"
            }, status=400)
        
        # Convert base64url to standard base64 for comparison
        # Replace URL-safe characters
        credential_id_b64 = credential_id.replace('-', '+').replace('_', '/')
        # Add padding if necessary
        padding = 4 - (len(credential_id_b64) % 4)
        if padding != 4:
            credential_id_b64 += '=' * padding
        
        try:
            passkey = Passkey.objects.get(credential_id=credential_id_b64)
        except Passkey.DoesNotExist:
            # Try without conversion in case it's already standard base64
            try:
                passkey = Passkey.objects.get(credential_id=credential_id)
            except Passkey.DoesNotExist:
                return Response({
                    "success": False,
                    "message": "Passkey not found"
                }, status=400)
        
        # Get RP ID based on request
        rp_id = get_rp_id(request)
        
        # Create RelyingParty object
        rp = webauthn.types.RelyingParty(
            id=rp_id,
            name=RP_NAME,
            icon=RP_ICON
        )
        
        # Get origin based on request
        origin = get_origin(request)
        
        # Verify authentication
        verification = webauthn.verify_get_webauthn_credentials(
            rp=rp,
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=origin,
            credential_public_key=base64.b64decode(passkey.public_key),
            credential_current_sign_count=passkey.sign_count
        )
        
        if verification.verified:
            # Update sign count
            passkey.sign_count = verification.new_sign_count
            passkey.save()
            
            # Log the user in
            user = passkey.user
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            # Clear challenge
            del request.session['authentication_challenge']
            
            # Create response
            response = Response({
                "success": True,
                "message": "Login successful",
                "username": user.username
            })
            
            # Set JWT cookies
            response.set_cookie(
                "access_token", access_token,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=os.getenv("COOKIE_SAMESITE", "Lax"),
                secure=os.getenv("COOKIE_SECURE", "False").lower() == "true",
                max_age=int(os.getenv("ACCESS_TOKEN_AGE", 1800))
            )
            response.set_cookie(
                "refresh_token", refresh_token,
                httponly=os.getenv("COOKIE_HTTPONLY", "True").lower() == "true",
                samesite=os.getenv("COOKIE_SAMESITE", "Lax"),
                secure=os.getenv("COOKIE_SECURE", "False").lower() == "true",
                max_age=int(os.getenv("REFRESH_TOKEN_AGE", 604800))
            )
            
            return response
        
        return Response({
            "success": False,
            "message": "Passkey verification failed"
        }, status=400)
        
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Failed to verify authentication: {str(e)}"
        }, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def passkey_list(request):
    """List all passkeys for the current user"""
    try:
        user_passkeys = Passkey.objects.filter(user=request.user)
        passkeys_data = [
            {
                "id": pk.id,
                "created_at": pk.created_at.isoformat(),
                "last_used": pk.created_at.isoformat(),  # You might want to track this separately
            }
            for pk in user_passkeys
        ]
        
        return Response({
            "success": True,
            "passkeys": passkeys_data
        })
        
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Failed to list passkeys: {str(e)}"
        }, status=500)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def passkey_delete(request, passkey_id):
    """Delete a specific passkey"""
    try:
        passkey = Passkey.objects.get(id=passkey_id, user=request.user)
        passkey.delete()
        
        return Response({
            "success": True,
            "message": "Passkey deleted successfully"
        })
        
    except Passkey.DoesNotExist:
        return Response({
            "success": False,
            "message": "Passkey not found"
        }, status=404)
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Failed to delete passkey: {str(e)}"
        }, status=500) 