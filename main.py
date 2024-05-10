import socket
import threading
import queue

from my_package.client_handling import handle_client
from my_package.data_returned_handing import process_data

threads = []
# 服务器用
SERVER_HOST = '172.17.233.120'  # 服务器主私网 IP 或主机名
SERVER_PORT = 8000  # 服务器端口

# 本地测试用
# SERVER_HOST = 'localhost'  # 服务器 IP 或主机名
# SERVER_PORT = 12345  # 服务器端口


def receive_data(server_host, server_port):
    """
    :param server_host: 服务器 IP
    :param server_port: 服务器端口
    :return: 无
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_host, server_port))
    server_socket.listen(1)
    data_queue = queue.Queue()

    print(f'Server listening on {server_host}:{server_port}')

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection from {client_address}")
            t1 = threading.Thread(target=handle_client, args=(client_socket, data_queue))  # 启动客户端接收线程
            t1.start()
            threads.append(t1)

            t2 = threading.Thread(target=process_data, args=(data_queue,))  # 启动数据处理线程
            t2.start()
            threads.append(t2)
    except KeyboardInterrupt:
        print("Interrupted by user. Stopping...")
    finally:
        for t in threads:
            t.join()
        server_socket.close()


# 使用示例
receive_data(SERVER_HOST, SERVER_PORT)
