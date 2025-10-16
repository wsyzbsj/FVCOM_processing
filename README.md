# FVCOM_processing

此模块作为DTO附属部分，其中主要包含三个模块，日志、FVCOM输出文件操作和FVCOM离线拉格朗日追踪三个模块。

## 各个目录

| 目录/文件名   | 用途              |
| ------------- | ----------------- |
| configuration | 配置文件存储位置  |
| modules       | 模块存储位置      |
| output        | 输出/日志存储位置 |
| main.py       | 主要代码          |

## 模块

### log——日志类

```python
logger = modules.log.AppLogger('main', configfile['Log']['Level'], pathlib.Path(configfile['Log']['File']))
logger.info('Found FVCOM output files: {}'.format(fvcom_file))
```

第一个参数'main'是当前日志记录器的名称，我将其设定为当前模块名称

第二个参数是日志等级，分为error、info和debug

第三个参数是日志存储位置

### FVCOMnetCDFReader——FVCOM输出处理类

#### 基本用法

```python
time_extractor = modules.FVCOMnetCDFReader.FVCOMResultExtractor(fvcom_file)
time_info = time_extractor.get_time_info()
time_extractor.print_time_summary()
logger.info('{} Time info: 开始 {};结束 {}'.format(fvcom_file,time_info['start_time'],time_info['end_time']))
```

#### 其他

根据ptraj版本决定是否转换坐标系

### LagrangianTracking类

主要分为写入namelist、编译、运行三个部分，尚未实现

