
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from tools import delete_all_files_and_subdirs, delete_file

import os

def load_hbr_damage_simulation():
    try:
        delete_all_files_and_subdirs(os.path.abspath('./工具/HBR伤害模拟/1.3.0_0'))
        delete_file(os.path.abspath('./工具/HBR伤害模拟/1.3.0_0.crx'))


        # 设置 Chrome 选项
        chrome_options = Options()
        # chrome_options.add_argument("--headless") # 无头模式

        # 忽略 SSL 证书错误
        chrome_options.add_argument("--ignore-certificate-errors")  
        # 禁用控制台日志输出，隐藏自动化标记
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # 插件绝对路径
        extension_path = os.path.abspath('./工具/HBR伤害模拟/1.4.0_0')
        chrome_options.add_argument(f'--load-extension={extension_path}')
        # 添加开发者模式参数
        chrome_options.add_argument('--disable-extensions-except=' + extension_path)

        # 加载插件
        # chrome_options.add_extension('./工具/HBR伤害模拟/1.3.0_0.crx')
        # chrome_options.add_argument('--load-extension=./工具/HBR伤害模拟/1.3.0_0')

        # 设置 ChromeDriver 的服务，初始化 Chrome WebDriver
        try:
            chromedriver_path = "./工具/HBRbrochure/chromedriver-win64/chromedriver.exe"
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            service = Service(executable_path=ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.set_window_size(1160, 820)
        # driver.get("chrome://extensions/jiakmnjmdhncjjobkjlipbcdgjidgffa")
        driver.get("chrome://extensions/")

    except Exception as e:
        print(f"[-] {e}")


