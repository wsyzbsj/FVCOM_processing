import toml
import os
import shutil
import pathlib
from ..Log import AppLogger
import subprocess
import threading
import re


class LagrangianTracking_FVCOMOffline:
    def __init__(self, configfile: str):
        self.configfile = toml.load(configfile)
        # 创建日志
        self.logger = AppLogger('LagrangianTracking(FVCOM_offline)', self.configfile['Log']['Level'], pathlib.Path(self.configfile['Log']['File']))

        # 读取粒子追踪设置
        self.logger.info('注:离线追踪目前至多支持1100个粒子')
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

        nml_file = os.path.join(self.directory,self.casename+'_run.dat')
        self.logger.info("开始 - 离线拉格朗日追踪的namelist文件已写入: {nml_file}")

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
            f.close()

        self.logger.info(f"结束 - 离线拉格朗日追踪的namelist文件已写入: {nml_file}")

    def compile_ptraj(self):
        '''
        检查例子追踪namelist与编译程序
        '''

        self.logger.info('更改当前目录至拉格朗日追踪源代码目录:{}'.format(self.sourcepath))
        os.chdir(self.sourcepath)
        self.logger.info('进行make clean')
        os.system('make clean')
        self.logger.info('开始 - 修改ptraj的makefile')
        self.logger.info('开始 - 选择球面(经纬度)/投影坐标系')
        if self.cart_shp:                   # 投影坐标系
            self.logger.info('您选择了:投影坐标系')
            shutil.copyfile('makefile_proj','makefile')
        else:                               # 球面坐标系
            self.logger.info('您选择了:球面(经纬度)坐标系')
            shutil.copyfile('makefile_latlon','makefile')
        self.logger.info('结束 - 选择球面(经纬度)/投影坐标系')

        with open('makefile', 'r') as fin:
            lines = fin.readlines()
            fin.close()
        # 判断makefile未注释的'CPPFLAGS ='行中是否有'-DINVERSE',即追溯
        self.logger.info('开始 - 选择追踪或追溯')
        if self.inverse:                    # 逆向追溯
            self.logger.info('您选择了:追溯')
            for i_line,line in enumerate(lines):
                if 'CPPFLAGS =' in line and '#' not in line:
                    if '-DINVERSE' in line:
                        lines[i_line] = line.rstrip()+'\n'
                    else:
                        lines[i_line] = line.rstrip()+' -DINVERSE \n'
        else:                               # 正向追踪
            self.logger.info('您选择了:追踪')
            for i_line,line in enumerate(lines):
                if 'CPPFLAGS =' in line and '#' not in line:
                    if '-DINVERSE' in line:
                        lines[i_line] = line.replace('-DINVERSE','').rstrip()+'\n'
        self.logger.info('结束 - 选择追踪或追溯')
        # 删除空行和行尾空白
        self.logger.info('开始 - 更新makefile(追踪/追溯)')
        cleaned_lines = []
        for line in lines:
            stripped_line = line.rstrip()
            if stripped_line:  # 如果不是空行
                cleaned_lines.append(stripped_line + '\n')
        with open('makefile', 'w') as fout:
            fout.writelines(cleaned_lines)
            fout.close()
        self.logger.info('结束 - 修改ptraj的makefile(追踪/追溯)')
        self.logger.info('结束 - 修改ptraj的makefile(全部)')
        self.logger.info('开始 - 编译ptraj可执行文件')
        os.system('source /usr/share/Modules/init/bash && module use /home/yzbsj/modulefiles && module load apps/netcdf-fortran/4.6.2 && make')
        self.logger.info('结束 - 编译ptraj可执行文件')

    def lag_run(self):
        self.logger.info('开始 - 运行追踪程序')
        self.logger.info('更改当前目录至:{},以运行离线粒子追踪'.format(self.directory))
        os.chdir(self.directory)
        compiled_excutable_file = os.path.join(self.sourcepath, 'ptraj')
        destination_path = os.path.join(self.directory, 'ptraj')
        os.remove(destination_path)
        os.symlink(compiled_excutable_file, destination_path)           # 链接至编译的可执行文件

        # 定义进度跟踪变量
        self.current_progress = 0
        self.total_hours = None
        self.current_hours = 0

        def parse_progress(line):
            """解析进度信息并返回百分比"""
            # 使用正则表达式匹配进度格式：数字 / 数字 finished (hours)
            pattern = r'\s*(\d+)\s*/\s*(\d+)\s*finished\s*\(hours\)'
            match = re.search(pattern, line)

            if match:
                current = int(match.group(1))
                total = int(match.group(2))

                # 更新总时次数（只更新一次）
                if self.total_hours is None:
                    self.total_hours = total
                    self.logger.info(f"检测到总时次数: {total}")

                # 计算百分比
                if total > 0:
                    progress_percent = (current / total) * 100
                    return progress_percent, current, total

            return None, None, None

        def handle_output(line):
            """处理输出的回调函数"""
            line = line.strip()

            # 记录所有输出
            self.logger.info(f"程序输出: {line}")

            # 尝试解析进度信息
            progress_percent, current, total = parse_progress(line)

            if progress_percent is not None:
                # 只有当进度有显著变化时才记录（避免过于频繁的记录）
                if abs(progress_percent - self.current_progress) >= 0.1:  # 至少1%的变化
                    self.current_progress = progress_percent
                    self.current_hours = current

                    self.logger.info(f"粒子追踪进度: {progress_percent:.1f}%")

                    # 这里可以添加其他进度处理逻辑
                    # 例如：更新GUI进度条、发送进度通知等

                    # 如果进度达到100%，记录完成
                    if progress_percent >= 100:
                        self.logger.info("粒子追踪已完成!")

        try:
            command = ['./ptraj', self.casename]
            self.logger.info(f"执行命令: {' '.join(command)}")

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )

            # 同步读取输出
            for line in iter(process.stdout.readline, ''):
                handle_output(line)

            # 等待进程完成
            process.wait()

        except Exception as e:
            self.logger.error(f"运行粒子追踪程序时发生错误: {e}")
            raise

        self.logger.info('结束 - 运行追踪程序')