import numpy as np
from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from tslearn.utils import to_time_series
from tslearn.metrics import dtw, dtw_path


def moving_average(data, window_size):
    """
    数据平滑函数
    取当前点前后窗口大小的数据，计算平均值
    """
    result = np.zeros(len(data) - window_size + 1)
    for i in range(window_size-1, len(data)):
        result[i-window_size+1] = (np.sum(data[i-window_size+1:i+1]) + data[i]) / window_size
    return result


class DataProcessor:
    """
    处理器类
    用于处理数据
    """
    def __init__(self, axis, description='Generic Processor'):
        """
        初始化处理器
        :param axis: 当前处理轴
        :param description: 当前处理轴的描述
        """
        self.axis = axis
        self.description = description
        self.abnormal_state = False  # 异常状态
        self.last_current_data = []  # 保存当前周期以及前一个周期的切片
        self.abnormal_period_data = []  # 所有的异常周期数据
        self.original_data = []  # 保存未进行平滑处理的周期数据

    def multiple_process(self, axis_data):
        """
        数据处理函数
        :param axis_data: 对应实例的周期数据
        :return: 返回异常状态、处理器描述、 当前周期数据（未经裁剪）、异常周期数据（总数据）
        """
        final_sleep_state = self.find_sleep_stage(axis_data)
        self.find_discontinuous_and_cut(final_sleep_state, axis_data)
        self.dtw_processing()
        return self.abnormal_state, self.description, self.original_data, self.abnormal_period_data

    def find_sleep_stage(self, axis_data):
        """
        找出睡眠阶段的索引
        :param axis_data:
        :return: 返回所有睡眠点的索引
        """
        sleep_point = min(axis_data)
        indices_of_sleep = [index for index, value in enumerate(axis_data) if (value - sleep_point) < 50]

        final_sleep_state = []  # 保存睡眠阶段索引
        threshold = 150  # 突变点阈值

        for idx in indices_of_sleep:
            left_window = axis_data[0:idx]
            right_window = axis_data[idx:]

            if len(left_window) > 1 and len(right_window) > 1:
                left_diff = np.abs(np.diff(left_window))
                right_diff = np.abs(np.diff(right_window))

                condition = np.max(left_diff) < threshold or np.max(right_diff) < threshold
                if condition:
                    final_sleep_state.append(idx)
        return final_sleep_state

    def find_discontinuous_and_cut(self, final_sleep_state, axis_data):
        """
        找出睡眠阶段索引中不连续的位置，并切割数据
        :param final_sleep_state: 睡眠点索引
        :param axis_data:
        """
        sleep_dist = 25  # 两睡眠阶段距离
        cut_adjust = 30  # 切割点距离调整
        split_points = []  # 切割点索引

        for i in range(1, len(final_sleep_state)):
            if final_sleep_state[i] - final_sleep_state[i - 1] > sleep_dist:
                startpoint = final_sleep_state[i - 1]
                split_points.append(max(0, startpoint - cut_adjust))
                endpoint = final_sleep_state[i]
                split_points.append(min(len(axis_data), endpoint + cut_adjust))

        for cut_idx in range(0, len(split_points), 2):
            cut_start_idx = split_points[cut_idx]
            cut_end_idx = split_points[cut_idx + 1]

            origin_cut_data = axis_data[cut_start_idx:cut_end_idx]
            smooth_cut_data = moving_average(origin_cut_data, 9)

            self.original_data.append(axis_data)
            self.last_current_data.append(smooth_cut_data)

            if len(self.last_current_data) > 2:
                self.original_data = self.original_data[-2:]
                self.last_current_data = self.last_current_data[-2:]

    def dtw_processing(self):
        """
        动态时间规整处理
        """
        # 只保留最新的两个周期数据
        if len(self.last_current_data) == 2:
            last_period_data = self.last_current_data[0]
            current_period_data = self.last_current_data[1]

            # 数据标准化
            scaler = TimeSeriesScalerMeanVariance(mu=0., std=1.)
            time_series_lst_1 = to_time_series(last_period_data)
            time_series_lst_1_norm = scaler.fit_transform([time_series_lst_1]).reshape(
                time_series_lst_1.shape)

            time_series_lst_2 = to_time_series(current_period_data)
            time_series_lst_2_norm = scaler.fit_transform([time_series_lst_2]).reshape(
                time_series_lst_2.shape)

            # 计算动态时间规整（DTW）距离
            optimal_path, dtw_score_ = dtw_path(time_series_lst_1_norm, time_series_lst_2_norm)

            # 如果DTW距离大于3，则认为是异常状态（3用作测试，实际应用中应根据实际情况调整）
            if dtw_score_ > 3:
                self.abnormal_state = True
                self.abnormal_period_data.append(self.original_data)
                print(f'{self.description} is abnormal, dtw_score: {dtw_score_}')
            # else:
            #     print(f'{self.description} is normal, dtw_score: {dtw_score_}')

