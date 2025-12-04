# FVCOM_processing

此模块作为DTO附属部分，其中主要包含三个模块，日志、FVCOM输出文件操作和FVCOM离线拉格朗日追踪三个模块。

## 使用

```python
python main.py
```

### 可用参数

已经实现的功能：离线拉格朗日追踪与追溯，输出计算百分比到日志

```python
    parser = argparse.ArgumentParser(description='FVCOM离线拉格朗日追踪/追溯程序')
    parser.add_argument('--config', type=str, default='configuration/config_1.toml', help='配置文件路径,默认: configuration/config.toml')
    parser.add_argument('--loglevel', type=str, default='INFO', help='配置文件路径 (默认: INFO,可选: ERROR,INFO,DEBUG)')
    parser.add_argument('--logfile', type=str, default='output/log/log', help='日志文件路径 (默认: output/log/log)')
    parser.add_argument('--starttime', type=str, default='2025-04-02 00:00:00', help='追踪/追溯起始时间')
    parser.add_argument('--endtime', type=str, default='2025-04-03 23:00:00', help='追踪/追溯终止时间')
    parser.add_argument('--inverse', type=str, default='F', help='是否为追溯模式,T为追溯,F为追踪 (默认:F)')
    parser.add_argument('--geoarea', type=str, default='subei', help='网格位置,默认:subei')
    parser.add_argument('--casename', type=str, default='tst_new', help='追踪namelist文件名,*_run.dat')
    parser.add_argument('--lagini', type=str, default='particle', help='粒子位置,*.dat')
    parser.add_argument('--cart_shp', type=str, default='F', help='坐标系统,T为投影坐标,F为球(经纬度)坐标 (默认:F)')
```

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

根据ptraj版本决定是否转换坐标系——目前实现了经纬度球坐标系

### LagrangianTracking类

主要分为写入namelist、编译、运行三个部分

## 备注
### 变量重命名

```python
ncrename -h -O -v wts,omega subei_0001.nc
```
### 追加变量

```python
ncks -A -v a1u subei_0001.nc subei_0005.nc
```
