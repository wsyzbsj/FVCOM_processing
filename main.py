import toml
import pathlib
import modules

if __name__ == "__main__":
    # 读取配置文件
    configfile ='configuration/config.toml'

    # 主程序日志文件
    main_config = toml.load(configfile)

    logger = modules.Log.AppLogger('main', main_config['Log']['Level'], pathlib.Path(main_config['Log']['File']))

    # 提取FVCOM输出文件时间
    modules.FVCOMnetCDFReader.FVCOMResultProcessor(configfile)

    # 读取并写入离线拉格朗日例子追踪namelist
    modules.LagrangianTracking.LagrangianTracking_FVCOMOffline(configfile)