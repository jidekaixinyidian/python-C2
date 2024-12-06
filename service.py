from socket import *
from threading import Thread, Lock
import os

# 配置
IP = '0.0.0.0'
PORT = 50000
BUFLEN = 4096

# 共享资源
id_counter = 1  # 客户端编号
clients = []  # 存储已连接客户端的信息
Flag = True  # 服务端运行状态
lock = Lock()  # 线程锁，保护共享资源

def handle_client(dataSocket, addr, cid):
    """处理单个客户端的通信"""
    global clients
    print(f"客户端连接：{addr}，编号：{cid}")

    try:
        while True:
            recved = dataSocket.recv(BUFLEN)
            if not recved:
                print(f"客户端 {cid} 已断开")
                break

            recved_decoded = recved.decode('utf-8', errors='ignore')
            print(f"收到客户端 {cid} 的数据：{recved_decoded}")

            # 回应客户端
            dataSocket.send(f"服务端回应：{recved_decoded}".encode('utf-8'))
    except Exception as e:
        print(f"处理客户端 {cid} 时出错：{e}")
    finally:
        # 移除断开连接的客户端
        with lock:
            clients = [client for client in clients if client['id'] != cid]
        dataSocket.close()
        print(f"客户端 {cid} 的线程已终止")

def listen():
    """监听客户端连接并创建线程处理"""
    global Flag
    listenSocket = socket(AF_INET, SOCK_STREAM)
    listenSocket.bind((IP, PORT))
    listenSocket.listen(5)
    print(f'服务端已启动，正在监听 {PORT} 端口')

    try:
        while Flag:
            listenSocket.settimeout(1)  # 设置超时以检查退出标志
            try:
                dataSocket, addr = listenSocket.accept()
            except timeout:
                continue

            with lock:
                global id_counter
                cid = id_counter
                id_counter += 1
                clients.append({'id': cid, 'addr': addr, 'socket': dataSocket})

            # 为每个客户端创建单独线程处理
            client_thread = Thread(target=handle_client, args=(dataSocket, addr, cid))
            client_thread.daemon = True  # 守护线程
            client_thread.start()
    finally:
        listenSocket.close()

def client_list():
    """打印当前已连接的客户端列表"""
    print('当前已连接的客户端：')
    with lock:
        if not clients:
            print("没有已连接的客户端")
        for client in clients:
            print(f"编号：{client['id']}，地址：{client['addr']}")

def close_client(cid):
    """关闭指定客户端的连接"""
    global clients
    with lock:
        target_client = next((client for client in clients if client['id'] == cid), None)
        if target_client:
            try:
                target_client['socket'].close()
                clients = [client for client in clients if client['id'] != cid]
                print(f"客户端 {cid} 已关闭")
            except Exception as e:
                print(f"关闭客户端 {cid} 时出错：{e}")

def cmd():
    """向指定客户端发送命令"""
    while True:
        if not clients:
            print("当前没有已连接的客户端！")
            return

        # 列出已连接客户端
        print("当前已连接的客户端：")
        with lock:
            for client in clients:
                print(f"编号：{client['id']}，地址：{client['addr']}")

        # 选择客户端
        try:
            target_id = int(input("输入目标客户端编号（输入0返回主菜单）："))
            if target_id == 0:
                return
        except ValueError:
            print("请输入有效的编号！")
            continue

        # 查找目标客户端
        with lock:
            target_client = next((client for client in clients if client['id'] == target_id), None)
        if not target_client:
            print(f"客户端 {target_id} 不存在，请重新选择！")
            continue

        # 发送命令
        try:
            command = input(f"向客户端 {target_id} 发送命令（输入'back'返回主菜单）：")
            if command.lower() == 'back':
                return

            target_client['socket'].send(command.encode('utf-8'))

            # 如果命令为 exit，则关闭该客户端
            if command.lower() == 'exit':
                close_client(target_id)
                return

            # 接收客户端的响应
            response = target_client['socket'].recv(BUFLEN).decode('utf-8', errors='ignore')
            print(f"客户端 {target_id} 响应：{response}")
        except Exception as e:
            print(f"与客户端 {target_id} 通信时出错：{e}")
            return

def close_all_clients():
    """关闭所有客户端连接"""
    global clients
    with lock:
        for client in clients:
            try:
                client['socket'].close()
            except Exception as e:
                print(f"关闭客户端 {client['id']} 时出错：{e}")
        clients = []

def menu():
    """显示服务端菜单"""
    print("\n-----------------------------------")
    print('1. 查看已连接的客户端')
    print('2. 向指定客户端发送命令')
    print('3. 退出并关闭服务端')

# 启动监听线程
listener_thread = Thread(target=listen)
listener_thread.start()

# 服务端主控制循环
try:
    while True:
        menu()
        try:
            choice = int(input("输入选择："))
            if choice == 1:
                client_list()
            elif choice == 2:
                cmd()
            elif choice == 3:
                print("正在关闭所有客户端和服务端...")
                close_all_clients()
                Flag = False  # 停止监听线程
                break
            else:
                print("请输入有效的选项！")
        except ValueError:
            print("请输入数字选项！")
finally:
    # 等待监听线程退出
    listener_thread.join()
    print("服务端已成功退出")
