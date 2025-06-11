from tools import load_json, get_dir_values_list
from role_info import creat_role_obj

from concurrent.futures import ThreadPoolExecutor, as_completed

# 队伍
class Team:
    def __init__(self, logo_path = None, 
        name = None, description = None, roles = None
        ):
        self.logo_path = logo_path                  # 队伍头像路径
        self.name = name                            # 队伍名
        self.description = description              # 队伍描述
        self.roles = roles                          # 角色对象列表


teams_json = {}
# 加载资源文件
def load_teams_json():
    global teams_json

    if teams_json:
        return

    teams_json = load_json("./角色/teams.json")

# 每个线程只写入不同的键，则无需额外加锁
# 队伍对象字典 键：队伍名，值：队伍对象
teams = {}

# 根据字典 创建并返回队伍对象
def creat_team(team_info, roles):

    logo_path = team_info['logo_path']
    name = team_info['name']
    description = team_info['description']

    team = Team(
        logo_path,
        name,
        description,
        roles
    )

    return team

# 获得 team 对象
def get_team_obj(team_name):
    global teams

    load_teams_json()

    # 判断队伍对象是否在字典中，在就复用，不在就生成
    if team_name in teams:
        team = teams[team_name]

    else:

        team_info = teams_json[team_name]

        team_info_roles = team_info['roles']
        roles_dir_list = get_dir_values_list(team_info_roles)

        # 队伍的角色对象列表
        roles = []
        # 遍历队伍字典列表
        for role_dir in roles_dir_list:
            # 获取角色资源的路径
            role_path = role_dir['path']

            role = creat_role_obj(role_path)
            roles.append(role)

        # 生成 team 队伍对象
        team = creat_team(team_info, roles)
        teams[team_name] = team

    return team

# # 加载全部队伍对象
# def get_all_team_obj():

#     load_teams_json()

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
                print(f"加载队伍：{team_name} 时出错: {e}")


