from django import template
from bufe.utils import is_bufeadmin

register = template.Library()


@register.filter(name='is_bufeadmin')
def is_bufeadmin_filter(user):
    """
    Template filter to check if user is a bufeadmin.
    Usage: {% if user|is_bufeadmin %}
    """
    return is_bufeadmin(user)


@register.filter(name='get_category_emoji')
def get_category_emoji(category_name):
    """
    Template filter to get emoji for category names.
    Usage: {{ kategoria.nev|get_category_emoji }}
    """
    # Convert to lowercase for matching
    name_lower = str(category_name).lower()
    
    # Category emoji mapping
    emoji_map = {
        # Drinks
        'italok': '🥤',
        'ital': '🥤', 
        'üdítő': '🥤',
        'üdítők': '🥤',
        'szörp': '🧃',
        'szörpök': '🧃',
        'víz': '💧',
        'kávé': '☕',
        'tea': '🍵',
        'energia': '⚡',
        'energiaital': '⚡',
        
        # Snacks & Sandwiches  
        'szendvics': '🥪',
        'szendvicsek': '🥪',
        'szendi': '🥪',
        'sandwich': '🥪',
        'pogácsa': '🥖',
        'péksütemény': '🥖',
        'péksütemények': '🥖',
        'kifli': '🥐',
        'croissant': '🥐',
        
        # Sweets
        'édesség': '🍬',
        'édességek': '🍬',
        'cukor': '🍬',
        'cukorka': '🍭',
        'cuki': '🍬',
        'bonbon': '🍬',
        'csoki': '🍫',
        'csokoládé': '🍫',
        'süti': '🍪',
        'sütemény': '🍪',
        'sütemények': '🍪',
        'keksz': '🍪',
        'torta': '🎂',
        'muffin': '🧁',
        'fagyi': '🍦',
        'fagylalt': '🍦',
        
        # Healthy/Fruits
        'gyümölcs': '🍎',
        'gyümölcsök': '🍎', 
        'alma': '🍎',
        'banán': '🍌',
        'narancs': '🍊',
        'egészséges': '🥗',
        'fitness': '💪',
        'zöldség': '🥕',
        'zöldségek': '🥕',
        'saláta': '🥗',
        
        # Pizza/Hot food
        'pizza': '🍕',
        'pizzák': '🍕',
        'meleg': '🔥',
        'forró': '🔥',
        'lángos': '🍳',
        'hamburger': '🍔',
        'burger': '🍔',
        'hotdog': '🌭',
        'virsli': '🌭',
        'hús': '🍖',
        'húsos': '🍖',
        'sült': '🍳',
        
        # Breakfast
        'reggeli': '🌅',
        'reggelik': '🌅',
        'tojás': '🥚',
        'bacon': '🥓',
        'sonka': '🥓',
        'sajt': '🧀',
        'tejtermék': '🥛',
        'tej': '🥛',
        'joghurt': '🥛',
        'müzli': '🥣',
        
        # Chips & Crackers
        'chips': '🥔',
        'sós': '🥨',
        'ropogós': '🥨',
        'kréker': '🥨',
        'popcorn': '🍿',
        'mogyoró': '🥜',
        'dió': '🥜',
        'mandula': '🥜',
        
        # Other
        'jégkrém': '🍨',
        'fagyott': '🧊',
        'levélke': '🍃',
        'bio': '🌱',
        'natúr': '🌿',
        'vegán': '🌱',
        'gluténmentes': '🌾',
    }
    
    # Try to find a match
    for key, emoji in emoji_map.items():
        if key in name_lower:
            return emoji
    
    # Default emojis based on common patterns
    if any(word in name_lower for word in ['ital', 'drink', 'víz', 'szörp']):
        return '🥤'
    elif any(word in name_lower for word in ['süt', 'cake', 'torta', 'muffin']):
        return '🍰'  
    elif any(word in name_lower for word in ['édes', 'sweet', 'candy']):
        return '🍬'
    elif any(word in name_lower for word in ['sós', 'salty', 'chips']):
        return '🥨'
    elif any(word in name_lower for word in ['meleg', 'hot', 'warm']):
        return '🔥'
    else:
        return '🍽️'  # Default food emoji
