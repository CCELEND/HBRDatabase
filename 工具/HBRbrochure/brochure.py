
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

from time import sleep

from HBRbrochure.mapping import GetBrochureIdByStyleId
# import HBRbrochure.mapping
from HBRbrochure.chrome_proc import clear_data_and_cookies

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

from 角色.style_info import get_en_by_id

def switch_cn(driver: webdriver.Chrome):
    try:
        CN_elements = driver.find_elements(By.XPATH, "//*[text()='CN']")
        
        # 如果已经是 CN，直接退出
        if len(CN_elements) > 0: return

        # 如果不是 CN，就找 JP 并点击切换
        JP_elements = driver.find_elements(By.XPATH, "//*[text()='JP']")
        if len(JP_elements) > 0:
            JP_elements[0].click()
            print("[+] 已切换到 CN")

    except Exception as e:
        logger.error(str(e))
        print(f"[-] 切换失败: {e}")


# 切换全屏
def switch_full_screen(driver: webdriver.Chrome):
    try:
        # 找到切换全屏元素，使用 XPath 查找包含 base64 编码的 background-image 属性的元素
        full_screen_element = driver.find_element(By.XPATH, "//*[contains(@style, 'background-image: url(\"data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48IS0tIFVwbG9hZGVkIHRvOiBTVkcgUmVwbywgd3d3LnN2Z3JlcG8uY29tLCBHZW5lcmF0b3I6IFNWRyBSZXBvIE1peGVyIFRvb2xzIC0tPgo8c3ZnIHdpZHRoPSI4MDBweCIgaGVpZ2h0PSI4MDBweCIgdmlld0JveD0iMCAwIDMyIDMyIiBpZD0iaS1mdWxsc2NyZWVuIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGZpbGw9Im5vbmUiIHN0cm9rZT0iY3VycmVudGNvbG9yIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIHN0cm9rZS13aWR0aD0iMiI+CiAgICA8cGF0aCBkPSJNNCAxMiBMNCA0IDEyIDQgTTIwIDQgTDI4IDQgMjggMTIgTTQgMjAgTDQgMjggMTIgMjggTTI4IDIwIEwyOCAyOCAyMCAyOCIgLz4KPC9zdmc+\");')]")

        full_screen_element.click()

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")


def web_abbreviation(driver: webdriver.Chrome, zoom_percentage: int):
    try:
        driver.execute_script(f"document.body.style.zoom = '{zoom_percentage}%'")

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")



def click_style_element(driver, style_id, limit_break_level):
    try:
        # brochure_id = get_en_by_id(style_id)
        brochure_id = GetBrochureIdByStyleId(style_id)
    except KeyError:
        logger.error(f"[-] Missing mapping, style ID: {style_id}")
        print("[-] Missing mapping, style ID: " + style_id)
        return False
    
    try:
        style_element = driver.find_element(By.ID, brochure_id)
        # 模拟点击 limit_break_level+1 次
        for _ in range(limit_break_level + 1):
            style_element.click()
        # logger.info(f"[+] Successfully clicked style ID: {style_id} ({brochure_id})")
        return True
    except NoSuchElementException:
        logger.error(f"[-] No such style element, ID:  {brochure_id}")
        print("[-] No such style element, ID: " + brochure_id)
        return False
    except Exception as e:
        logger.error(f"[-] Error clicking style {style_id}: {str(e)}")
        print(f"[-] Error clicking style {style_id}: {e}")
        return False


def process_style_chunk(driver: webdriver.Chrome, chunk_data):
    chunk_style_infos, thread_id = chunk_data
    success_count = 0
    fail_count = 0
    
    try:
        # driver = init_thread_driver()
        # logger.info(f"[+] 线程 {thread_id} 启动，处理 {len(chunk_style_infos)} 个风格")
        
        # 处理当前分片的所有style
        for style_id, info in chunk_style_infos.items():
            limit_break_level = int(info["limit_break_level"])
            try:
                brochure_id = get_en_by_id(style_id)
                style_element = driver.find_element(By.ID, brochure_id)
                # 模拟点击
                for _ in range(limit_break_level + 1):
                    style_element.click()
                success_count += 1
            except KeyError:
                logger.error(f"[-] 线程 {thread_id} - 缺失映射: {style_id}")
                fail_count += 1
            except NoSuchElementException:
                logger.error(f"[-] 线程 {thread_id} - 元素不存在: {brochure_id}")
                fail_count += 1
            except Exception as e:
                logger.error(f"[-] 线程 {thread_id} - 处理 {style_id} 失败: {e}")
                fail_count += 1
        
        return {
            "thread_id": thread_id,
            "success": success_count,
            "fail": fail_count,
            "total": len(chunk_style_infos)
        }
    
    except Exception as e:
        logger.error(f"[-] 线程 {thread_id} 执行失败: {e}")
        return {
            "thread_id": thread_id,
            "success": 0,
            "fail": len(chunk_style_infos),
            "total": len(chunk_style_infos),
            "error": str(e)
        }

