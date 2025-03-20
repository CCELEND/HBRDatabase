import asyncio
import json
import time
import os
import hashlib
import traceback
import base64
from tkinter import messagebox

from tools import creat_directory, str_8bytes_to_int, find_all_substring_positions, confirm_restart

def analyze_file_header(file_header):

    file_header_info = {}

    # 读取文件名长度
    file_name_len_data = file_header[16: 16 + 8]
    file_name_len = str_8bytes_to_int(file_name_len_data)
    # print(f"文件名长度：{file_name_len_data}，{file_name_len}")

    # 读取文件base64编码总长度
    file_content_base64_len_data = file_header[24: 24 + 8]
    file_content_base64_len = str_8bytes_to_int(file_content_base64_len_data)
    # print(f"base64编码总长度：{file_content_base64_len_data}，{file_content_base64_len}")

    # 读取文件名
    file_name_data = file_header[32: 32 + file_name_len]
    file_name = file_name_data.decode('utf-8')
    # print(f"文件名：{file_name}")

    file_header_len = 32 + file_name_len

    file_header_info["file_name_len"] = file_name_len
    file_header_info["file_content_base64_len"] = file_content_base64_len
    file_header_info["file_name"] = file_name
    file_header_info["file_header_len"] = file_header_len

    return file_header_info

# base64 解码保存
def decoding_saving(file_name, file_content_base64_buff):
    # print(file_content_base64_buff)
    # Base64 解码
    file_content = base64.b64decode(file_content_base64_buff)

    creat_directory(file_name)
    # 保存文件
    with open(file_name, 'wb') as f:
        f.write(file_content)

    print(f"更新：'{file_name}'")

def buff_clutter_removal(buff):
    buff = buff.replace(b"\x00",b"")
    buff = buff.replace(b"#",b"")
    buff = buff.replace(b"TRANSFEREND",b"")
    return buff

CHUNKSIZE = 1024
async def send_dict_to_server(current_file_hashes, timeout, host='47.96.235.36', port=65432):
# async def send_dict_to_server(current_file_hashes, timeout, host='106.55.178.101', port=65432):
# async def send_dict_to_server(current_file_hashes, timeout, host='127.0.0.1', port=65432):
    try:
        reader, writer = await asyncio.open_connection(host, port)

        # 将字典转换为 JSON 字符串并编码为字节
        data = json.dumps(current_file_hashes).encode('utf-8')
        # 发送数据长度（4 字节）
        writer.write(len(data).to_bytes(4, 'big'))
        await writer.drain()
        # 分块发送数据，每次发送 1024 字节
        for i in range(0, len(data), CHUNKSIZE):
            chunk = data[i:i + CHUNKSIZE]
            writer.write(chunk)
            await writer.drain()
        # print("[+] 当前文件 hash 已发送到服务器")

        file_content_base64_buff = b""
        file_content_base64_len = 0
        file_name = ""
        trans_flag = False

        # 等待服务端传输
        while True:
            # 使用 asyncio.wait_for 设置超时
            chunk_data = await asyncio.wait_for(reader.read(CHUNKSIZE*2), timeout)
            if not chunk_data:
                break

            # 文件头块
            positions = find_all_substring_positions(b"FILESTART", chunk_data)
            for filestart_index in positions:
                trans_flag = True
                if file_name:
                    if filestart_index-file_content_base64_len >= 0:
                        cut_chunk = chunk_data[filestart_index-file_content_base64_len:filestart_index]
                    else:
                        cut_chunk = chunk_data[:filestart_index]
                    file_content_base64_buff += buff_clutter_removal(cut_chunk)
                    # 解码保存
                    decoding_saving(file_name, file_content_base64_buff)
                    # 清空缓冲区
                    file_content_base64_buff = b""

                # print(f"FILESTART index：{filestart_index}")
                # 解析文件头
                file_header_info = analyze_file_header(chunk_data[filestart_index:])
                file_name_len = file_header_info["file_name_len"]
                file_content_base64_len = file_header_info["file_content_base64_len"]
                file_name = file_header_info["file_name"]
                file_header_len = file_header_info["file_header_len"]

                cut_chunk = chunk_data[filestart_index+file_header_len: filestart_index+file_header_len+file_content_base64_len]
                file_content_base64_buff += buff_clutter_removal(cut_chunk)

            # 纯数据块
            if (not positions) and (b"TRANSFEREND" not in chunk_data):
                file_content_base64_buff += buff_clutter_removal(chunk_data)

            # 传输结束块
            if b"TRANSFEREND" in chunk_data:
                # print(chunk_data)
                if file_name:
                    file_content_base64_buff += buff_clutter_removal(chunk_data)
                    # 解码保存
                    decoding_saving(file_name, file_content_base64_buff)
                    # 清空缓冲区
                    file_content_base64_buff = b""

                if trans_flag:
                    writer.close()
                    await writer.wait_closed()
                    confirm_restart("更新完成")
                else:
                    messagebox.showinfo("提示", "已是最新版本")
                break

    except asyncio.TimeoutError:
        print("[-] 连接超时")
    except ConnectionResetError:
        print("[-] 连接被服务器重置")
    except Exception as e:
        # print(f"[-] 发生错误：文件 {file_name} 下载失败\n{e}")
        traceback.print_exc()  # 这将打印出错误信息和行号
        messagebox.showerror("错误", f"文件 '{file_name}' 下载失败\n请重试 {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        # if trans_flag:
        #     confirm_restart("更新完成")
        
async def send_hashes_to_server(current_file_hashes):
    # 设置超时时间，例如 5 秒
    timeout = 5
    await send_dict_to_server(current_file_hashes, timeout)
