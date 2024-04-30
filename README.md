## 运行测试

  对于main.py，因运行在本地，需在本地安装相应的库  
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

将服务端代码拆分成了3个包与main程序，main程序为主入口，三个包放在了mypackage文件夹当中通过import调用


## 贡献

请阅读 [CONTRIBUTING.md](链接到贡献指南) 了解如何为该项目做出贡献。

## 版本控制

我们使用 [Git](https://git-scm.com/) 进行版本控制。您可以在仓库中查看可用版本。

## 作者

* **Chan** - *初始工作* - [yooyoui](https://github.com/yooyoui)