def click_brochure_by_chunk(driver: webdriver.Chrome, style_infos: dict, thread_count=4):
    # 将字典拆分为多个分片
    style_items = list(style_infos.items())
    chunk_size = (len(style_items) + thread_count - 1) // thread_count  # 向上取整
    chunks = []
    
    for i in range(thread_count):
        # 切片并转换回字典
        start = i * chunk_size
        end = min((i + 1) * chunk_size, len(style_items))
        chunk_dict = dict(style_items[start:end])
        if chunk_dict:  # 跳过空分片
            chunks.append((chunk_dict, i + 1))
    
    # 多线程执行分片任务
    results = []
    with ThreadPoolExecutor(max_workers=len(chunks)) as executor:
        # 提交所有分片任务
        future_to_chunk = {
            executor.submit(process_style_chunk, driver, chunk_data): chunk_data[1]
            for chunk_data in chunks
        }
        
        # 收集结果
        for future in as_completed(future_to_chunk):
            thread_id = future_to_chunk[future]
            try:
                result = future.result()
                results.append(result)
                # logger.info(f"[+] 线程 {thread_id} 完成: 成功{result['success']} / 失败{result['fail']}")
            except Exception as e:
                logger.error(f"[-] 线程 {thread_id} 结果获取失败: {e}")
    
    # 汇总结果
    total_success = sum(r["success"] for r in results)
    total_fail = sum(r["fail"] for r in results)
    # logger.info(f"[+] 所有线程执行完成 - 总计: 成功{total_success} / 失败{total_fail}")
    return {
        "total_success": total_success,
        "total_fail": total_fail,
        "thread_results": results
    }

from concurrent.futures import ThreadPoolExecutor, as_completed
def click_brochure_multithread(driver: webdriver.Chrome, style_infos: dict, max_workers=4):
    # 将任务拆分为列表
    tasks = []
    for style_id, info in style_infos.items():
        limit_break_level = int(info["limit_break_level"])
        tasks.append((style_id, limit_break_level))
    
    # 使用线程池执行任务
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_task = {
            executor.submit(click_style_element, driver, style_id, limit_break_level): (style_id, limit_break_level)
            for style_id, limit_break_level in tasks
        }
        
        # 收集执行结果
        for future in as_completed(future_to_task):
            style_id, _ = future_to_task[future]
            try:
                success = future.result()
                results.append((style_id, success))
            except Exception as e:
                logger.error(f"[-] Task for style {style_id} failed: {str(e)}")
                results.append((style_id, False))
    
    # 统计执行结果
    # success_count = sum(1 for _, success in results if success)
    # fail_count = len(results) - success_count
    # logger.info(f"[+] Multithread click completed: {success_count} succeeded, {fail_count} failed")
    return results

def click_brochure(driver: webdriver.Chrome, my_style_infos: dict):
    try:
        for style_id in my_style_infos:
            try:
                brochure_id = GetBrochureIdByStyleId(style_id)
                # brochure_id = get_en_by_id(style_id)
            except KeyError:
                logger.error(f"[-] Missing mapping, style ID: {style_id}")
                print("[-] Missing mapping, style ID: " + style_id)
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

def download_brochure(driver: webdriver.Chrome):
    try:
        # 找到下载图鉴的元素，使用 XPath 查找包含 base64 编码的 background-image 属性的元素
        download_element = driver.find_element(By.XPATH, "//*[contains(@style, 'background-image: url(\"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAALgAAAC4AQMAAABq/bSEAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAGUExURQAAAP///6XZn90AAAAJcEhZcwAADsIAAA7CARUoSoAAAAF1SURBVFjD7dYxUsUgEAbgn6FImSPkKPEoHsHSwpF4s1h5DOlssYszmSDZTYC3kNHRFvKq7zHwL0P2Pfj6aN68+d/848JfLny6cJjmzZs3L/3r8Hfh1rB30kfyTQufB/JVSe/Jl8I7cle4JrdyfavIZ+kO5JPMuQTcP73wFWPwDYPwXWD2b299XwFmiUcXPewI49I0nwqAsarwQDAxPvsbFwBD8T+jay4gPHv82ZyuuAA8U/zom+IC8ETxp/F0cAF4pPjJFReAB5ogfNa4VxW3Cne64g5AV/EleF/xNfhQ8S34WHEf3NR8Ah+u9Bmq6ha66o7jF74cl0f6elwe6dtxeaSf713hx+914a8X7n/r+J+bH1z8eUFy8w/f0tLTeOFD5uuFc6shn/u62y5zp5PrzG1ylx80txr2m47aR18wZDGTr0gbWJ5Dvl/9NMbo/sZN8il3n9xmrDN3mXeZr5kPmXu57elWLJP688Gyn8vRvHlzObz/BhLP4gc16GgKAAAAAElFTkSuQmCC\");')]")
        download_element.click()

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

# 按下 esc 键
def press_esc(driver: webdriver.Chrome):
    try:
        # 使用 ActionChains 模拟按下 ESC 键
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

def get_brochure(driver: webdriver.Chrome, style_infos: dict):

    # 加载资源文件
    # HBRbrochure.mapping.load_resources()
    try:
        # 等待立华奏加载完成 绝对不是因为我是一个奏厨（
        TachibanaKanadeElement = WebDriverWait(driver, 300).until(
            EC.visibility_of_element_located((By.ID, "ab-1-2"))
        )
        
    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

    # 切换国服
    switch_cn(driver)

    sleep(1)

    # 网页缩略到60%
    web_abbreviation(driver, 60)

    # 点击图鉴
    # click_brochure(driver, style_infos)
    click_brochure_multithread(driver, style_infos, max_workers=4)
    # click_brochure_by_chunk(driver, style_infos, thread_count=8)

    # 下载图鉴
    download_brochure(driver)

    clear_data_and_cookies(driver)
