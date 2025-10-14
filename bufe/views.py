from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
import json
from .utils import domain_required, check_domain_access, get_user_domain, bufeadmin_required, is_bufeadmin, broadcast_order_update
from .models import *
from .forms import RendelesForm

@login_required
@domain_required()
def index(request):
    """
    Büfé app main view for students.
    Requires authentication and valid email domain (@szlgbp.hu or @botond.eu).
    Displays available products by category and allows students to place orders.
    """
    user = request.user
    user_domain = get_user_domain(user)
    
    # Get the buffet (assuming single buffet instance)
    try:
        bufe = Bufe.objects.first()
        if not bufe:
            # Create default buffet if none exists
            bufe = Bufe.objects.create(nev="Iskolai Büfé")
    except Exception as e:
        bufe = None
    
    # Get categories with available products
    kategoriak = Kategoria.objects.filter(bufe=bufe).prefetch_related('termekek') if bufe else []
    
    # Get available products grouped by category
    termekek_by_kategoria = {}
    if bufe:
        for kategoria in kategoriak:
            termekek = kategoria.termekek.filter(elerheto=True)
            if termekek.exists():
                termekek_by_kategoria[kategoria] = termekek
    
    # Get user's recent orders
    recent_orders = Rendeles.objects.filter(
        user=user,
        archived=False
    ).order_by('-leadva')[:5]
    
    # Check if buffet is open
    is_open = bufe.is_open_now() if bufe else False
    
    context = {
        'user': user,
        'user_domain': user_domain,
        'user_full_name': f"{user.last_name} {user.first_name}".strip() or user.username,
        'welcome_message': f"Üdvözöljük a Büfé alkalmazásban, {user.first_name}!" or "Üdvözöljük a Büfé alkalmazásban!",
        'bufe': bufe,
        'kategoriak': kategoriak,
        'termekek_by_kategoria': termekek_by_kategoria,
        'recent_orders': recent_orders,
        'is_open': is_open,
    }
    
    return render(request, 'bufe/index.html', context)


@login_required
@domain_required()
def create_order(request):
    """
    View for students to create a new order.
    Displays product catalog and order form.
    """
    user = request.user
    user_domain = get_user_domain(user)
    
    # Get the buffet
    bufe = Bufe.objects.first()
    if not bufe:
        messages.error(request, "A büfé jelenleg nem elérhető.")
        return redirect('bufe:index')
    
    # Check if buffet is exceptionally closed
    if bufe.rendkivuli_zarva:
        messages.error(request, "A büfé rendkívüli okok miatt zárva tart. Kérjük, próbálja később.")
        return redirect('bufe:index')
    
    # Check if buffet is open
    is_open = bufe.is_open_now()
    
    # Get categories with available products
    kategoriak = Kategoria.objects.filter(bufe=bufe).prefetch_related('termekek')
    termekek_by_kategoria = {}
    for kategoria in kategoriak:
        termekek = kategoria.termekek.filter(elerheto=True)
        if termekek.exists():
            termekek_by_kategoria[kategoria] = termekek
    
    if request.method == 'POST':
        form = RendelesForm(request.POST)
        
        # Get cart items from POST data
        cart_items = []
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                termek_id = int(key.replace('quantity_', ''))
                quantity = int(value) if value else 0
                
                if quantity > 0:
                    try:
                        termek = Termek.objects.get(id=termek_id, elerheto=True)
                        if quantity <= termek.max_rendelesenkent:
                            cart_items.append({
                                'termek_id': termek_id,
                                'db': quantity
                            })
                        else:
                            messages.error(
                                request,
                                f"{termek.nev}: Maximum {termek.max_rendelesenkent} darab rendelhető."
                            )
                    except Termek.DoesNotExist:
                        pass
        
        if not cart_items:
            messages.error(request, "Kérem válasszon ki legalább egy terméket!")
            return redirect('bufe:create_order')
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the order
                    rendeles = form.save(commit=False)
                    rendeles.user = user
                    rendeles.items = cart_items
                    rendeles.vegosszeg = 0  # Will be calculated in save()
                    rendeles.save()
                    
                    # Broadcast new order to bufeadmin WebSocket clients
                    order_data = serialize_order(rendeles)
                    broadcast_order_update(order_data, action='new')
                    
                    messages.success(
                        request,
                        f"Rendelés sikeresen leadva! Rendelésszám: #{rendeles.id}, Végösszeg: {rendeles.vegosszeg} Ft"
                    )
                    return redirect('bufe:order_detail', order_id=rendeles.id)
            except Exception as e:
                messages.error(request, f"Hiba történt a rendelés leadása során: {str(e)}")
                return redirect('bufe:create_order')
    else:
        form = RendelesForm()
    
    context = {
        'user': user,
        'user_domain': user_domain,
        'user_full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
        'bufe': bufe,
        'is_open': is_open,
        'kategoriak': kategoriak,
        'termekek_by_kategoria': termekek_by_kategoria,
        'form': form,
    }
    
    return render(request, 'bufe/create_order.html', context)


