import socket
import numpy as np
from matplotlib import pyplot as plt
import struct

from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from tslearn.utils import to_time_series
from tslearn.metrics import dtw, dtw_path

import threading
from threading import Lock
import queue
from multiprocessing import Process, Queue

save_of_data = []  # 保存接收到的数据
last_current_data = []  # 保存当前周期以及它们前一个周期的切片
abnormal_state = False  # 标记是否存在异常状态


def plot_data(data, title='Combined Data'):  # 绘制数据
    plt.plot(data, label='combined data')  # 绘制合并后的数据
    plt.legend(title=title)  # 显示图例
    plt.xlabel('Index')  # 设置x轴标签
    plt.ylabel('Value')  # 设置y轴标签
    plt.draw()  # 绘制图表
    plt.pause(0.0001)  # 暂停一段时间，以显示图表


# 数据平滑函数
def moving_average(data, window_size):
    result = np.zeros(len(data) - window_size + 1)  # 创建结果数组，长度为原数据长度减去窗口大小加1
    for i in range(window_size-1, len(data)):
        result[i-window_size+1] = (np.sum(data[i-window_size+1:i+1]) + data[i]) / window_size
    return result


def handle_client(client_socket, data_queue):
    current_save_of_data = []  # 保存接收到的数据

    while True:
        # 接收数据，直到 current_save_of_data 的长度至少为 2000
        message_length = client_socket.recv(4)
        data_length = struct.unpack('!I', message_length)[0]
        received_data = client_socket.recv(data_length)
        if not received_data:
            break

        current_save_of_data.append(list(map(int, received_data.decode().split(','))))

        if len(current_save_of_data) > 2000:
            # 采用主轴1的数据判断周期是否完整
            Axis_1 = [row[0] for row in current_save_of_data]
            # 检查最后 50 个数中非睡眠点的数量
            non_sleep_indices = np.where(np.array(Axis_1[-50:]) > 50)[0]
            if len(non_sleep_indices) > 0:
                continue  # 如果条件满足，继续接收数据
            else:
                save_of_data.append(Axis_1.copy())  # 保存数据
                data_queue.put(current_save_of_data.copy())  # 放入数据队列
                current_save_of_data.clear()  # 清空当前数据
                continue  # 采集下一周期数据
    client_socket.close()


def process_data(data_queue):  # 多线程处理数据

    processors = []  # 实例化处理器列表

    for i in range(15):
        processor = DataProcessor(i, f"Axis {i + 1}")
        processors.append(processor)

    while True:
        data = data_queue.get()  # 取出数据队列中的数据

        thread_list = []  # 线程列表

        for i in range(15):
            thread = threading.Thread(target=processors[i].multiple_process, args=(data,))
            thread.start()
            thread_list.append(thread)

        for t in thread_list:  # 等待所有线程结束
            t.join()


