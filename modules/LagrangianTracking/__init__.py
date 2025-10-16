import toml
import os
import shutil
import pathlib
from ..Log import AppLogger


class LagrangianTracking_FVCOMOffline:
    def __init__(self, configfile: str):
        self.configfile = toml.load(configfile)
        # 创建日志
        self.logger = AppLogger('LagrangianTracking(FVCOM_offline)', self.configfile['Log']['Level'], pathlib.Path(self.configfile['Log']['File']))

        # 读取粒子追踪设置
        self.logger.info('注 - 离线追踪目前至多支持1100个粒子')
        self.logger.info('开始 - 读取FVCOM离线拉格朗日追踪配置')
        self.inverse = self.configfile['Lagrangian']['General']['Inverse']
        self.directory = self.configfile['Lagrangian']['General']['Directory']
        self.casename = self.configfile['Lagrangian']['General']['CaseName']
        self.sourcepath = self.configfile['Lagrangian']['General']['SourcePath']
        # namelist所有设置
        self.dti = self.configfile['Lagrangian']['TimeIntegration']['DTI']
        self.instp = self.configfile['Lagrangian']['TimeIntegration']['INSTP']
        self.dtout = self.configfile['Lagrangian']['TimeIntegration']['DTOUT']
        self.tdrift = self.configfile['Lagrangian']['TimeIntegration']['TDRIFT']
        self.yearlag = self.configfile['Lagrangian']['StartTime']['YEARLAG']
        self.monthlag = self.configfile['Lagrangian']['StartTime']['MONTHLAG']
        self.daylag = self.configfile['Lagrangian']['StartTime']['DAYLAG']
        self.hourlag = self.configfile['Lagrangian']['StartTime']['HOURLAG']
        self.inpdir = self.configfile['Lagrangian']['IOLocation']['INPDIR']
        self.geoarea = self.configfile['Lagrangian']['IOLocation']['GEOAREA']
        self.outdir = self.configfile['Lagrangian']['IOLocation']['OUTDIR']
        self.infofile = self.configfile['Lagrangian']['IOLocation']['INFOFILE']
        self.lagini = self.configfile['Lagrangian']['IOLocation']['LAGINI']
        self.f_depth = self.configfile['Lagrangian']['Coor']['F_DEPTH']
        self.p_sigma = self.configfile['Lagrangian']['Coor']['P_SIGMA']
        self.out_sigma = self.configfile['Lagrangian']['Coor']['OUTSIGMA']
        self.irw = self.configfile['Lagrangian']['RandomWalk']['IRW']
        self.dhor = self.configfile['Lagrangian']['RandomWalk']['DHOR']
        self.dtrw = self.configfile['Lagrangian']['RandomWalk']['DTRW']
        self.cart_shp = self.configfile['Lagrangian']['ProjectionControl']['CART_SHP']
        self.projection_reference = self.configfile['Lagrangian']['ProjectionControl']['PROJECTION_REFERENCE']
        self.logger.info('结束 - 读取FVCOM离线拉格朗日追踪配置')

        # 写入dat文件
        self.nml_writer()
        # 编译适合的程序
        self.compile_ptraj()
        # 运行
        self.lag_run()

    def nml_writer(self):
        """写入namelist文件，保持相对路径"""

        # 处理路径变量，将相对路径转换为基于配置文件目录的绝对路径
        def resolve_path(path):
            if not path or not isinstance(path, str):
                return path
            # 如果是相对路径，则基于配置文件目录解析
            if not os.path.isabs(path):
                return os.path.join(self.config_dir, path)
            return path

        nml_file = os.path.join(self.directory,self.casename+'_run.dat')

        with open(nml_file, 'w') as f:
            # 时间积分参数
            f.write(f"DTI = {self.dti}\n")
            f.write(f"INSTP = {self.instp}\n")
            f.write(f"DTOUT = {self.dtout}\n")
            f.write(f"TDRIFT = {self.tdrift}\n")

            # 开始时间参数
            f.write(f"YEARLAG = {self.yearlag}\n")
            f.write(f"MONTHLAG = {self.monthlag}\n")
            f.write(f"DAYLAG = {self.daylag}\n")
            f.write(f"HOURLAG = {self.hourlag}\n")

            # IO位置参数 - 保持相对路径结构
            f.write(f"INPDIR = {self.inpdir}\n")
            f.write(f"GEOAREA = {self.geoarea}\n")
            f.write(f"OUTDIR = {self.outdir}\n")
            f.write(f"INFOFILE = {self.infofile}\n")
            f.write(f"LAGINI = {self.lagini}\n")

            # SIGMA或CARTESIAN参数
            if self.f_depth:
                f.write(f"F_DEPTH = T\n")
            else:
                f.write(f"F_DEPTH = F\n")
            if self.p_sigma:
                f.write(f"P_SIGMA = T\n")
            else:
                f.write(f"P_SIGMA = F\n")
            if self.out_sigma:
                f.write(f"OUT_SIGMA = T\n")
            else:
                f.write(f"OUT_SIGMA = F\n")

            # 随机游走参数
            f.write(f"IRW = {self.irw}\n")
            f.write(f"DHOR = {self.dhor}\n")
            f.write(f"DTRW = {self.dtrw}\n")

            # 投影控制参数
            if self.cart_shp:
                f.write(f"CART_SHP = T\n")
            else:
                f.write(f"CART_SHP = F\n")
            f.write(f"PROJECTION_REFERENCE = \'{self.projection_reference}\'\n")

        self.logger.info(f"离线拉格朗日追踪的namelist文件已写入: {nml_file}")

    def compile_ptraj(self):
        '''
        检查例子追踪namelist与编译程序
        '''

        self.logger.info('开始 - 编译ptraj可执行文件')
        os.chdir(self.sourcepath)
        self.logger.info('Current change directory to {}'.format(self.sourcepath))
        os.system('make clean')

        if self.cart_shp:                   # 投影坐标系
            shutil.copyfile('makefile_proj','makefile')
        else:                               # 经纬度坐标系
            shutil.copyfile('makefile_latlon','makefile')

        # 判断makefile中是否有'CPPFLAGS ='和'-DINVERSE'
        with open('makefile', 'r') as fin:
            lines = fin.readlines()
            fin.close()
        if self.inverse:                    # 逆向追溯
            for i_line,line in enumerate(lines):
                if 'CPPFLAGS =' in line and '#' not in line:
                    if '-DINVERSE' in line:
                        lines[i_line] = line.rstrip()+'\n'
                    else:
                        lines[i_line] = line.rstrip()+' -DINVERSE \n'
        else:                               # 正向追踪
            for i_line,line in enumerate(lines):
                if 'CPPFLAGS =' in line and '#' not in line:
                    if '-DINVERSE' in line:
                        lines[i_line] = line.replace('-DINVERSE','').rstrip()+'\n'
        # 删除空行和行尾空白
        cleaned_lines = []
        for line in lines:
            stripped_line = line.rstrip()
            if stripped_line:  # 如果不是空行
                cleaned_lines.append(stripped_line + '\n')
        with open('makefile', 'w') as fout:
            fout.writelines(cleaned_lines)
            fout.close()
        os.system('source /usr/share/Modules/init/bash && module use /home/yzbsj/modulefiles && module load apps/netcdf-fortran/4.6.2 && make')
        self.logger.info('结束 - 编译ptraj可执行文件')

    def lag_run(self):
        self.logger.info('Current change directory to {}'.format(self.directory))
        os.chdir(self.directory)
        compiled_excutable_file = os.path.join(self.sourcepath, 'ptraj')
        destination_path = os.path.join(self.directory, 'ptraj')
        shutil.copyfile(compiled_excutable_file, destination_path)
        self.logger.info('开始 - 运行追踪程序')
        os.system('./ptraj '+self.casename)
        self.logger.info('结束 - 运行追踪程序')