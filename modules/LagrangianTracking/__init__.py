import toml
from ..log import AppLogger


class LagrangianTracking:

    def __init__(self, configfile):
        self.configfile = toml.load(configfile)
        self.inverse = self.configfile['Lagrangian']['Inverse']
        self.version = self.configfile['Lagrangian']['Version']
        self.dti = self.configfile['Lagrangian']['Time Integration']['DTI']
        self.instp = self.configfile['Lagrangian']['Time Integration']['INSTP']
        self.dtout = self.configfile['Lagrangian']['Time Integration']['DTOUT']
        self.tdrift = self.configfile['Lagrangian']['Time Integration']['TDRIFT']
        self.yearlag = self.configfile['Lagrangian']['Start Time']['YEARLAG']
        self.monthlag = self.configfile['Lagrangian']['Start Time']['MONTHLAG']
        self.daylag = self.configfile['Lagrangian']['Start Time']['DAYLAG']
        self.hourlag = self.configfile['Lagrangian']['Start Time']['HOURLAG']
        self.inpdir = self.configfile['Lagrangian']['IO Location']['INPDIR']
        self.geoarea = self.configfile['Lagrangian']['IO Location']['GEOAREA']
        self.outdir = self.configfile['Lagrangian']['IO Location']['OUTDIR']
        self.infofile = self.configfile['Lagrangian']['IO Location']['INFOFILE']
        self.lagini = self.configfile['Lagrangian']['IO Location']['LAGINI']
        self.f_depth = self.configfile['Lagrangian']['SIGMA or CARTESIAN']['F_DEPTH']
        self.p_sigma = self.configfile['Lagrangian']['SIGMA or CARTESIAN']['P_SIGMA']
        self.outsigma = self.configfile['Lagrangian']['SIGMA or CARTESIAN']['OUTSIGMA']
        self.irw = self.configfile['Lagrangian']['Random Walk']['IRW']
        self.dhor = self.configfile['Lagrangian']['Random Walk']['DHOR']
        self.dtrw = self.configfile['Lagrangian']['Random Walk']['DTRW']
        self.cart_shp = self.configfile['Lagrangian']['Projection Control']['CART_SHP']
        self.projection_reference = self.configfile['Lagrangian']['Projection Control']['PROJECTION_REFERENCE']

    def nml_writer(selfself):

    def

