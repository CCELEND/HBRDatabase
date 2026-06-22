import pathlib

from selenium.webdriver.chrome.options import Options
from tools import delete_all_files_and_subdirs, delete_file

import os
from tools import init_chrome_driver, unzip_file, check_dir_exists_pathlib
from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

import threading
global chrome_driver
chrome_driver = None

def run_browser_in_thread():
    global chrome_driver
    try:
        
        if not check_dir_exists_pathlib('./工具/HBR伤害模拟/2.1.0_0'):
            unzip_file(os.path.abspath('./工具/HBR伤害模拟/2.1.0_0.zip'), os.path.abspath('./工具/HBR伤害模拟'))

        # 设置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument("--ignore-certificate-errors")  
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        extension_path = os.path.abspath('./工具/HBR伤害模拟/2.1.0_0')
        chrome_options.add_argument(f"--load-extension={extension_path}")

        # 设置用户数据目录
        script_directory = pathlib.Path().absolute()
        data_dir = f"{script_directory}\\工具\\chrome\\chrome_user_data"
        chrome_options.add_argument(f"--user-data-dir={data_dir}")

        # 初始化driver
        chrome_driver = init_chrome_driver(chrome_options)
        if chrome_driver is None:
            return

        chrome_driver.set_window_size(1160, 820)
        chrome_driver.get("chrome://extensions/")

        from time import sleep
        # 等待浏览器被关闭
        while True:
            try:
                chrome_driver.window_handles
            except:
                break
            sleep(0.5)
        chrome_driver.quit()

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

def load_hbr_damage_simulation():
    # 启动独立线程执行浏览器操作
    browser_thread = threading.Thread(target=run_browser_in_thread, daemon=False)
    browser_thread.start()