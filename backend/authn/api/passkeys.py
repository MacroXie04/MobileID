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


# Get the origin from environment or use default
ORIGIN = os.getenv("WEBAUTHN_ORIGIN", "http://localhost:3000")
RP_ID = os.getenv("WEBAUTHN_RP_ID", "localhost")
RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "Barcode Manager")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def passkey_registration_options(request):
    """Generate registration options for creating a new passkey"""
    try:
        user = request.user
        
        # Create webauthn user object
        webauthn_user = webauthn.types.PublicKeyCredentialUserEntity(
            id=str(user.id).encode('utf-8'),
            name=user.username,
            display_name=getattr(user.userprofile, 'name', user.username) if hasattr(user, 'userprofile') else user.username
        )
        
        # Get existing passkeys for this user to exclude
        exclude_credentials = []
        user_passkeys = Passkey.objects.filter(user=user)
        for passkey in user_passkeys:
            exclude_credentials.append({
                'id': passkey.credential_id,
                'type': 'public-key'
            })
        
        # Generate registration options
        registration_options = webauthn.create_webauthn_credentials(
            rp_name=RP_NAME,
            rp_id=RP_ID,
            user=webauthn_user,
            exclude_credentials=exclude_credentials,
            authenticator_selection={
                'authenticatorAttachment': 'platform',
                'residentKey': 'preferred',
                'userVerification': 'preferred'
            },
            attestation='direct'
        )
        
        # Store challenge in session
        request.session['registration_challenge'] = registration_options['challenge']
        
        return Response({
            "success": True,
            "options": registration_options
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
        
        # Verify registration
        verification = webauthn.verify_create_webauthn_credentials(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID
        )
        
        if verification.verified:
            # Create new passkey
            Passkey.objects.create(
                user=user,
                credential_id=verification.credential_id,
                public_key=verification.public_key,
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
        
        # Get credentials based on username
        allow_credentials = []
        if username:
            try:
                user = User.objects.get(username=username)
                user_passkeys = Passkey.objects.filter(user=user)
                for passkey in user_passkeys:
                    allow_credentials.append({
                        'id': passkey.credential_id,
                        'type': 'public-key',
                        'transports': passkey.transports or []
                    })
            except User.DoesNotExist:
                pass
        
        # Generate authentication options
        authentication_options = webauthn.get_webauthn_credentials(
            rp_id=RP_ID,
            allow_credentials=allow_credentials if allow_credentials else None,
            user_verification='preferred'
        )
        
        # Store challenge in session
        request.session['authentication_challenge'] = authentication_options['challenge']
        
        return Response({
            "success": True,
            "options": authentication_options
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
        
        try:
            passkey = Passkey.objects.get(credential_id=credential_id)
        except Passkey.DoesNotExist:
            return Response({
                "success": False,
                "message": "Passkey not found"
            }, status=400)
        
        # Verify authentication
        verification = webauthn.verify_get_webauthn_credentials(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=passkey.public_key,
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