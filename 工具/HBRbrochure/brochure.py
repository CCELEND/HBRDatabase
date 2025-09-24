

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

# from HBRbrochure.mapping import GetBrochureIdByStyleId
import HBRbrochure.mapping

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

from 角色.style_info import get_en_by_id

def switch_cn(driver):
    try:
        # 找到切换图鉴的元素，初始是国际服JP
        data_switch_element = driver.find_element(By.XPATH, "//*[text()='JP']")
        data_switch_element.click()

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

# 切换全屏
def switch_full_screen(driver):
    try:
        # 找到切换全屏元素，使用 XPath 查找包含 base64 编码的 background-image 属性的元素
        full_screen_element = driver.find_element(By.XPATH, "//*[contains(@style, 'background-image: url(\"data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48IS0tIFVwbG9hZGVkIHRvOiBTVkcgUmVwbywgd3d3LnN2Z3JlcG8uY29tLCBHZW5lcmF0b3I6IFNWRyBSZXBvIE1peGVyIFRvb2xzIC0tPgo8c3ZnIHdpZHRoPSI4MDBweCIgaGVpZ2h0PSI4MDBweCIgdmlld0JveD0iMCAwIDMyIDMyIiBpZD0iaS1mdWxsc2NyZWVuIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGZpbGw9Im5vbmUiIHN0cm9rZT0iY3VycmVudGNvbG9yIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIHN0cm9rZS13aWR0aD0iMiI+CiAgICA8cGF0aCBkPSJNNCAxMiBMNCA0IDEyIDQgTTIwIDQgTDI4IDQgMjggMTIgTTQgMjAgTDQgMjggMTIgMjggTTI4IDIwIEwyOCAyOCAyMCAyOCIgLz4KPC9zdmc+\");')]")

        full_screen_element.click()

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")


def web_abbreviation(driver, zoom_percentage):
    try:
        driver.execute_script(f"document.body.style.zoom = '{zoom_percentage}%'")

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

def click_brochure(driver, my_style_infos):
    try:
        for style_id in my_style_infos:
            try:
                # brochure_id = GetBrochureIdByStyleId(style_id)
                brochure_id = get_en_by_id(style_id)
            except KeyError:
                logger.error(f"[-] Missing mapping, please modify the style_id_brochure_id.json file, style ID: {style_id}")
                print("[-] Missing mapping, please modify the style_id_brochure_id.json file, style ID: " + style_id)
                continue
            limit_break_level = int(my_style_infos[style_id]["limit_break_level"])

            # 查找 id 名为 brochure_id 的元素，如果没有找到说明国服图鉴还没有更新
            try:
                style_element = driver.find_element(By.ID, brochure_id)
            except NoSuchElementException:
                logger.error(f"[-] No such style element, ID:  {brochure_id}")
                print("[-] No such style element, ID: " + brochure_id)
                continue

            # 模拟点击 limit_break_level+1 次
            for _ in range(limit_break_level+1):
                style_element.click()

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

def download_brochure(driver):
    try:
        # 找到下载图鉴的元素，使用 XPath 查找包含 base64 编码的 background-image 属性的元素
        download_element = driver.find_element(By.XPATH, "//*[contains(@style, 'background-image: url(\"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAALgAAAC4AQMAAABq/bSEAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAGUExURQAAAP///6XZn90AAAAJcEhZcwAADsIAAA7CARUoSoAAAAF1SURBVFjD7dYxUsUgEAbgn6FImSPkKPEoHsHSwpF4s1h5DOlssYszmSDZTYC3kNHRFvKq7zHwL0P2Pfj6aN68+d/848JfLny6cJjmzZs3L/3r8Hfh1rB30kfyTQufB/JVSe/Jl8I7cle4JrdyfavIZ+kO5JPMuQTcP73wFWPwDYPwXWD2b299XwFmiUcXPewI49I0nwqAsarwQDAxPvsbFwBD8T+jay4gPHv82ZyuuAA8U/zom+IC8ETxp/F0cAF4pPjJFReAB5ogfNa4VxW3Cne64g5AV/EleF/xNfhQ8S34WHEf3NR8Ah+u9Bmq6ha66o7jF74cl0f6elwe6dtxeaSf713hx+914a8X7n/r+J+bH1z8eUFy8w/f0tLTeOFD5uuFc6shn/u62y5zp5PrzG1ylx80txr2m47aR18wZDGTr0gbWJ5Dvl/9NMbo/sZN8il3n9xmrDN3mXeZr5kPmXu57elWLJP688Gyn8vRvHlzObz/BhLP4gc16GgKAAAAAElFTkSuQmCC\");')]")
        download_element.click()

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

# 按下 esc 键
def press_esc(driver):
    try:
        # 使用 ActionChains 模拟按下 ESC 键
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

def get_brochure(driver, style_infos):

    # 加载资源文件
    HBRbrochure.mapping.load_resources()
    try:
        # 等待立华奏加载完成 绝对不是因为我是一个奏厨（
        TachibanaKanadeElement = WebDriverWait(driver, 300).until(
            EC.visibility_of_element_located((By.ID, "AliceADefault_R3"))
        )
        
    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

    # 切换国服
    switch_cn(driver)

    # 网页缩略到50%
    web_abbreviation(driver, 50)

    # 点击图鉴
    click_brochure(driver, style_infos)

    # 下载图鉴
    download_brochure(driver)

    driver.delete_all_cookies()  # 清除所有cookies
    driver.execute_script('window.localStorage.clear();')  # 清除localStorage
    driver.execute_script('window.sessionStorage.clear();')  # 清除sessionStorage