@login_required
@domain_required()
def order_detail(request, order_id):
    """
    View to display order details.
    Students can only view their own orders.
    """
    rendeles = get_object_or_404(Rendeles, id=order_id, user=request.user)
    
    # Build order items with product details
    order_items = []
    for item in rendeles.items:
        try:
            termek = Termek.objects.get(id=item['termek_id'])
            order_items.append({
                'termek': termek,
                'mennyiseg': item['db'],
                'osszeg': termek.ar * item['db']
            })
        except Termek.DoesNotExist:
            order_items.append({
                'termek': None,
                'termek_id': item['termek_id'],
                'mennyiseg': item['db'],
                'osszeg': 0
            })
    
    context = {
        'rendeles': rendeles,
        'order_items': order_items,
        'user_full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
    }
    
    return render(request, 'bufe/order_detail.html', context)


@login_required
@domain_required()
def my_orders(request):
    """
    View to display all orders for the current user.
    """
    orders = Rendeles.objects.filter(
        user=request.user,
        archived=False
    ).order_by('-leadva')
    
    context = {
        'orders': orders,
        'user_full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
    }
    
    return render(request, 'bufe/my_orders.html', context)


@login_required
@domain_required()
@require_http_methods(["POST"])
def cancel_order(request, order_id):
    """
    Cancel an order if it's still in 'leadva' state.
    """
    rendeles = get_object_or_404(Rendeles, id=order_id, user=request.user)
    
    if rendeles.allapot == 'leadva':
        rendeles.allapot = 'visszavonva'
        rendeles.save()
        messages.success(request, f"Rendelés #{rendeles.id} sikeresen visszavonva.")
    else:
        messages.error(request, "Ez a rendelés már nem vonható vissza.")
    
    return redirect('bufe:my_orders')


