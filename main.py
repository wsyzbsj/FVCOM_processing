import argparse
import toml
import os
import pathlib
import shutil
import modules
from datetime import datetime,timedelta

if __name__ == "__main__":
    # 创建命令行参数解析器
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

    # 解析命令行参数
    args = parser.parse_args()
    # 主程序日志
    logger = modules.Log.AppLogger('main', args.loglevel, args.logfile)
    # 使用解析得到的配置文件路径
    configfile = args.config
    shutil.copyfile('configuration/config.toml', configfile)
    if args.logfile.startswith('/'):
        logpath = pathlib.Path(args.logfile).parent
    else:
        logpath = pathlib.Path(os.path.join(os.getcwd()),args.logfile)
    if os.path.exists(logpath):
        if os.path.exists(args.logfile):
            os.remove(args.logfile)
    else:
        os.makedirs(logpath)

    # 写入配置文件
    with open(configfile, 'r', encoding='utf-8') as fin:
        data = toml.load(fin)
        # 计算运算时间
        endtime = datetime.strptime(args.endtime, '%Y-%m-%d %H:%M:%S')
        starttime = datetime.strptime(args.starttime, '%Y-%m-%d %H:%M:%S')
        time_run = (endtime-starttime).total_seconds()//3600
        if args.inverse == 'T':
            time_run *= -1
            logger.info('开始时间:{}, 追溯时长:{}小时'.format(starttime,time_run))
        elif args.inverse == 'F':
            logger.info('开始时间:{}, 追踪时长:{}小时'.format(starttime,time_run))
        else:
            logger.error('追踪/追溯时间为负,错误')
            raise RuntimeError
        if time_run < 0:
            logger.error('追踪/追溯时间为负,错误')
            raise RuntimeError
        data['Lagrangian']['TimeIntegration']['TDRIFT'] = int(time_run*(3600/data['Lagrangian']['TimeIntegration']['INSTP']))
        data['Lagrangian']['General']['CaseName'] = args.casename
        if args.inverse == 'F':
            data['Lagrangian']['General']['Inverse'] = False
        elif args.inverse == 'T':
            data['Lagrangian']['General']['Inverse'] = True
        else:
            logger.error('追溯/追踪选择错误')
            raise ValueError
        data['Lagrangian']['StartTime']['YEARLAG'] = starttime.strftime('%Y')
        data['Lagrangian']['StartTime']['MONTHLAG'] = starttime.strftime('%m')
        data['Lagrangian']['StartTime']['DAYLAG'] = starttime.strftime('%d')
        data['Lagrangian']['StartTime']['HOURLAG'] = starttime.strftime('%H')
        data['Lagrangian']['IOLocation']['GEOAREA'] = args.geoarea
        data['Lagrangian']['IOLocation']['LAGINI'] = args.lagini
        if args.cart_shp == 'F':
            data['Lagrangian']['ProjectionControl']['CART_SHP'] = False
        elif args.cart_shp == 'T':
            data['Lagrangian']['ProjectionControl']['CART_SHP'] = True
        else:
            logger.error('坐标系选择T/F错误')
            raise ValueError
        fin.close()

    with open(configfile, 'w', encoding='utf-8') as fout:
        toml.dump(data, fout)

# 提取FVCOM输出文件时间
    logger.info('开始 - 读取指定目录下netCDF文件')
    modules.FVCOMnetCDFReader.FVCOMResultProcessor(configfile)
    logger.info('结束 - 读取指定目录下netCDF文件')

    # 读取并写入离线拉格朗日粒子追踪namelist
    logger.info('开始 - 写入粒子追踪namelist并编译运行')
    modules.LagrangianTracking.LagrangianTracking_FVCOMOffline(configfile)
    logger.info('结束 - 写入粒子追踪namelist并编译运行')