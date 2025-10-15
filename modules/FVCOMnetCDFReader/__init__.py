import datetime
import netCDF4 as nc
import numpy as np
from datetime import datetime, timedelta
import pathlib
import toml
from ..log import AppLogger

class FVCOMResultProcessor: # 用于提取FVCOM输出文件中的时间信息
    def __init__(self, filename):
        """
        初始化类

        Parameters:
        filename (str): FVCOM输出文件的路径
        """
        self.filename = filename
        self.dataset = None
        self.time_var = None
        configfile = toml.load('configuration/config.toml')
        self.logger = AppLogger('FVCOM_Reader', configfile['Log']['Level'], pathlib.Path(configfile['Log']['File']))

    def open_dataset(self):
        """打开NetCDF数据集"""
        try:
            self.dataset = nc.Dataset(self.filename, 'r')

            self.logger.info('{} Opened'.format(self.filename))
            # 查找时间变量名（常见的时间变量名）
            possible_time_vars = ['time', 'Time', 'Times', 'itime', 'itime2']
            for var in possible_time_vars:
                if var in self.dataset.variables:
                    self.time_var = var
                    break

            if self.time_var is None:
                self.logger.error('Time Variables not Found')
                raise ValueError("未找到时间变量")

        except Exception as e:
            self.logger.error('{} not Opened'.format(self.filename))
            raise

    def close_dataset(self):
        """关闭数据集"""
        if self.dataset:
            self.dataset.close()
            self.logger.info('{} Closed'.format(self.filename))

    def get_time_info(self):
        """
        获取时间信息

        Returns:
        dict: 包含时间信息的字典
        """
        if self.dataset is None:
            self.open_dataset()

        try:
            time_data = self.dataset.variables[self.time_var][:]

            # 获取时间单位信息
            time_units = self.dataset.variables[self.time_var].units

            # 解析时间单位（常见格式：'days since 1858-11-17 00:00:00'）
            if 'since' in time_units:
                base_time_str = time_units.split('since ')[-1]
                base_time = datetime.strptime(base_time_str, '%Y-%m-%d %H:%M:%S')
            else:
                # 如果没有明确的时间基准，使用默认值
                base_time = datetime(1858, 11, 17, 0, 0, 0)  # FVCOM常用基准时间

            # 转换时间为datetime对象
            if self.time_var in ['itime', 'itime2']:
                # 处理特殊的时间格式（可能需要特殊处理）
                time_deltas = [timedelta(days=float(t)) for t in time_data]
            else:
                time_deltas = [timedelta(days=float(t)) for t in time_data]

            datetimes = [base_time + delta for delta in time_deltas]

            # 获取起止时间
            start_time = datetimes[0]
            end_time = datetimes[-1]

            time_info = {
                'start_time': start_time,
                'end_time': end_time,
                'total_timesteps': len(time_data),
                'time_units': time_units,
                'base_time': base_time,
                'all_times': datetimes
            }

            return time_info

        except Exception as e:
            self.logger.error('Time Variables Read Error'.format(self.filename))
            raise

    def print_time_summary(self):
        """打印时间信息摘要"""
        time_info = self.get_time_info()
        self.logger.info(self.time_var)

    def latlon2projection(self):
        from pyproj import Transformer

        transformer = Transformer.from_crs("epsg:4326", "epsg:32630")

        # 读取经纬度数据
        lat = self.dataset.variables['lat'][:]
        lon = self.dataset.variables['lon'][:]
        latc = self.dataset.variables['latc'][:]
        lonc = self.dataset.variables['lonc'][:]

        # 转换坐标并直接覆盖原有变量
        for i in range(len(lat)):
            x_temp, y_temp = transformer.transform(lat[i], lon[i])
            self.dataset.variables['x'][i] = x_temp
            self.dataset.variables['y'][i] = y_temp

        for i in range(len(latc)):
            xc_temp, yc_temp = transformer.transform(latc[i], lonc[i])
            self.dataset.variables['xc'][i] = xc_temp
            self.dataset.variables['yc'][i] = yc_temp