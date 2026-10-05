
import os
from 角色.style_info import get_style_obj
from 角色.master_skill_info import get_master_skill_obj
from tools import load_json, get_dir_values_list

import 日志.error_queue_proc
from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


def report_data_error(msg):
    """数据文件有问题：写日志 + 推到错误队列（主界面会弹提示）。"""
    logger.error(msg)
    try:
        日志.error_queue_proc.error_queue.put(msg)
    except Exception:
        pass

# 角色
class Role:
    def __init__(self, img_path = None, 
        name = None, en = None,nicknames = None, description = None,
        team = None,
        weapon_attribute = None, weapon = None, master_skill = None,
        Astyles = None, Sstyles = None, SSstyles = None, SSRstyles = None
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

        self.Astyles = Astyles                      # A风格对象列表[]
        self.Sstyles = Sstyles                      # S风格对象列表[]
        self.SSstyles = SSstyles                    # SS风格对象列表[]
        self.SSRstyles = SSRstyles                  # SSR风格对象列表[]
    
    def __str__(self):
        return f"角色：{self.name}，英文：{self.en}，别名：{self.nicknames}，描述：{self.description}，队伍：{self.team}，武器属性：{self.weapon_attribute}，武器：{self.weapon}，大师技能：{self.master_skill}，A风格数量：{len(self.Astyles)}，S风格数量：{len(self.Sstyles)}，SS风格数量：{len(self.SSstyles)}，SSR风格数量：{len(self.SSRstyles)}"

# 根据字典 创建并返回角色对象
def creat_role(role_json, Astyles, Sstyles, SSstyles, SSRstyles) -> Role:

    # 字段缺失时不再直接抛 KeyError：用空值代替并提示
    needed = ("img_path", "name", "en", "nicknames", "description",
              "team", "weapon_attribute", "weapon")
    missing = [k for k in needed if k not in role_json]
    if missing:
        report_data_error(
            "角色数据缺少字段：%s（已用空值代替，角色：%s）"
            % ("、".join(missing), role_json.get("name") or "?"))

    img_path = role_json.get('img_path')
    name = role_json.get('name')
    en = role_json.get('en')
    nicknames = role_json.get('nicknames')
    description = role_json.get('description')
    team = role_json.get('team')
    weapon_attribute = role_json.get('weapon_attribute')
    weapon = role_json.get('weapon')

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
        SSstyles,
        SSRstyles
    )

    return role

# 获取角色的风格对象列表
def get_styles(role_path, style_rarity) -> list:
    file_path = os.path.join(role_path, f"{style_rarity}styles.json")
    if not os.path.exists(file_path):
        return []
    styles_dir = load_json(file_path)
    if not styles_dir:
        return []
    # 逐个风格解析：某个风格的数据缺字段时只跳过它并提示，不影响其它风格
    styles = []
    for style_name, style_dir in styles_dir.items():
        try:
            styles.append(get_style_obj(style_dir))
        except Exception as e:
            report_data_error(
                "风格数据解析失败，已跳过该风格：\n"
                "文件：%s\n风格：%s\n原因：%s: %s"
                % (file_path.replace("\\", "/"), style_name,
                   type(e).__name__, e))
    return styles


# 角色对象字典 键：角色名，值：角色对象
all_roles = {}

def creat_role_obj(role_path) -> Role:

    role_json = load_json(role_path + "/role.json")
    role_name = role_json.get('name')
    if not role_name:
        report_data_error(
            "角色数据缺少 name 字段，已跳过该角色：\n文件：%s/role.json"
            % role_path.replace("\\", "/"))
        role_name = os.path.basename(str(role_path)) or "?"
        role_json["name"] = role_name      # 让 Role 对象也有可用的名字
    if role_name in all_roles:
        return all_roles[role_name]

    # 通过 JSON 资源文件加载必要风格信息 Astyles.json、Sstyles.json、SSstyles.json、SSRstyles.json
    # 生成各稀有度风格对象列表
    Astyles = get_styles(role_path, "A")
    Sstyles = get_styles(role_path, "S")
    SSstyles = get_styles(role_path, "SS")
    SSRstyles = get_styles(role_path, "SSR")

    # 生成 role 角色对象
    role = creat_role(role_json, Astyles, Sstyles, SSstyles, SSRstyles)
    all_roles[role_name] = role

    return role


def get_role_master_img(role) -> str:
    photo_path = f"./角色/{role.team}/{role.en}/{role.en}Q.png"
    return photo_path
