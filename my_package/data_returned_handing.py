from concurrent.futures import ThreadPoolExecutor
from matplotlib import pyplot as plt
from my_package.data_receive_handing import DataProcessor


def process_data(data_queue):
    """
    数据处理函数
    :param data_queue: 当前获得的周期
    :return: 返回异常状态、原始周期数据、处理器描述
    """
    processors = []  # 实例化处理器列表
    # 实例化15个处理器
    for process in range(15):
        processor = DataProcessor(process, f'Axis {process + 1}')
        processors.append(processor)

    # 将数据放入处理器中进行处理
    while True:
        abnormal_state_for_all = []
        fig = plt.figure(figsize=(25.60, 14.40))
        data = data_queue.get()
        if not data:
            print('No data received from queue')
            break

        # 将各线程的处理结果返回并保存
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = []  # 保存线程返回结果
            for thread in range(15):
                axis_data = [row[thread] for row in data]
                axis = executor.submit(processors[thread].multiple_process, axis_data)
                futures.append(axis)

            for i, future in enumerate(futures):
                result = future.result()
                # 返回异常状态、处理器描述、当前周期数据（未经裁剪）、异常周期数据（总数据）
                state, description, local_data, all_data = result
                abnormal_state_for_all.append(state)
                if len(local_data) == 2:
                    # 创建15个子图
                    ax = fig.add_subplot(3, 5, i + 1)
                    if state:
                        print(f"Abnormal state detected for {description}")
                        ax.axvspan(len(local_data[0]), len(local_data[0]) + len(local_data[1])
                                   , color='red', alpha=0.3, label=f'Abnormal Period')
                    ax.plot(local_data[0] + local_data[1], label=description)
                    ax.legend()
            # 只要任一轴存在异常
            # 就显示全部轴的前一个以及当前周期
            if any(abnormal_state_for_all):
                plt.show()
        executor.shutdown()
