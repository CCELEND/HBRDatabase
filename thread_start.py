
import threading

def creat_new_thread(target_fun):
	# 创建并启动新线程
	thread = threading.Thread(target=target_fun)
	thread.start()