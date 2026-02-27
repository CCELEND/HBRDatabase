from selenium.webdriver.chrome.options import Options
from tools import delete_all_files_and_subdirs, delete_file

import os
from tools import init_chrome_driver
from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

import threading
global chrome_driver
chrome_driver = None

def run_browser_in_thread():
    global chrome_driver
    try:
        # 清理文件
        delete_all_files_and_subdirs(os.path.abspath('./工具/HBR伤害模拟/1.3.0_0'))
        delete_file(os.path.abspath('./工具/HBR伤害模拟/1.3.0_0.crx'))
        delete_all_files_and_subdirs(os.path.abspath('./工具/HBR伤害模拟/1.4.0_0'))
        delete_all_files_and_subdirs(os.path.abspath('./工具/HBR伤害模拟/1.4.1_0'))

        # 设置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument("--ignore-certificate-errors")  
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        extension_path = os.path.abspath('./工具/HBR伤害模拟/1.7.0_0')
        chrome_options.add_argument(f"--load-extension={extension_path}")

        # 初始化driver
        chrome_driver = init_chrome_driver(chrome_options)
        if chrome_driver is None:
            return

        chrome_driver.set_window_size(1160, 820)
        chrome_driver.get("chrome://extensions/")

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")

def load_hbr_damage_simulation():
    # 启动独立线程执行浏览器操作
    browser_thread = threading.Thread(target=run_browser_in_thread, daemon=False)
    browser_thread.start()