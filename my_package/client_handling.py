import struct
import time
import numpy as np

save_of_data = []  # 保存接收到的数据
current_save_of_data = []  # 保存接收到的数据


def handle_client(client_socket, data_queue):
    """
    接收并处理客户端数据
    为保证数据完整性，每次接收 2000 个数据后进行处理，不宜过大，不然会导致一次截取两个周期数据
    请尽量保证数据每次只接收一个周期
    """
    while True:
        # socket接收数据
        message_length = client_socket.recv(4)
        data_length = struct.unpack('!I', message_length)[0]
        received_data = client_socket.recv(data_length)
        if not received_data:
            print('No data received from client')
            break

        # 将接收到的数据转换进行拆分
        data_with_timestamp = list(map(float, received_data.decode().split(',')))
        # 去掉时间戳
        data_without_timestamp = data_with_timestamp[:-1]
        current_save_of_data.append(data_without_timestamp)
        # 只保留每个周期的第一个时间戳
        if len(current_save_of_data) < 2:
            timestamp = data_with_timestamp[-1]
        if len(current_save_of_data) > 2000:
            # 采用主轴1的数据判断周期是否完整
            Axis_1 = [row[0] for row in current_save_of_data]
            # 保证最后的50个点为非睡眠点
            non_sleep_indices = np.where(np.array(Axis_1[-50:]) > 50)[0]
            if len(non_sleep_indices) > 0:
                continue
            else:
                # 将数据放入队列并清空当前接收数据
                # save_of_data用于存储已接收的所有数据
                # 在代码中暂未进行使用
                while not current_save_of_data:
                    time.sleep(0.5)
                save_of_data.append(Axis_1.copy())
                data_queue.put((current_save_of_data.copy(), timestamp))
                current_save_of_data.clear()
                continue
    client_socket.close()
