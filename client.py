import csv
import socket
import time
import struct

FILENAME = '../data/56500be4/2022-12-16-00.csv'  # 你要发送的 CSV 文件名
# 服务器用
# SERVER_HOST = '47.109.38.244'  # 服务器 IP 或主机名
# SERVER_PORT = 8000  # 服务器端口

# 本地测试用
SERVER_HOST = 'localhost'  # 服务器 IP 或主机名
SERVER_PORT = 12345  # 服务器端口


def send_row_data(filename, server_host, server_port, delay=0.001):
    # 建立客户端套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))

    try:
        # 打开 CSV 文件
        with open(filename, 'r') as file:
            csv_reader = csv.reader(file)
            # 读取 CSV 文件的所有数据
            data = list(csv_reader)
            # 逐行发送数据
            for row in data[1:]:  # 从第二行开始循环，因为第一行通常是列标题
                # 将整行数据转换为适当的格式（例如 CSV、JSON、XML）
                row_data = ','.join(row[1:-1])  # 以逗号分隔的行数据
                # 发送当前行数据的长度作为消息头
                message_length = len(row_data)
                length_header = struct.pack('!I', message_length)
                client_socket.send(length_header)
                # 发送当前行数据
                client_socket.send(row_data.encode())
                # 停顿一段时间
                time.sleep(delay)
    except Exception as e:
        print("Error:", e)
    finally:
        # 关闭套接字
        client_socket.close()


# 使用示例
send_row_data(FILENAME, SERVER_HOST, SERVER_PORT)
