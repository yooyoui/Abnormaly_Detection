## 运行测试

  对于client.py，因运行在本地，需在本地安装相应的库  
  对于socket server.py, 因运行在云端，需部署ssh并使用云端上的解释器（其中，阿里云ecs中已经安装anaconda及相应的库）  
  因此，可能需要将客户端与服务器端分别放在两个项目当中。
  
## 部署

  对于PyCharm,需要进行如下配置(>工具 中可进行ssh deploy)  
  ![ssh deploy](image%20for%20readme/deploy/ssh%20deploy.png)
  ![ssh enterpreter](image%20for%20readme/deploy/ssh%20enterpreter.png)

  
## 使用到的框架

列出该项目使用到的语言和框架。

- [Python](https://www.python.org/)
- [Socket](https://docs.python.org/3/library/socket.html)
- [tslearn](https://tslearn.readthedocs.io/en/stable/installation.html)

## 代码解释

这段Python代码是一个服务器端应用程序，它从客户端接收数据，处理数据，并根据动态时间规整（DTW）得分检测异常。代码使用了多个库，如`socket`、`numpy`、`matplotlib`、`struct`、`threading`、`queue`、`multiprocessing`和`tslearn`。

服务器使用`socket`库进行设置。`receive_data`函数创建一个服务器套接字，将其绑定到提供的主机和端口，并开始监听传入的连接。对于每个连接的客户端，都会创建一个新线程来处理客户端的数据。这是通过使用`threading.Thread`函数完成的，目标是`handle_client`函数。

```python
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_host, server_port))
server_socket.listen(1)
```

`handle_client`函数从客户端接收数据并将其添加到列表（`current_save_of_data`）中。当此列表的长度超过2000时（基本上保证能够接收到活跃点，同时也能使每次只截取一个周期以保证实时性），它会检查最后50个数据点。如果这些点满足这50个数据点都不为"睡眠点"，数据将被添加到队列（`data_queue`）中进行进一步处理，列表将被清空。

```python
current_save_of_data.append(list(map(int, received_data.decode().split(','))))
```

`process_data`函数从队列中检索数据，并为每个数据轴（总共15个）创建一个新线程。每个线程使用`DataProcessor`类的一个实例来处理数据。

```python
thread = threading.Thread(target=processors[i].multiple_process, args=(data,))
```

`DataProcessor`类负责处理数据。它首先选择其轴的数据并识别睡眠点的索引。然后，它检查每个睡眠点周围的突变，并识别最终的睡眠状态。然后，根据这些睡眠状态将数据分割成周期。

```python
Axis_data = [row[self.axis] for row in current_save_of_data]
```

每个周期都使用移动平均函数进行平滑处理，并保留最后两个周期进行比较。计算这两个周期之间的动态时间规整（DTW）得分。如果得分超过某个阈值，该周期将被标记为异常。

```python
if dtw_score_ > 3:
    print(f'{self.description} is abnormal!, dtw_score: {dtw_score_}')
    self.abnormal_state = True
    self.abnormal_period_data = self.last_current_data.copy()
```

总的来说，这段代码从客户端接收数据，在多个线程中处理数据，并使用DTW得分来检测数据中的异常。


## 贡献

请阅读 [CONTRIBUTING.md](链接到贡献指南) 了解如何为该项目做出贡献。

## 版本控制

我们使用 [Git](https://git-scm.com/) 进行版本控制。您可以在仓库中查看可用版本。

## 作者

* **Chan** - *初始工作* - [yooyoui](https://github.com/yooyoui)

