import toml
import os
import shutil
import pathlib
from ..Log import AppLogger
import subprocess
import threading
import re
import numpy as np

class LagrangianTracking_FVCOMOffline:
    def __init__(self, configfile: str):
        self.total_progress = 0.0
        self.configfile = toml.load(configfile)
        # 创建日志
        self.logger = AppLogger('LagrangianTracking(FVCOM_offline)', self.configfile['Log']['Level'], pathlib.Path(self.configfile['Log']['File']))
        # 总线程数
        self.thread_nums = int(self.configfile['General']['Threads'])

        # 读取粒子追踪设置
        self.logger.info('开始 - 读取FVCOM离线拉格朗日追踪配置')
        self.inverse = self.configfile['Lagrangian']['General']['Inverse']
        self.directory = self.configfile['Lagrangian']['General']['Directory']
        self.casename = self.configfile['Lagrangian']['General']['CaseName']
        self.sourcepath = self.configfile['Lagrangian']['General']['SourcePath']
        self.dragc = self.configfile['Lagrangian']['General']['Dragc']
        self.rotate_angle = self.configfile['Lagrangian']['General']['ROTATE_ANGLE']
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
        # 拆分算例
        self.particle_spliter()
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
            f.write(f"DRAG_C={self.dragc}\n")
            f.write(f"ROTATE_ANGLE={self.rotate_angle}\n")
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
        os.system('make')
        self.logger.info('结束 - 编译ptraj可执行文件')

    def lag_run(self):
        self.logger.info('开始 - 并行运行追踪程序')
        self.logger.info(f'更改当前目录至:{self.directory}, 以运行离线粒子追踪')
        os.chdir(self.directory)
        compiled_executable_file = os.path.join(self.sourcepath, 'ptraj')
        destination_path = os.path.join(self.directory, 'ptraj')

        if os.path.exists(destination_path):
            os.remove(destination_path)
        os.symlink(compiled_executable_file, destination_path)

        # -------------------------
        # 新增：并行运行多个算例
        # -------------------------
        num_threads = self.thread_nums
        self.logger.info(f"共检测到 {num_threads} 个算例，将并行运行。")

        # 各线程的当前进度（百分比）
        progress_list = [0.0 for _ in range(num_threads)]

        # 定义锁以防止多线程竞争
        progress_lock = threading.Lock()

        # 正则表达式模式复用
        pattern = re.compile(r'\s*(\d+)\s*/\s*(\d+)\s*finished\s*\(hours\)')

        def parse_progress(line):
            match = pattern.search(line)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                if total > 0:
                    return (current / total) * 100
            return None

        def handle_output(idx, line):
            """处理子进程输出并更新对应线程的进度"""
            line = line.strip()
            self.logger.info(f"[{idx:02d}] 输出: {line}")
            progress_percent = parse_progress(line)
            if progress_percent is not None:
                with progress_lock:
                    progress_list[idx] = progress_percent
                    self.total_progress = sum(progress_list) / num_threads
                self.logger.info(f"[{idx:02d}] 当前进度: {progress_percent:.1f}%，总体进度: {self.total_progress:.1f}%")

        def run_case(idx):
            """运行单个粒子追踪算例"""
            case_name = f"{self.casename}_{idx:03d}"
            command = ['./ptraj', case_name]
            self.logger.info(f"[{idx:02d}] 启动命令: {' '.join(command)}")

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )

            for line in iter(process.stdout.readline, ''):
                handle_output(idx, line)

            process.wait()
            self.logger.info(f"[{idx:02d}] 进程结束")

        # -------------------------
        # 启动所有线程
        # -------------------------
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=run_case, args=(i,))
            threads.append(t)
            t.start()

        # -------------------------
        # 等待所有线程结束
        # -------------------------
        for t in threads:
            t.join()

        self.logger.info("全部粒子追踪算例运行完毕！")

    def particle_spliter(self):
        current_dir = os.getcwd()
        os.chdir(os.path.join(self.directory,self.inpdir))
        # 读取粒子
        self.particles = np.loadtxt('particles.dat', skiprows=1, dtype=float, usecols=[1,2])
        num_particles_all = self.particles.shape[0]
        if num_particles_all < self.thread_nums:
            print(f"警告:  总粒子数 ({num_particles_all}) 小于总线程数 ({self.thread_nums})")
        num_shouldbe = num_particles_all//self.thread_nums              # 最少每个有多少 +1为其他
        num_error = num_particles_all - num_shouldbe*self.thread_nums   # 多少个+1
        j_all = 0
        for i in range(self.thread_nums):
            with open(f"{self.casename}_{i:03d}.dat", 'w') as fout:
                if i < num_error:                                       # 未达到组数,为n+1个
                    j_max = num_shouldbe+1
                else:                                                   # 达到组数,为n个
                    j_max = num_shouldbe
                    if j_max == 0:                                      # 不足每线程一个粒子则停止
                        break
                # 处理nml文件
                os.system(f'cp ../{self.casename}_run.dat ../{self.casename}_{i:3d}_run.dat')
                with open ('../{self.casename}_{i:3d}_run.dat') as f_nml:
                    lines = f_nml.readlines()
                    for i_line,line in enumerate(lines):
                        if 'LAGINI =' in line:
                            lines[i_line] = line.rstrip()+f'_{i:3d}\n'
                    f_nml.writelines(lines)
                # 开始写入粒子文件
                fout.write(str(j_max)+'\n')
                for j in range(j_max):
                    fout.write(f'{j+1:3d} {self.particles[j_all,0]:10.6f} {self.particles[j_all,1]:10.7f} 0.000\n')
                    j_all += 1
            # 写入运行脚本
            with open('pbs{:03d}_'.format(i-1)+str(self.configfile['Lagrangian']['General']['Dragc']), 'w') as fout:
                fout.write("""#!/bin/bash
#SBATCH --job-name="{:03d}_""".format(i-1)+str(self.configfile['Lagrangian']['General']['Dragc'])+""""
#SBATCH --partition="cpu"
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 144:00:00
#SBATCH --output={:03d}_""".format(i-1)+str(self.configfile['Lagrangian']['General']['Dragc'])+""".log
#SBATCH --error={:03d}_""".format(i-1)+str(self.configfile['Lagrangian']['General']['Dragc'])+""".error


###以上部分说明：###
####第一段部分，后面不可以有注释，不可以有空格！！！！！
#SBATCH 
#SBATCH -t 144:00:00                            ###作业强制终止时间.可自定义时长。格式为“小时：分钟：秒”

echo "SLURM_JOBID= "$SLURM_JOBID
echo "SLURM_JOB_NODELIST= "$SLURM_JOB_NODELIST
echo "SLURM_NNODES= "$SLURM_NNODES
echo "SLURMTMPDIR= "$SLURMTMPDIR
echo "working directory= "$SLURM_SUBMIT_DIR

NPROCS=`srun --nodes=${SLURM_NNODES} bash -c 'hostname' | wc -l`
echo "Number of Processors = "$NPROCS

module use /public/software/modulefiles
module purge
module load netcdf-fortran/4.6.2
./ptraj_inverse_"""+str(self.configfile['Lagrangian']['General']['Dragc'])+""" Jun_2025_{:03d}_""".format(i-1)+str(self.configfile['Lagrangian']['General']['Dragc']))
        shutil.rmtree(f"{self.lagini}_run.dat")
        shutil.rmtree(f"../{self.casename}_run.dat")
        os.chdir(current_dir)