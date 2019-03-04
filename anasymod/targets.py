import os

from anasymod.defines import Define
from anasymod.util import back2fwd
from anasymod.config import EmuConfig
from anasymod.sources import Sources, VerilogSource, VerilogHeader, VHDLSource

class Target():
    """
    This class inherits all source and define objects necessary in order to run actions for a specific target.

    Attributes:
        _name               Target name
        content    Dict of Lists of source and define objects associated with target
    """
    def __init__(self, prj_cfg, name):
        self._prj_cfg = prj_cfg
        self._name = name

        # Initialize content dict  to store design sources and defines
        self.content = {}
        self.content['verilog_sources'] = []
        """:type : List[VerilogSource]"""
        self.content['verilog_headers'] = []
        """:type : List[VerilogHeader]"""
        self.content['vhdl_sources'] = []
        """:type : List[VHDLSource]"""
        self.content['defines'] = []
        """:type : List[Define]"""

        # Initialize target_config
        self.cfg = {}
        self.cfg['tstop'] = 1e-05
        self.cfg['top_module'] = 'top'
        self.cfg['vcd_name'] = f"{self.cfg['top_module']}_{self._name}.vcd"
        self.cfg['vcd_path'] = os.path.join(self._prj_cfg.build_root, r"vcd", self.cfg['vcd_name'])

    def set_tstop(self):
        """
        Add define statement to specify tstop
        """
        self.content['defines'].append(Define(name='TSTOP_MSDSL', value=self.cfg['tstop']))

    def assign_fileset(self, fileset: dict):
        """
        Add a fileset to the target by adding defines and sources to the according attributes

        :param fileset: fileset that shall be added to target
        :type fileset: dict
        """

        for k in fileset.keys():
            self.content[k] += fileset[k]

    def update_config(self, config_section: dict=None):
        if config_section is not None:
            for k, v in config_section.items():
                if k in self.cfg:
                    self.cfg[k] = v
                else:
                    print(f"Warning: During target config update; provided config key: {k} in target: {self._name} does not exist")

class SimulationTarget(Target):
    def __init__(self, prj_cfg: EmuConfig, name=r"sim"):
        super().__init__(prj_cfg=prj_cfg, name=name)

    def setup_vcd(self):
        self.content['defines'].append(Define(name='VCD_FILE_MSDSL', value=back2fwd(self.cfg['vcd_path'])))

class FPGATarget(Target):
    """

    Attributes:
        _ip_cores        List of ip_core objects associated with target, those will generated during the build process
    """
    def __init__(self, prj_cfg: EmuConfig, name=r"fpga"):
        super().__init__(prj_cfg=prj_cfg, name=name)
        self._ip_cores = []

        self.cfg['csv_name'] = f"{self.cfg['top_module']}_{self._name}.csv"
        self.cfg['csv_path'] = os.path.join(self._prj_cfg.build_root, r"csv", self.cfg['csv_name'])
