
from selenium.webdriver.chrome.options import Options
from tools import init_chrome_driver

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

def load_game8_hbr():
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
        driver = init_chrome_driver(chrome_options)
        if driver == None:
            return

        driver.set_window_size(1160, 820)
        driver.get("https://game8.jp/heavenburnsred")

    except Exception as e:
        logger.error(str(e))
        print(f"[-] {e}")