class DataProcessor:   # 处理器类
    deskLock = Lock()  # 线程锁

    def __init__(self, axis, description="Generic Processor"):  # 初始化处理器
        self.axis = axis
        self.description = description
        self.last_current_data = []
        self.abnormal_state = False
        self.abnormal_period_data = []

    def multiple_process(self, current_save_of_data):  # 数据切割与异常检测
        DataProcessor.deskLock.acquire()

        Axis_data = [row[self.axis] for row in current_save_of_data]         # 选择当前轴的数据

        # 找出睡眠阶段的索引
        sleep_point = min(Axis_data)
        indices_of_sleep = [index for index, value in enumerate(Axis_data) if (value - sleep_point) < 50]

        # 检查每个睡眠阶段点周围是否存在突变点
        final_sleep_state = []
        # window_size = 600  # 窗口大小
        threshold = 150  # 突变点阈值

        for idx in indices_of_sleep:
            # left_window = Axis_data[max(0, idx - window_size):idx]
            # right_window = Axis_data[idx:min(len(Axis_data), idx + window_size)]
            left_window = Axis_data[0:idx]
            right_window = Axis_data[idx:]

            if len(left_window) > 1 and len(right_window) > 1:
                left_diff = np.abs(np.diff(left_window))
                right_diff = np.abs(np.diff(right_window))

                condition = np.max(left_diff) < threshold or np.max(right_diff) < threshold
                if condition:
                    final_sleep_state.append(idx)

        #   找出睡眠阶段索引中不连续的位置，并切割数据
        sleep_dist = 25  # 两睡眠阶段距离
        cut_adjust = 30  # 切割点距离调整
        split_points = []  # 切割点索引

        for i in range(1, len(final_sleep_state)):
            if final_sleep_state[i] - final_sleep_state[i - 1] > sleep_dist:
                startpoint = final_sleep_state[i - 1]
                split_points.append(max(0, startpoint - cut_adjust))
                endpoint = final_sleep_state[i]
                split_points.append(min(len(Axis_data), endpoint + cut_adjust))

        for cut_idx in range(0, len(split_points), 2):

            # 周期裁剪
            cut_start_idx = split_points[cut_idx]
            cut_end_idx = split_points[cut_idx + 1]

            origin_cut_data = Axis_data[cut_start_idx:cut_end_idx]
            smooth_cut_data = moving_average(origin_cut_data, 9)

            self.last_current_data.append(smooth_cut_data)
            print(f"Processing with {self.description}, received data:")
            print(Axis_data)

            # 只保留最新的两个周期数据
            if len(self.last_current_data) > 2:
                self.last_current_data = self.last_current_data[-2:]

            # 根据周期索引获得上一周期数据与当前周期数据
            if len(self.last_current_data) == 2:

                last_period_data = self.last_current_data[0]
                current_period_data = self.last_current_data[1]

                # 调整时间序列特征大小并进行标准化处理
                scaler = TimeSeriesScalerMeanVariance(mu=0., std=1.)
                time_series_lst_1 = to_time_series(last_period_data)
                time_series_lst_1_norm = scaler.fit_transform([time_series_lst_1]).reshape(
                    time_series_lst_1.shape)

                time_series_lst_2 = to_time_series(current_period_data)
                time_series_lst_2_norm = scaler.fit_transform([time_series_lst_2]).reshape(
                    time_series_lst_2.shape)

                # 计算动态时间规整（DTW）距离
                optimal_path, dtw_score_ = dtw_path(time_series_lst_1_norm, time_series_lst_2_norm)

                # 检测到异常后，在下一周期对异常周期及其前后周期展出
                if self.abnormal_state:
                    plt.axvspan(len(self.abnormal_period_data[0]), len(self.abnormal_period_data[1])
                                + len(current_period_data),
                                color='red', alpha=0.3, label=f'Abnormal Period')  # 标记异常时间序列
                    plot_data(list(self.abnormal_period_data[0]) + list(self.abnormal_period_data[1])
                              + list(current_period_data), self.description)
                    self.abnormal_state = False

                # 检测异常，并保留上一周期
                if dtw_score_ > 3:
                    print(f'{self.description} is abnormal!, dtw_score: {dtw_score_}')
                    self.abnormal_state = True
                    self.abnormal_period_data = self.last_current_data.copy()
                else:
                    print(f'{self.description} is normal, dtw_score: {dtw_score_}')

        DataProcessor.deskLock.release()


def receive_data(server_host, server_port):  # socket接收数据
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_host, server_port))
    server_socket.listen(1)
    data_queue = queue.Queue()

    print(f"Server listening on {server_host}:{server_port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection from {client_address}")
            threading.Thread(target=handle_client, args=(client_socket, data_queue)).start()  # 启动客户端接收线程
            # 启动数据处理线程
            threading.Thread(target=process_data, args=(data_queue,)).start()  # 启动数据处理线程

    finally:
        server_socket.close()


# 使用示例
server_host = '172.17.233.120'  # 服务器 IP 或主机名
server_port = 8000  # 服务器端口
receive_data(server_host, server_port)
