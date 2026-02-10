
from tools import list_val_in_another, is_parentstring, check_dict_in_list

def check_resonance(role, style, keyword_list):
    if not style.resonance: 
        return False

    if not keyword_list: 
        return True

    checks = [
        is_parentstring(style.resonance['name'], keyword_list),
        list_val_in_another(style.resonance.get('type'), keyword_list),
        is_parentstring(style.resonance['0'], keyword_list),

        list_val_in_another(role.nicknames, keyword_list),
        is_parentstring(role.en.upper(), keyword_list),
        list_val_in_another(style.nicknames, keyword_list),
        is_parentstring(style.role_name, keyword_list),
        is_parentstring(style.name, keyword_list),
        check_dict_in_list(style.id_en, keyword_list)
    ]
    
    return any(checks)