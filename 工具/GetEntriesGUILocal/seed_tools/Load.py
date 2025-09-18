

import subprocess


from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

def load_seed_tools():
    seed_tools_path = "./工具/GetEntriesGUILocal/seed_tools/seed_tools.exe"
    try:
        subprocess.run(seed_tools_path)
    except Exception as e:
        print(f"[-] {e}")
        logger.error(str(e))


