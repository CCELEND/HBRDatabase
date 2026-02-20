
import threading

def creat_new_thread(target_fun: callable):
	# 创建并启动新线程
	thread = threading.Thread(target=target_fun, daemon=True)
	thread.start()

def run_in_thread(func: callable):

	def wrapper():
		func()  # 执行计算任务

	# 创建并启动线程
	thread = threading.Thread(target=wrapper, daemon=True)
	thread.start()