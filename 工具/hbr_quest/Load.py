
from selenium.webdriver.chrome.options import Options
from tools import init_chrome_driver

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

import threading
global chrome_driver
chrome_driver = None

def run_browser_in_thread():
    global chrome_driver
    try:
        # 设置 Chrome 选项
        chrome_options = Options()
        # chrome_options.add_argument("--headless") # 无头模式

        # 忽略 SSL 证书错误
        chrome_options.add_argument("--ignore-certificate-errors")  
        # 禁用控制台日志输出，隐藏自动化标记
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # 设置 ChromeDriver 的服务，初始化 Chrome WebDriver
        chrome_driver = init_chrome_driver(chrome_options)
        if chrome_driver == None:
            return

        chrome_driver.set_window_size(1160, 820)
        chrome_driver.get("https://hbr.quest/")

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")


def load_hbr_quest():
    # 启动独立线程执行浏览器操作
    browser_thread = threading.Thread(target=run_browser_in_thread, daemon=False)
    browser_thread.start()