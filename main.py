import toml
import os
import glob
import pathlib
import modules

if __name__ == "__main__":
    # 读取配置文件
    configfile = toml.load('configuration/config.toml')

    logger = modules.log.AppLogger('main', configfile['Log']['Level'], pathlib.Path(configfile['Log']['File']))

    # 替换为你的FVCOM输出文件路径
    fvcom_files = sorted(glob.glob(os.path.join(configfile['FVCOM Output Directory']['Directory'],'*.nc')))
    for fvcom_file in fvcom_files:
        logger.info('Found FVCOM output files: {}'.format(fvcom_file))

        # 创建时间提取器实例
        time_extractor = modules.FVCOMnetCDFReader.FVCOMResultExtractor(fvcom_file)

        try:
            # 获取时间信息
            time_info = time_extractor.get_time_info()

            # 打印摘要
            time_extractor.print_time_summary()

            logger.info('{} Time info: 开始 {};结束 {}'.format(fvcom_file,time_info['start_time'],time_info['end_time']))

        except Exception as e:
            logger.error('Processing {} Error'.format(fvcom_file))

        finally:
            # 确保关闭文件
            time_extractor.close_dataset()