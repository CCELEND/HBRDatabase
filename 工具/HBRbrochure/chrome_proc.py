
from selenium import webdriver

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

def close_browser_completely(driver: webdriver.Chrome):
    """
    完全关闭浏览器，关闭所有标签页和驱动进程
    """
    try:
        # 关闭所有标签页并退出浏览器
        driver.quit()
    except Exception as e:
        logger.error(f"关闭浏览器失败: {e}")

def close_all_tabs(driver: webdriver.Chrome):
    """
    关闭所有标签页，但保持浏览器进程
    """
    try:
        # 获取所有窗口句柄
        window_handles = driver.window_handles
        
        if len(window_handles) > 1:
            # 如果有多个标签页，逐个关闭
            for handle in window_handles[1:]:  # 跳过第一个
                driver.switch_to.window(handle)
                driver.close()
            
            # 切换回第一个标签页
            driver.switch_to.window(window_handles[0])
            
    except Exception as e:
        logger.error(f"关闭标签页失败: {e}")

def close_other_tabs(driver: webdriver.Chrome):
    """
    关闭所有非当前页面的标签页，只保留当前激活的标签页
    """
    try:
        # 获取当前标签页句柄
        current_handle = driver.current_window_handle
        # 获取所有窗口句柄
        all_handles = driver.window_handles

        # 遍历所有标签页，关闭非当前标签页
        for handle in all_handles:
            if handle != current_handle:
                driver.switch_to.window(handle)
                driver.close()

        # 确保最终切回当前标签页
        driver.switch_to.window(current_handle)

    except Exception as e:
        logger.error(f"关闭标签页失败: {e}")
