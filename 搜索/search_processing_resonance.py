
from tools import list_val_in_another, is_parentstring

def check_resonance(style, keyword_list):
    if not style.resonance: 
        return False

    if not keyword_list: 
        return True

    checks = [
        is_parentstring(style.resonance['name'], keyword_list),
        list_val_in_another(style.resonance.get('type'), keyword_list),
        is_parentstring(style.resonance['0'], keyword_list)
    ]
    
    return any(checks)