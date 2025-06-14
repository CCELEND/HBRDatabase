
import os
from style_info import get_style_obj
from master_skill_info import get_master_skill_obj
from tools import load_json, get_dir_values_list

# 角色
class Role:
    def __init__(self, img_path = None, 
        name = None, en = None,nicknames = None, description = None,
        team = None,
        weapon_attribute = None, weapon = None, master_skill = None,
        Astyles = None, Sstyles = None, SSstyles = None
        ):
        self.img_path = img_path                    # 角色头像路径
        self.name = name                            # 角色名
        self.en = en                                # 英文
        self.nicknames = nicknames                  # 别名列表
        self.description = description              # 描述
        self.team = team                            # 队伍
        self.weapon_attribute = weapon_attribute    # 武器属性 斩 突 打
        self.weapon = weapon                        # 武器
        self.master_skill = master_skill            # 大师技能

        self.Astyles = Astyles                      # A风格对象列表
        self.Sstyles = Sstyles                      # S风格对象列表
        self.SSstyles = SSstyles                    # SS风格对象列表

# 根据字典 创建并返回角色对象
def creat_role(role_json, Astyles, Sstyles, SSstyles):

    img_path = role_json['img_path']
    name = role_json['name']
    en = role_json['en']
    nicknames = role_json['nicknames']
    description = role_json['description']
    team = role_json['team']
    weapon_attribute = role_json['weapon_attribute']
    weapon = role_json['weapon']

    skill_info = role_json.get("master_skill")
    master_skill = get_master_skill_obj(skill_info)

    role = Role(
        img_path,
        name,
        en,
        nicknames,
        description,
        team,
        weapon_attribute,
        weapon,
        master_skill,

        Astyles,
        Sstyles,
        SSstyles
    )

    return role

# 获取角色的风格对象列表
def get_styles(role_path, style_rarity):
    file_path = os.path.join(role_path, f"{style_rarity}styles.json")
    if not os.path.exists(file_path):
        return []
    styles_dir = load_json(file_path)
    if not styles_dir:
        return []
    return [get_style_obj(style_dir) for style_dir in get_dir_values_list(styles_dir)]


# 角色对象字典 键：角色名，值：角色对象
all_roles = {}

def creat_role_obj(role_path):

    role_json = load_json(role_path + "/role.json")
    role_name = role_json['name']
    if role_name in all_roles:
        return all_roles[role_name]

    # 通过 JSON 资源文件加载必要风格信息 Astyles.json、Sstyles.json、SSstyles.json
    # 生成各稀有度风格对象列表
    Astyles = get_styles(role_path, "A")
    Sstyles = get_styles(role_path, "S")
    SSstyles = get_styles(role_path, "SS")

    # 生成 role 角色对象
    role = creat_role(role_json, Astyles, Sstyles, SSstyles)
    all_roles[role_name] = role

    return role