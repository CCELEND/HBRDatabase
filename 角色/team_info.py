from tools import load_json
from 角色.role_info import creat_role_obj, Role, report_data_error

from concurrent.futures import ThreadPoolExecutor, as_completed

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

# 队伍
class Team:
    def __init__(self, logo_path = None, 
        name = None, description = None, roles = None
        ):
        self.logo_path = logo_path                  # 队伍头像路径
        self.name = name                            # 队伍名
        self.description = description              # 队伍描述
        self.roles = roles                          # 角色对象列表[]

    def __str__(self):
        return f"队伍：{self.name}，描述：{self.description}，角色数量：{len(self.roles)}"


teams_json = {}
# 加载资源文件
def load_teams_json():
    global teams_json

    if teams_json:
        return

    data = load_json("./角色/teams.json")
    if not isinstance(data, dict):
        report_data_error(
            "队伍文件格式错误（根节点应为 JSON 对象），已忽略：./角色/teams.json")
        data = {}
    teams_json = data

# 每个线程只写入不同的键，则无需额外加锁
# 队伍对象字典 键：队伍名，值：队伍对象
teams = {}

# 根据字典 创建并返回队伍对象
def creat_team(team_info, roles) -> Team:

    if not isinstance(team_info, dict):
        report_data_error("队伍数据格式错误（应为 JSON 对象），已用空值代替")
        team_info = {}
    missing = [k for k in ("logo_path", "name", "description")
               if k not in team_info]
    if missing:
        report_data_error(
            "队伍数据缺少字段：%s（已用空值代替，队伍：%s）"
            % ("、".join(missing), team_info.get("name") or "?"))

    logo_path = team_info.get('logo_path')
    name = team_info.get('name')
    description = team_info.get('description')

    team = Team(
        logo_path,
        name,
        description,
        roles
    )

    return team


def get_team_logo_path(team_name) -> str:
    return f"./角色/{team_name}/{team_name.lower()}.ico"

# 获得 team 对象
def get_team_obj(team_name) -> Team:
    global teams

    load_teams_json()

    # 判断队伍对象是否在字典中，在就复用，不在就生成
    if team_name in teams:
        team = teams[team_name]

    else:

        team_info = teams_json.get(team_name)
        if not isinstance(team_info, dict):
            report_data_error(
                "队伍数据格式错误（应为 JSON 对象），已跳过：%s" % team_name)
            team_info = {}

        team_info_roles = team_info.get('roles')
        if not isinstance(team_info_roles, dict):
            if team_info_roles:
                report_data_error(
                    "队伍「%s」的 roles 不是 JSON 对象，已忽略" % team_name)
            team_info_roles = {}

        # 队伍的角色对象列表；单个角色坏数据只跳过它自己
        roles = []
        for role_key, role_dir in team_info_roles.items():
            if not isinstance(role_dir, dict) or not role_dir.get('path'):
                report_data_error(
                    "角色数据格式错误或缺少 path，已跳过：队伍「%s」/ %s"
                    % (team_name, role_key))
                continue
            try:
                role = creat_role_obj(role_dir['path'])
            except Exception as e:
                report_data_error(
                    "加载角色失败，已跳过：队伍「%s」/ %s\n%s: %s"
                    % (team_name, role_key, type(e).__name__, e))
                continue
            roles.append(role)

        # 生成 team 队伍对象
        team = creat_team(team_info, roles)
        teams[team_name] = team

    return team

# # 加载全部队伍对象
# def get_all_team_obj():
#     load_teams_json()
#     if not teams_json:
#         return
#     if len(teams) == len(teams_json):
#         return

#     for team_name in teams_json:
#         get_team_obj(team_name)

# 使用多线程加载全部队伍对象
def get_all_team_obj():
    load_teams_json()  # 确保 teams_json 已加载
    if not teams_json:
        return

    if len(teams) == len(teams_json):
        return

    # 使用 ThreadPoolExecutor 实现多线程
    with ThreadPoolExecutor() as executor:
        # 提交任务到线程池
        futures = {executor.submit(get_team_obj, team_name): team_name for team_name in teams_json}

        # 等待所有任务完成
        for future in as_completed(futures):
            team_name = futures[future]
            try:
                future.result()  # 获取结果（如果有异常会抛出）
            except Exception as e:
                logger.error(f"加载队伍：{team_name} 时出错: {e}")
                try:
                    from 角色.role_info import report_data_error
                    report_data_error(
                        "加载队伍「%s」时出错（已跳过该队伍的这部分数据）：\n%s: %s"
                        % (team_name, type(e).__name__, e))
                except Exception:
                    pass


def get_role_by_master_name(name) -> Role:
    for team in teams.values():
        for role in team.roles:
            if not role.master_skill:
                continue
            if role.master_skill.name == name:
                return role