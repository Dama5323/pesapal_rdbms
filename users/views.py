import sys
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction as db_transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models and serializers
from .models import User, UserProfile, Account
from .serializers import UserSerializer, UserCreateSerializer, UserKYCUpdateSerializer, AccountSerializer  # ← ADDED AccountSerializer

# Try to import RDBMS service
try:
    from services import rdbms_service
    RDBMS_AVAILABLE = True
except ImportError:
    print("⚠ RDBMS service not available in users/views.py")
    RDBMS_AVAILABLE = False

# ==================== API VIEWS ====================

@api_view(['GET', 'POST'])
def users_list(request):
    """
    List all users or create a new user
    """
    if request.method == 'GET':
        # Only staff can list all users
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        
        # Log audit if RDBMS available
        if RDBMS_AVAILABLE:
            rdbms_service.log_audit(
                model_name='User',
                object_id='list',
                action='VIEW',
                user_id=str(request.user.id) if request.user.is_authenticated else 'anonymous',
                changes={'action': 'list_users', 'count': users.count()}
            )
        
        return Response({'users': serializer.data})
    
    elif request.method == 'POST':
        # Anyone can create an account
        serializer = UserCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            with db_transaction.atomic():
                user = serializer.save()
                
                # Log to RDBMS if available
                if RDBMS_AVAILABLE:
                    rdbms_service.log_audit(
                        model_name='User',
                        object_id=str(user.id),
                        action='CREATE',
                        user_id=str(user.id),
                        changes={
                            'username': user.username,
                            'email': user.email,
                            'phone_number': user.phone_number
                        }
                    )
                
                # Return user data
                user_serializer = UserSerializer(user)
                return Response(
                    {'user': user_serializer.data, 'message': 'User created successfully'},
                    status=status.HTTP_201_CREATED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_detail(request, user_id):
    """
    Retrieve, update or delete a user
    """
    try:
        # Users can only access their own data, unless they're staff
        if str(request.user.id) != user_id and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = User.objects.get(id=user_id)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        
        # Log audit
        if RDBMS_AVAILABLE:
            rdbms_service.log_audit(
                model_name='User',
                object_id=user_id,
                action='VIEW',
                user_id=str(request.user.id),
                changes={}
            )
        
        return Response({'user': serializer.data})
    
    elif request.method == 'PUT':
        # Users can only update their own profile, staff can update any
        if str(request.user.id) != user_id and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            old_data = UserSerializer(user).data
            
            with db_transaction.atomic():
                user = serializer.save()
                
                # Log to RDBMS
                if RDBMS_AVAILABLE:
                    # Find changed fields
                    new_data = UserSerializer(user).data
                    changes = {}
                    for key in old_data:
                        if old_data.get(key) != new_data.get(key):
                            changes[key] = {
                                'old': old_data.get(key),
                                'new': new_data.get(key)
                            }
                    
                    rdbms_service.log_audit(
                        model_name='User',
                        object_id=user_id,
                        action='UPDATE',
                        user_id=str(request.user.id),
                        changes=changes
                    )
            
            return Response({
                'user': serializer.data,
                'message': 'User updated successfully'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Only staff can delete users
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Log before deletion
        if RDBMS_AVAILABLE:
            rdbms_service.log_audit(
                model_name='User',
                object_id=user_id,
                action='DELETE',
                user_id=str(request.user.id),
                changes={'user': str(user)}
            )
        
        user.delete()
        return Response(
            {'message': 'User deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )

@api_view(['POST'])
def login_view(request):
    """
    User login
    """
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Log login to RDBMS
            if RDBMS_AVAILABLE:
                rdbms_service.log_audit(
                    model_name='User',
                    object_id=str(user.id),
                    action='LOGIN',
                    user_id=str(user.id),
                    changes={'ip': request.META.get('REMOTE_ADDR')},
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            
            serializer = UserSerializer(user)
            return Response({
                'user': serializer.data,
                'message': 'Login successful'
            })
        
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    User logout
    """
    # Log logout to RDBMS
    if RDBMS_AVAILABLE:
        rdbms_service.log_audit(
            model_name='User',
            object_id=str(request.user.id),
            action='LOGOUT',
            user_id=str(request.user.id),
            changes={},
            ip_address=request.META.get('REMOTE_ADDR')
        )
    
    logout(request)
    return Response({'message': 'Logout successful'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Get current authenticated user
    """
    serializer = UserSerializer(request.user)
    return Response({'user': serializer.data})

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_kyc_status(request, user_id):
    """
    Update KYC status (admin only)
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = UserKYCUpdateSerializer(user, data=request.data)
    
    if serializer.is_valid():
        old_status = user.kyc_status
        user = serializer.save()
        
        # Log KYC change to RDBMS
        if RDBMS_AVAILABLE:
            rdbms_service.log_audit(
                model_name='User',
                object_id=user_id,
                action='KYC_UPDATE',
                user_id=str(request.user.id),
                changes={
                    'kyc_status': {
                        'old': old_status,
                        'new': user.kyc_status
                    }
                }
            )
        
        return Response({
            'user': UserSerializer(user).data,
            'message': f'KYC status updated to {user.kyc_status}'
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_accounts(request, user_id):
    """
    Get all accounts for a user
    """
    # Users can only see their own accounts, unless staff
    if str(request.user.id) != user_id and not request.user.is_staff:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        user = User.objects.get(id=user_id)
        accounts = user.accounts.all()
        serializer = AccountSerializer(accounts, many=True)  # ← NOW DEFINED
        
        return Response({'accounts': serializer.data})
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

# ==================== RDBMS INTEGRATION VIEWS ====================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_audit_logs(request, user_id):
    """
    Get audit logs for a user (admin only)
    """
    if not RDBMS_AVAILABLE:
        return Response(
            {'error': 'RDBMS service not available'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        user = User.objects.get(id=user_id)
        
        # Get audit logs from RDBMS
        audit_logs = rdbms_service.get_audit_logs(
            model_name='User',
            object_id=user_id,
            limit=100
        )
        
        return Response({
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email
            },
            'audit_logs': audit_logs,
            'count': len(audit_logs)
        })
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAdminUser])
def account_transaction_history(request, account_number):
    """
    Get transaction history for an account (admin only)
    """
    if not RDBMS_AVAILABLE:
        return Response(
            {'error': 'RDBMS service not available'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        account = Account.objects.get(account_number=account_number)
        
        # Get transaction history from RDBMS
        transactions = rdbms_service.get_transaction_history(
            account_id=account_number,
            limit=50
        )
        
        return Response({
            'account': {
                'account_number': account.account_number,
                'user': str(account.user),
                'balance': str(account.balance),
                'currency': account.currency
            },
            'transactions': transactions,
            'count': len(transactions)
        })
        
    except Account.DoesNotExist:
        return Response(
            {'error': 'Account not found'},
            status=status.HTTP_404_NOT_FOUND
        )

# ==================== LEGACY VIEWS (for compatibility) ====================

@csrf_exempt
def users_list_legacy(request):
    """
    Legacy view for /api/users/ (without DRF)
    """
    if request.method == 'GET':
        users = User.objects.all()[:100]  # Limit for performance
        serializer = UserSerializer(users, many=True)
        return JsonResponse({'users': serializer.data})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            serializer = UserCreateSerializer(data=data)
            
            if serializer.is_valid():
                user = serializer.save()
                return JsonResponse(
                    {'user': UserSerializer(user).data},
                    status=201
                )
            
            return JsonResponse(
                {'error': serializer.errors},
                status=400
            )
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def user_detail_legacy(request, user_id):
    """
    Legacy view for /api/users/<id>/ (without DRF)
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return JsonResponse({'user': serializer.data})
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            serializer = UserSerializer(user, data=data, partial=True)
            
            if serializer.is_valid():
                user = serializer.save()
                return JsonResponse({'user': serializer.data})
            
            return JsonResponse({'error': serializer.errors}, status=400)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        user.delete()
        return JsonResponse({'message': 'User deleted'})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)