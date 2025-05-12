
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

def load_hbr_damage_simulation():
    try:
        # 设置 Chrome 选项以在后台运行
        chrome_options = Options()
        # chrome_options.add_argument("--headless")

        # 忽略 SSL 证书错误
        chrome_options.add_argument("--ignore-certificate-errors")  
        # 忽略 Bluetooth: bluetooth_adapter_winrt.cc:1075 Getting Default Adapter failed. 错误
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 忽略 DevTools listening on ws://127.0.0.1... 提示
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 加载插件
        chrome_options.add_extension('./工具/HBR伤害模拟/1.3.0_0.crx')

        # 设置 ChromeDriver 的服务，初始化 Chrome WebDriver
        try:
            chromedriver_path = "./工具/HBRbrochure/chromedriver-win64/chromedriver.exe"
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            service = Service(executable_path=ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service)

        driver.get("chrome://extensions/jiakmnjmdhncjjobkjlipbcdgjidgffa")

    except Exception as e:
        print(f"[-] {e}")


