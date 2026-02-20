from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pathlib

from tools import init_chrome_driver, add_dicts
# import HBRbrochure.role_info
import HBRbrochure.brochure
from 角色.team_info import get_all_team_obj

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

import threading
global chrome_driver
chrome_driver = None

def list_newline(you_list: list, how_projects_newline: int):
    for i in range(0, len(you_list), how_projects_newline):
        print(", ".join(map(str, you_list[i:i+how_projects_newline])))

def dir_newline(you_dir: dict, how_projects_newline: int):
    line_count = how_projects_newline - 1
    # 初始化计数器
    count = 0
    # 遍历字典的项
    for key, value in you_dir.items():
        # 输出键值对，格式为 "key: value"
        print(f"{key}: {value}", 
            end = ", " if count % how_projects_newline != line_count else "\n")
        count += 1

    # 如果最后一行不足 how_projects_newline 项，需要手动换行
    if count % how_projects_newline != 0:
        print()

def FindKeyByValue(dict: dict, value_to_find: str) -> str | None:
    for key, value in dict.items():
        if value == value_to_find:
            return key
    return None  # 如果没有找到对应的键，则返回None

# 获取风格 id
def get_style_id(style_item_card_element) -> str:
    style_id = ""
    try:
        # 获取 data-id 属性值
        style_id = style_item_card_element.get_attribute('data-id')

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

    return style_id

# 获取风格等级信息
def get_role_level(style_item_card_elements, i):

    style_item_card_element = style_item_card_elements[i]

    current_level = ""
    maximum_level = ""
    try:
        role_level_element = style_item_card_element.find_element(
            By.XPATH, ".//div[contains(@class, 'level')]"
        )
        # 定位 level 元素三个子元素的 data-content 属性
        span_elements = role_level_element.find_elements(
            By.XPATH, ".//span[@data-content]"
        )

        if not role_level_element.is_displayed():
            style_item_card_elements[i-1].location_once_scrolled_into_view

        # 提取元素值
        current_level = span_elements[1].text
        maximum_level = span_elements[2].text

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")    

    return [current_level, maximum_level]

# 获取风格上限突破
def get_limit_break_level(style_item_card_elements, i):

    style_item_card_element = style_item_card_elements[i]

    limit_break_level = '0'
    try:
        limit_break_level_element = style_item_card_element.find_element(
            By.XPATH, ".//div[contains(@class, 'limit-break-level')]"
        )

        if not limit_break_level_element.is_displayed():
            style_item_card_elements[i-1].location_once_scrolled_into_view

        limit_break_level = limit_break_level_element.text

    except Exception as e:
        pass

    return limit_break_level


def get_styles_info(container):

    # 查找类名为 style-item card 的 <div> 元素
    card_box_element = container.find_element(
        By.XPATH, ".//div[contains(@class, 'card-box')]"
    )

    # 查找类名为 style-item card 的 <div> 元素
    style_item_card_elements = card_box_element.find_elements(
        By.XPATH, ".//div[contains(@class, 'style-item') and contains(@class, 'card')]"
    )

    my_style_num = 0
    my_style_ids = []
    my_style_levels = {}
    limit_break_levels = {}
    my_style_infos = {}

    # 获取风格数据
    for i, style_item_card_element in enumerate(style_item_card_elements):
        # 获取风格 id
        my_style_id = get_style_id(style_item_card_element)
        my_style_ids.append(my_style_id)

        # 获取风格等级
        # result = get_role_level(style_item_card_element)
        result = get_role_level(style_item_card_elements, i)
        current_level = result[0]
        maximum_level = result[1].replace("/", "")  # 去掉第二个元素中的 "/"
        my_style_levels[my_style_id] = [current_level, maximum_level]

        # 获取风格上限突破
        limit_break_level = get_limit_break_level(style_item_card_elements, i)
        limit_break_levels[my_style_id] = limit_break_level

        try:
            # my_style_infos[my_style_id] = HBRbrochure.role_info.style_id_all_infos[my_style_id]
            my_style_infos[my_style_id] = {}
            my_style_infos[my_style_id]["current_level"] = current_level
            my_style_infos[my_style_id]["maximum_level"] = maximum_level
            my_style_infos[my_style_id]["limit_break_level"] = limit_break_level
        except KeyError:
            logger.error(f"[-] Missing information on style ID, style ID:   {my_style_id}")
            print("[-] Missing information on style ID, style ID: " + my_style_id)
            continue

        my_style_num += 1

    style_infos_dir = {}
    style_infos_dir["my_style_num"] = my_style_num
    style_infos_dir["my_style_ids"] = my_style_ids
    style_infos_dir["my_style_levels"] = my_style_levels
    style_infos_dir["limit_break_levels"] = limit_break_levels
    style_infos_dir["my_style_infos"] = my_style_infos
    return style_infos_dir



