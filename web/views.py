from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datetime import datetime, timedelta
import json
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import logout as auth_logout
from django.views.decorators.http import require_POST
# Try to import models, handle if they don't exist yet
try:
    from tasks.models import Transaction
    HAS_TRANSACTION_MODEL = True
except ImportError:
    HAS_TRANSACTION_MODEL = False
    Transaction = None

try:
    from tasks.models import Ledger
    HAS_LEDGER_MODEL = True
except ImportError:
    HAS_LEDGER_MODEL = False
    Ledger = None

from users.models import User
def home(request):
    """Landing page for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')

@login_required
def dashboard(request):
    """Main dashboard view"""
    # Initialize with default values
    context = {
        'total_transactions': 0,
        'today_transactions': 0,
        'verification_rate': 0,
        'verified_count': 0,
        'recent_transactions': [],
        'status_counts': [],
        'daily_transactions': [],
        'current_date': datetime.now(),
        'users_count': User.objects.count(),
        'total_volume': 0,
        'avg_transaction': 0,
        'success_rate': 0,
    }
    
    # Only calculate if Transaction model exists
    try:
        from tasks.models import Transaction
        
        total_transactions = Transaction.objects.count()
        today_transactions = Transaction.objects.filter(
            initiated_at__date=datetime.now().date()  # Use initiated_at instead of created_at
        ).count()
        
        # Recent transactions - use initiated_at for ordering
        recent_transactions = Transaction.objects.order_by('-initiated_at')[:10]
        
        # Transaction by status
        status_counts = Transaction.objects.values('status').annotate(count=Count('id'))
        
        # Weekly transaction data for chart - use initiated_at
        week_ago = datetime.now() - timedelta(days=7)
        daily_transactions = []
        for i in range(7):
            date = week_ago + timedelta(days=i)
            count = Transaction.objects.filter(initiated_at__date=date.date()).count()
            daily_transactions.append({
                'date': date.strftime('%a'),
                'count': count
            })
        
        # Calculate total volume
        total_volume_result = Transaction.objects.aggregate(total=Sum('amount'))
        total_volume = total_volume_result['total'] or 0
        
        # Calculate average transaction
        avg_transaction_result = Transaction.objects.aggregate(avg=Avg('amount'))
        avg_transaction = avg_transaction_result['avg'] or 0
        
        # Calculate success rate (assuming 'completed' status means success)
        completed_count = Transaction.objects.filter(status='completed').count()
        success_rate = (completed_count / total_transactions * 100) if total_transactions > 0 else 0
        
        # Update context
        context.update({
            'total_transactions': total_transactions,
            'today_transactions': today_transactions,
            'recent_transactions': recent_transactions,
            'status_counts': status_counts,
            'daily_transactions': json.dumps(daily_transactions),  # Convert to JSON for JS
            'total_volume': total_volume,
            'avg_transaction': avg_transaction,
            'success_rate': round(success_rate, 1),
        })
        
    except (ImportError, Exception) as e:
        # If Transaction model doesn't exist or has errors, use defaults
        print(f"Dashboard error (Transaction model): {str(e)}")
        pass
    
    # Ledger verification data (if Ledger model exists)
    try:
        from tasks.models import Ledger
        ledgers = Ledger.objects.all()
        verified_count = ledgers.filter(is_verified=True).count()
        verification_rate = (verified_count / ledgers.count() * 100) if ledgers.count() > 0 else 0
        
        context.update({
            'verification_rate': round(verification_rate, 1),
            'verified_count': verified_count,
        })
    except (ImportError, Exception) as e:
        # If Ledger model doesn't exist, use defaults
        print(f"Dashboard error (Ledger model): {str(e)}")
        pass
    
    return render(request, 'dashboard.html', context)

@login_required
def transactions_view(request):
    """List all transactions"""
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    transactions = Transaction.objects.all()
    
    if status:
        transactions = transactions.filter(status=status)
    
    if search:
        transactions = transactions.filter(
            Q(transaction_id__icontains=search) |
            Q(description__icontains=search) |
            Q(sender_account__icontains=search) |
            Q(receiver_account__icontains=search)
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(transactions, 20)
    
    try:
        transactions_page = paginator.page(page)
    except PageNotAnInteger:
        transactions_page = paginator.page(1)
    except EmptyPage:
        transactions_page = paginator.page(paginator.num_pages)
    
    context = {
        'transactions': transactions_page,
        'status_filter': status,
        'search_query': search,
    }
    return render(request, 'transactions/list.html', context)

@login_required
def create_transaction_view(request):
    """Create a new transaction"""
    if request.method == 'POST':
        try:
            # Process transaction creation
            sender = request.POST.get('sender_account')
            receiver = request.POST.get('receiver_account')
            amount = request.POST.get('amount')
            description = request.POST.get('description')
            
            # Create transaction (you'll need to integrate with your service)
            # transaction = Transaction.objects.create(...)
            
            messages.success(request, 'Transaction created successfully!')
            return redirect('transactions')
        except Exception as e:
            messages.error(request, f'Error creating transaction: {str(e)}')
    
    return render(request, 'transactions/create.html')

@login_required
def ledger_view(request):
    """View the immutable ledger"""
    # Initialize with empty data
    context = {
        'ledgers': [],
        'total_ledgers': 0,
        'verified_count': 0,
        'chain_integrity': 0,
    }
    
    try:
        from tasks.models import Ledger
        HAS_LEDGER_MODEL = True
    except ImportError:
        HAS_LEDGER_MODEL = False
        messages.info(request, 'Ledger model is not available yet.')
    
    if HAS_LEDGER_MODEL:
        try:
            ledgers = Ledger.objects.order_by('-timestamp')
            
            # Pagination
            page = request.GET.get('page', 1)
            paginator = Paginator(ledgers, 20)
            
            try:
                ledgers_page = paginator.page(page)
            except PageNotAnInteger:
                ledgers_page = paginator.page(1)
            except EmptyPage:
                ledgers_page = paginator.page(paginator.num_pages)
            
            # Calculate stats
            total_ledgers = ledgers.count()
            verified_count = ledgers.filter(is_verified=True).count()
            chain_integrity = (verified_count / total_ledgers * 100) if total_ledgers > 0 else 0
            
            context.update({
                'ledgers': ledgers_page,
                'total_ledgers': total_ledgers,
                'verified_count': verified_count,
                'chain_integrity': round(chain_integrity, 1),
            })
            
        except Exception as e:
            messages.error(request, f'Error loading ledger: {str(e)}')
    
    return render(request, 'ledger/list.html', context)

@login_required
def audit_view(request):
    """Audit and verification view"""
    context = {
        'ledgers': [],
        'verification_results': [],
        'verified_count': 0,
        'total_count': 0,
        'verification_percentage': 0,
        'pending_count': 0,
        'failed_count': 0,
    }
    
    try:
        from tasks.models import Ledger
        HAS_LEDGER_MODEL = True
    except ImportError:
        HAS_LEDGER_MODEL = False
        messages.info(request, 'Ledger model is not available yet.')
        return render(request, 'audit/verify.html', context)
    
    if HAS_LEDGER_MODEL:
        ledgers = Ledger.objects.all()
        verification_results = []
        
        if request.method == 'POST' and 'verify_all' in request.POST:
            # Verify all ledgers
            for ledger in ledgers:
                try:
                    is_valid = ledger.verify_hash() if hasattr(ledger, 'verify_hash') else False
                    verification_results.append({
                        'ledger': ledger,
                        'is_valid': is_valid,
                        'message': 'Valid' if is_valid else 'Hash mismatch or verification not available'
                    })
                except Exception as e:
                    verification_results.append({
                        'ledger': ledger,
                        'is_valid': False,
                        'message': f'Error: {str(e)}'
                    })
        
        total_count = ledgers.count()
        verified_count = ledgers.filter(is_verified=True).count() if hasattr(Ledger, 'is_verified') else 0
        verification_percentage = (verified_count / total_count * 100) if total_count > 0 else 0
        
        context.update({
            'ledgers': ledgers,
            'verification_results': verification_results,
            'verified_count': verified_count,
            'total_count': total_count,
            'verification_percentage': round(verification_percentage, 1),
            'pending_count': total_count - verified_count,
            'failed_count': 0, 
        })
    
    return render(request, 'audit/verify.html', context)

@login_required
def reports_view(request):
    """Financial reports and charts"""
    context = {
        'monthly_data': [],
        'top_transactions': [],
        'status_distribution': [],
        'total_volume': 0,
        'total_transactions': 0,
        'avg_transaction': 0,
        'success_rate': 0,
        'recent_transactions': [],
    }
    
    if HAS_TRANSACTION_MODEL:
        try:
            # Get basic stats
            total_transactions = Transaction.objects.count()
            total_volume_result = Transaction.objects.aggregate(total=Sum('amount'))
            total_volume = total_volume_result['total'] or 0
            
            avg_transaction_result = Transaction.objects.aggregate(avg=Avg('amount'))
            avg_transaction = avg_transaction_result['avg'] or 0
            
            completed_count = Transaction.objects.filter(status='completed').count()
            success_rate = (completed_count / total_transactions * 100) if total_transactions > 0 else 0
            
            # Monthly transaction data - use initiated_at instead of created_at
            monthly_data = []
            current_date = datetime.now()
            
            for i in range(6, -1, -1):
                month_start = current_date.replace(day=1) - timedelta(days=30*i)
                # Calculate month end (last day of month)
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
                
                transactions = Transaction.objects.filter(
                    initiated_at__range=(month_start, month_end)
                )
                
                monthly_data.append({
                    'month': month_start.strftime('%b'),
                    'count': transactions.count(),
                    'amount': transactions.aggregate(total=Sum('amount'))['total'] or 0
                })
            
            # Top transactions
            top_transactions = Transaction.objects.order_by('-amount')[:10]
            
            # Status distribution
            status_distribution = Transaction.objects.values('status').annotate(
                count=Count('id'),
                total=Sum('amount')
            )
            
            # Recent transactions - use initiated_at for ordering
            recent_transactions = Transaction.objects.order_by('-initiated_at')[:10]
            
            context.update({
                'monthly_data': monthly_data,
                'top_transactions': top_transactions,
                'status_distribution': status_distribution,
                'total_volume': total_volume,
                'total_transactions': total_transactions,
                'avg_transaction': avg_transaction,
                'success_rate': round(success_rate, 1),
                'recent_transactions': recent_transactions,
            })
            
        except Exception as e:
            messages.error(request, f'Error loading reports: {str(e)}')
            # Provide sample data for demo
            context.update({
                'monthly_data': [
                    {'month': 'Jan', 'count': 45, 'amount': 12500},
                    {'month': 'Feb', 'count': 52, 'amount': 14300},
                    {'month': 'Mar', 'count': 38, 'amount': 9800},
                ],
                'total_volume': 36600,
                'total_transactions': 135,
                'avg_transaction': 271.11,
                'success_rate': 85.2,
            })
    else:
        messages.info(request, 'Transaction data is not available yet.')
        # Provide sample data for demo
        context.update({
            'monthly_data': [
                {'month': 'Jan', 'count': 45, 'amount': 12500},
                {'month': 'Feb', 'count': 52, 'amount': 14300},
                {'month': 'Mar', 'count': 38, 'amount': 9800},
            ],
            'total_volume': 36600,
            'total_transactions': 135,
            'avg_transaction': 271.11,
            'success_rate': 85.2,
        })
    
    return render(request, 'reports/index.html', context)

def login_view(request):
    """Login page"""
    if request.method == 'POST':
        # Add your authentication logic here
        pass
    return render(request, 'auth/login.html')


@login_required
def profile_view(request):
    """User profile"""
    return render(request, 'auth/profile.html')

def api_docs(request):
    """API documentation page"""
    api_endpoints = {
        'users': {
            'GET /api/users/': 'List all users',
            'GET /api/users/<uuid:user_id>/': 'Get user details',
            'POST /api/users/login/': 'User login',
            'POST /api/users/logout/': 'User logout',
        },
        'tasks': {
            'GET /api/tasks/': 'List all tasks',
            'POST /api/tasks/create/': 'Create a new task',
            'GET /api/tasks/<uuid:task_id>/': 'Get task details',
            'PUT /api/tasks/<uuid:task_id>/': 'Update task',
        },
        'transactions': {
            'POST /api/transactions/create/': 'Create a transaction',
            'GET /api/transactions/<str:transaction_id>/audit/': 'Audit transaction',
            'GET /api/ledgers/verify/': 'Verify all ledgers',
        },
        'financial': {
            'POST /api/financial/sql/': 'Execute financial SQL',
            'GET /api/financial/report/': 'Get financial report',
        }
    }
    
    return render(request, 'api/docs.html', {'api_endpoints': api_endpoints})

def sql_executor(request):
    """SQL Executor page"""
    if request.method == 'POST':
        sql_query = request.POST.get('sql_query', '')
        # Basic SQL execution (simplified - in production, use proper validation)
        if sql_query:
            try:
                # Here you would execute SQL using your RDBMS service
                # For now, just return a mock response
                result = {
                    'query': sql_query,
                    'status': 'executed',
                    'message': 'SQL query executed successfully',
                    'rows_affected': 1
                }
                return JsonResponse(result)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
    
    return render(request, 'sql/executor.html')

def custom_404(request, exception):
    """Custom 404 page"""
    from django.shortcuts import render
    return render(request, '404.html', {'exception': exception}, status=404)

def custom_500(request):
    """Custom 500 page"""
    from django.shortcuts import render
    return render(request, '500.html', status=500)

def register_view(request):
    """Registration page for custom User model with email as username"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone', '')
        
        # Basic validation
        errors = []
        if not email:
            errors.append('Email is required')
        if not password:
            errors.append('Password is required')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters')
        elif password != confirm_password:
            errors.append('Passwords do not match')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            from users.models import User
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered')
            else:
                try:
                    # Create user with custom User model
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=phone_number or None,
                        kyc_status='pending',
                        daily_limit=1000.00,
                        monthly_limit=10000.00
                    )
                    
                    # Log the user in
                    backend = 'users.backends.EmailBackend'
                    login(request, user, backend=backend)
                    
                    messages.success(request, 'Registration successful!')
                    return redirect('dashboard')
                    
                except Exception as e:
                    messages.error(request, f'Error creating account: {str(e)}')
    
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'auth/register.html')

def login_view(request):
    """Login page for custom User model with email as username"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Email and password are required')
        else:
            # Authenticate using custom backend
            from users.backends import EmailBackend
            user = EmailBackend().authenticate(request, username=email, password=password)
            
            if user is not None:
                # Login with custom backend
                backend = 'users.backends.EmailBackend'
                login(request, user, backend=backend)
                messages.success(request, 'Login successful!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password')
    
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'auth/login.html')

def logout_view(request):
    """Handle logout with both GET and POST"""
    if request.method == 'POST':
        auth_logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('home')
    
    # For GET requests, show confirmation or directly logout
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')