@csrf_exempt
@require_http_methods(["GET"])
def api_check_access(request):
    """
    API endpoint to check if current user has access to Büfé app.
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'has_access': False,
            'reason': 'not_authenticated',
            'message': 'Felhasználó nincs bejelentkezve'
        }, status=401)
    
    has_access, reason = check_domain_access(request.user)
    user_domain = get_user_domain(request.user)
    
    if has_access:
        return JsonResponse({
            'has_access': True,
            'reason': reason,
            'message': 'Hozzáférés engedélyezve',
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'domain': user_domain,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_active': request.user.is_active
            }
        })
    else:
        status_codes = {
            'not_authenticated': 401,
            'not_active': 403,
            'invalid_domain': 403
        }
        
        messages = {
            'not_authenticated': 'Felhasználó nincs bejelentkezve',
            'not_active': 'Felhasználó fiókja nincs aktiválva',
            'invalid_domain': f'Érvénytelen e-mail domain: @{user_domain}'
        }
        
        return JsonResponse({
            'has_access': False,
            'reason': reason,
            'message': messages.get(reason, 'Hozzáférés megtagadva'),
            'user_domain': user_domain,
            'allowed_domains': ['szlgbp.hu', 'botond.eu']
        }, status=status_codes.get(reason, 403))


@csrf_exempt
@require_http_methods(["GET"])
def api_opening_hours(request):
    """
    API endpoint to get opening hours for validation.
    Returns all opening hours for the buffet.
    """
    bufe = Bufe.objects.first()
    if not bufe:
        return JsonResponse({
            'error': 'Büfé nem található'
        }, status=404)
    
    opening_hours = []
    for oh in bufe.opening_hours.all():
        opening_hours.append({
            'weekday': oh.weekday,
            'weekday_name': oh.get_weekday_display(),
            'from_hour': oh.from_hour.strftime('%H:%M') if oh.from_hour else None,
            'to_hour': oh.to_hour.strftime('%H:%M') if oh.to_hour else None,
            'is_closed': oh.is_closed()
        })
    
    return JsonResponse({
        'bufe_name': bufe.nev,
        'rendkivuli_zarva': bufe.rendkivuli_zarva,
        'opening_hours': opening_hours
    })


# ============================================================================
# BUFEADMIN VIEWS
# ============================================================================

@login_required
@bufeadmin_required
def admin_dashboard(request):
    """
    Main dashboard for bufeadmin users.
    Shows real-time order monitoring interface.
    """
    bufe = Bufe.objects.first()
    
    # Get non-archived orders grouped by status
    active_orders = Rendeles.objects.filter(archived=False).order_by('-leadva')
    
    context = {
        'user': request.user,
        'bufe': bufe,
        'active_orders': active_orders,
        'user_full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
    }
    
    return render(request, 'bufe/admin/dashboard.html', context)


@login_required
@bufeadmin_required
def admin_menu_management(request):
    """
    Menu management interface for bufeadmin.
    Allows editing categories, products, prices, and availability.
    """
    bufe = Bufe.objects.first()
    if not bufe:
        messages.error(request, "A büfé nem található.")
        return redirect('bufe:admin_dashboard')
    
    kategoriak = Kategoria.objects.filter(bufe=bufe).prefetch_related('termekek')
    
    context = {
        'user': request.user,
        'bufe': bufe,
        'kategoriak': kategoriak,
        'user_full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
    }
    
    return render(request, 'bufe/admin/menu_management.html', context)


@login_required
@bufeadmin_required
def admin_opening_hours(request):
    """
    Opening hours management interface for bufeadmin.
    """
    bufe = Bufe.objects.first()
    if not bufe:
        messages.error(request, "A büfé nem található.")
        return redirect('bufe:admin_dashboard')
    
    opening_hours = bufe.opening_hours.all().order_by('weekday', 'from_hour')
    
    context = {
        'user': request.user,
        'bufe': bufe,
        'opening_hours': opening_hours,
        'user_full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
    }
    
    return render(request, 'bufe/admin/opening_hours.html', context)


@login_required
@bufeadmin_required
@csrf_exempt
@require_http_methods(["POST"])
def api_update_order_status(request):
    """
    API endpoint to update order status.
    """
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        new_status = data.get('status')
        
        if not order_id or not new_status:
            return JsonResponse({
                'success': False,
                'error': 'Hiányzó paraméterek'
            }, status=400)
        
        rendeles = get_object_or_404(Rendeles, id=order_id)
        
        # Validate status transition
        valid_statuses = ['leadva', 'visszavonva', 'visszaigasolva', 'torolve', 'atadva']
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': 'Érvénytelen állapot'
            }, status=400)
        
        rendeles.allapot = new_status
        rendeles.save()
        
        # Broadcast update to connected WebSocket clients
        order_data = serialize_order(rendeles)
        broadcast_order_update(order_data, action='update')
        
        return JsonResponse({
            'success': True,
            'order': order_data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@bufeadmin_required
@csrf_exempt
@require_http_methods(["POST"])
def api_archive_order(request):
    """
    API endpoint to archive a single order.
    """
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        
        if not order_id:
            return JsonResponse({
                'success': False,
                'error': 'Hiányzó rendelés azonosító'
            }, status=400)
        
        rendeles = get_object_or_404(Rendeles, id=order_id)
        rendeles.archived = True
        rendeles.save()
        
        # Broadcast update to connected WebSocket clients
        order_data = serialize_order(rendeles)
        broadcast_order_update(order_data, action='archive')
        
        return JsonResponse({
            'success': True,
            'order_id': order_id
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@bufeadmin_required
@csrf_exempt
@require_http_methods(["POST"])
def api_archive_all_done(request):
    """
    API endpoint to archive all orders with status 'atadva', 'torolve', or 'visszavonva'.
    """
    try:
        archived_count = Rendeles.objects.filter(
            allapot__in=['atadva', 'torolve', 'visszavonva'],
            archived=False
        ).update(archived=True)
        
        # Broadcast update to refresh all clients
        broadcast_order_update({}, action='archive_all')
        
        return JsonResponse({
            'success': True,
            'archived_count': archived_count
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@bufeadmin_required
@require_http_methods(["GET"])
def api_get_orders(request):
    """
    API endpoint to get all non-archived orders.
    """
    try:
        orders = Rendeles.objects.filter(archived=False).order_by('-leadva')
        orders_data = [serialize_order(order) for order in orders]
        
        return JsonResponse({
            'success': True,
            'orders': orders_data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@bufeadmin_required
@csrf_exempt
@require_http_methods(["POST"])
def api_update_product(request):
    """
    API endpoint to update product details (price, availability, etc.).
    """
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        if not product_id:
            return JsonResponse({
                'success': False,
                'error': 'Hiányzó termék azonosító'
            }, status=400)
        
        termek = get_object_or_404(Termek, id=product_id)
        
        # Update fields if provided
        if 'ar' in data:
            termek.ar = int(data['ar'])
        if 'elerheto' in data:
            termek.elerheto = bool(data['elerheto'])
        if 'kisult' in data:
            termek.kisult = bool(data['kisult'])
        if 'hutve' in data:
            termek.hutve = bool(data['hutve'])
        if 'max_rendelesenkent' in data:
            termek.max_rendelesenkent = int(data['max_rendelesenkent'])
        
        termek.save()
        
        return JsonResponse({
            'success': True,
            'product': {
                'id': termek.id,
                'nev': termek.nev,
                'ar': termek.ar,
                'elerheto': termek.elerheto,
                'kisult': termek.kisult,
                'hutve': termek.hutve,
                'max_rendelesenkent': termek.max_rendelesenkent
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@bufeadmin_required
@csrf_exempt
@require_http_methods(["POST"])
def api_update_bufe(request):
    """
    API endpoint to update bufe settings (rendkivuli_zarva, etc.).
    """
    try:
        data = json.loads(request.body)
        bufe = Bufe.objects.first()
        
        if not bufe:
            return JsonResponse({
                'success': False,
                'error': 'Büfé nem található'
            }, status=404)
        
        # Update fields if provided
        if 'rendkivuli_zarva' in data:
            bufe.rendkivuli_zarva = bool(data['rendkivuli_zarva'])
        
        bufe.save()
        
        return JsonResponse({
            'success': True,
            'bufe': {
                'id': bufe.id,
                'nev': bufe.nev,
                'rendkivuli_zarva': bufe.rendkivuli_zarva
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def serialize_order(rendeles):
    """
    Helper function to serialize order data for JSON responses.
    """
    # Get order items with product details
    order_items = []
    for item in rendeles.items:
        try:
            termek = Termek.objects.get(id=item['termek_id'])
            order_items.append({
                'termek_id': termek.id,
                'termek_nev': termek.nev,
                'termek_ar': termek.ar,
                'mennyiseg': item['db'],
                'osszeg': termek.ar * item['db']
            })
        except Termek.DoesNotExist:
            order_items.append({
                'termek_id': item['termek_id'],
                'termek_nev': 'Ismeretlen termék',
                'termek_ar': 0,
                'mennyiseg': item['db'],
                'osszeg': 0
            })
    
    return {
        'id': rendeles.id,
        'user': {
            'id': rendeles.user.id,
            'username': rendeles.user.username,
            'full_name': f"{rendeles.user.last_name} {rendeles.user.first_name}".strip() or rendeles.user.username,
            'email': rendeles.user.email
        },
        'items': order_items,
        'allapot': rendeles.allapot,
        'allapot_display': rendeles.get_allapot_display(),
        'leadva': rendeles.leadva.strftime('%Y-%m-%d %H:%M:%S'),
        'idozitve': rendeles.idozitve.strftime('%Y-%m-%d %H:%M:%S') if rendeles.idozitve else None,
        'megjegyzes': rendeles.megjegyzes,
        'vegosszeg': rendeles.vegosszeg,
        'archived': rendeles.archived
    }


@csrf_exempt
@require_http_methods(["POST"])
@bufeadmin_required
def api_update_opening_hours(request):
    """
    API endpoint to update opening hours time slots.
    """
    try:
        data = json.loads(request.body)
        oh_id = data.get('id')
        from_hour = data.get('from_hour')
        to_hour = data.get('to_hour')
        
        if not oh_id:
            return JsonResponse({
                'success': False,
                'error': 'Hiányzó ID'
            }, status=400)
        
        oh = get_object_or_404(OpeningHours, id=oh_id)
        
        # Parse time strings and update
        if from_hour:
            from datetime import datetime
            oh.from_hour = datetime.strptime(from_hour, '%H:%M').time()
        
        if to_hour:
            from datetime import datetime
            oh.to_hour = datetime.strptime(to_hour, '%H:%M').time()
        
        oh.save()
        
        return JsonResponse({
            'success': True,
            'opening_hours': {
                'id': oh.id,
                'weekday': oh.weekday,
                'from_hour': oh.from_hour.strftime('%H:%M'),
                'to_hour': oh.to_hour.strftime('%H:%M')
            }
        })
    
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': 'Hibás időformátum (használd: HH:MM)'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