def switch_to_brochure(driver: webdriver.Chrome, style_infos: dict):
    # 使用 JavaScript 打开新标签页
    driver.execute_script(
        "window.open('https://leprechaun-chtholly-nota-seniorious.github.io/HeavenBurnsRedStyleChart.html');"
    )

    # 获取所有窗口句柄
    handles = driver.window_handles
    # 切换到新打开的标签页
    driver.switch_to.window(handles[-1])

    HBRbrochure.brochure.get_brochure(driver, style_infos)


def run_browser_in_thread():
    global chrome_driver

    try:

        # # 获取全部队伍对象
        # get_all_team_obj()

        # 加载资源文件
        # HBRbrochure.role_info.load_resources()
        # 当前脚本路径
        scriptDirectory = pathlib.Path().absolute()

        # 设置 Chrome 选项
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # 无头模式

        # 无痕浏览模式
        # chrome_options.add_argument("--incognito")
        # 忽略 SSL 证书错误
        chrome_options.add_argument("--ignore-certificate-errors")  
        # 禁用控制台日志输出，隐藏自动化标记
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # 设置用户数据目录以保存登录状态
        script_directory = pathlib.Path().absolute()
        data_dir = f"{script_directory}\\工具\\chrome\\chrome_user_data"
        chrome_options.add_argument(f"--user-data-dir={data_dir}")

        # 设置 ChromeDriver 的服务，初始化 Chrome WebDriver
        chrome_driver = init_chrome_driver(chrome_options)
        if chrome_driver == None:
            return

        chrome_driver.set_window_size(1160, 820)
        # 打开 game.bilibili.com
        chrome_driver.get('https://game.bilibili.com/tool/hbr/#/file/more')

        # 等待 class 为 card-box 的元素加载完成
        card_box_element = WebDriverWait(chrome_driver, 300).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "card-box"))
        )

        # 等待 class 为 content 的元素加载完成
        content_element = WebDriverWait(chrome_driver, 300).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "content"))
        )

        container_elements = content_element.find_elements(By.CLASS_NAME, "container")

        SSR_style_infos_dir = get_styles_info(container_elements[0])
        SS_style_infos_dir = get_styles_info(container_elements[1])

        SSR_style_num = SSR_style_infos_dir["my_style_num"]
        SSR_style_ids = SSR_style_infos_dir["my_style_ids"]
        SSR_style_levels = SSR_style_infos_dir["my_style_levels"]
        SSR_limit_break_levels = SSR_style_infos_dir["limit_break_levels"]
        SSR_style_infos = SSR_style_infos_dir["my_style_infos"]

        SS_style_num = SS_style_infos_dir["my_style_num"]
        SS_style_ids = SS_style_infos_dir["my_style_ids"]
        SS_style_levels = SS_style_infos_dir["my_style_levels"]
        SS_limit_break_levels = SS_style_infos_dir["limit_break_levels"]
        SS_style_infos = SS_style_infos_dir["my_style_infos"]

        my_style_num = SSR_style_num + SS_style_num
        my_style_ids = SSR_style_ids + SS_style_ids
        my_style_levels = add_dicts(SSR_style_levels, SS_style_levels)
        limit_break_levels = add_dicts(SSR_limit_break_levels, SS_limit_break_levels)
        my_style_infos = add_dicts(SSR_style_infos, SS_style_infos)

        print(f"[+] 拥有的 SSR 风格数: {len(SSR_style_ids)}")
        print("[+] SSR 风格 ID:")
        list_newline(SSR_style_ids, 6)
        
        print("[+] SSR 风格等级:")
        dir_newline(SSR_style_levels, 3)
        print("[+] SSR 风格上限突破:")
        dir_newline(SSR_limit_break_levels, 6)


        print(f"[+] 拥有的 SS 风格数: {len(SS_style_ids)}")
        print("[+] SS 风格 ID:")
        list_newline(SS_style_ids, 6)
        
        print("[+] SS 风格等级:")
        dir_newline(SS_style_levels, 3)
        print("[+] SS 风格上限突破:")
        dir_newline(SS_limit_break_levels, 6)

        # 打开并切换到新标签页
        switch_to_brochure(chrome_driver, my_style_infos)

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")


def get_hbr_brochure():
    # 获取全部队伍对象
    get_all_team_obj()
    # 启动独立线程执行浏览器操作
    browser_thread = threading.Thread(target=run_browser_in_thread, daemon=False)
    browser_thread.start()