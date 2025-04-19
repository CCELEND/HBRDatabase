
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

import time
import role_info

from HBRbrochure.role_info import team_id_names, role_id_names, style_id_all_infos
from HBRbrochure.brochure import get_brochure

def list_newline(you_list, how_projects_newline):
    for i in range(0, len(you_list), how_projects_newline):
        print(", ".join(map(str, you_list[i:i+how_projects_newline])))

def dir_newline(you_dir, how_projects_newline):
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

def FindKeyByValue(dict, value_to_find):
    for key, value in dict.items():
        if value == value_to_find:
            return key
    return None  # 如果没有找到对应的键，则返回None

# 获取风格 id
def get_style_id(style_item_card_element):
    style_id = ""
    try:
        # 获取 data-id 属性值
        style_id = style_item_card_element.get_attribute('data-id')

    except Exception as e:
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


def switch_to_brochure(driver, style_infos):
    # 使用 JavaScript 打开新标签页
    driver.execute_script(
        "window.open('https://leprechaun-chtholly-nota-seniorious.github.io/HeavenBurnsRedStyleChart.html');"
    )

    # 获取所有窗口句柄
    handles = driver.window_handles
    # 切换到新打开的标签页
    driver.switch_to.window(handles[-1])

    get_brochure(driver, style_infos)


def get_hbr_brochure():

    try:
        # 设置 Chrome 选项以在后台运行
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        # 设置 ChromeDriver 的服务
        chromedriver_path = "./工具/HBRbrochure/chromedriver-win64/chromedriver.exe"
        # service = Service(executable_path=ChromeDriverManager().install())
        service = Service(executable_path=chromedriver_path)
        # 初始化 Chrome WebDriver
        driver = webdriver.Chrome(service=service)

        # 打开 game.bilibili.com
        driver.get('https://game.bilibili.com/tool/hbr/#/file/more')

        # 等待 class 为 card-box 的元素加载完成
        card_box_element = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "card-box"))
        )


        # 查找类名为 style-item card 的 <div> 元素
        style_item_card_elements = card_box_element.find_elements(
            By.XPATH, ".//div[contains(@class, 'style-item') and contains(@class, 'card')]"
        )


        my_style_num = 0
        my_style_ids = []
        my_style_png_srcs = {}
        my_style_character_roles = {}
        my_style_element_types = {}
        my_style_weapon_types = {}
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
                my_style_infos[my_style_id] = style_id_all_infos[my_style_id]
                my_style_infos[my_style_id]["current_level"] = current_level
                my_style_infos[my_style_id]["maximum_level"] = maximum_level
                my_style_infos[my_style_id]["limit_break_level"] = limit_break_level
            except KeyError:
                print("[-] Missing information on style ID, please modify the role_info.py file, style ID: " + my_style_id)
                continue

            my_style_num += 1

        print(f"[+] 拥有的 SS 风格数: {len(my_style_ids)}")
        print("[+] SS 风格 ID:")
        list_newline(my_style_ids, 6)
        
        print("[+] SS 风格等级:")
        dir_newline(my_style_levels, 3)
        print("[+] SS 风格上限突破:")
        dir_newline(limit_break_levels, 6)

        # 打开并切换到新标签页
        switch_to_brochure(driver, my_style_infos)

    except Exception as e:
        print(f"[-] {e}")


