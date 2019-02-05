import os.path

from anasymod.vivado import VivadoControl
from anasymod.codegen import CodeGenerator
from anasymod.config import EmuConfig
from anasymod.util import back2fwd

from anasymod.blocks.ila import TemplILA
from anasymod.blocks.dbg_hub import TemplDbgHub
from anasymod.blocks.ext_clk import TemplExtClk
from anasymod.blocks.clk_wiz import TemplClkWiz
from anasymod.blocks.vio import TemplVIO, VioOutput
from anasymod.blocks.probe_extract import TemplPROBE_EXTRACT
from anasymod.blocks.execute_FPGA_sim import TemplEXECUTE_FPGA_SIM

class VivadoBuild():
    def __init__(self, cfg: EmuConfig):
        # save settings
        self.cfg = cfg

        # TCL generators
        self.v = VivadoControl()

    def build(self):
        # create a new project
        self.v.create_project(project_name=self.cfg.vivado_config.project_name,
                              project_directory=self.cfg.vivado_config.project_directory,
                              full_part_name=self.cfg.fpga_board_config.full_part_name,
                              force=True)

        # add all source files to the project (including header files)
        self.v.add_project_contents(sources=self.cfg.synth_verilog_sources,
                                    headers=self.cfg.synth_verilog_headers)

        # define the top module
        self.v.set_property('top', f'{{{self.cfg.top_module}}}', '[current_fileset]')

        # set define variables
        self.v.set_property('verilog_define', f"{{{' '.join(self.cfg.synth_verilog_defines)}}}", '[current_fileset]')

        # write constraints to file
        constrs = CodeGenerator()

        constrs.use_templ(TemplExtClk(ext_clk_pin=self.cfg.fpga_board_config.clk_pin,
                                      ext_clk_io_std=self.cfg.fpga_board_config.clk_io,
                                      ext_clk_freq=self.cfg.fpga_board_config.clk_freq))

        cpath = os.path.join(self.cfg.build_dir, 'constrs.xdc')
        constrs.write_to_file(cpath)

        # add constraints to project
        self.v.add_files([back2fwd(cpath)], fileset='constrs_1')

        # generate the IP blocks
        self.v.use_templ(TemplClkWiz(input_freq=self.cfg.fpga_board_config.clk_freq,
                                     output_freqs=[self.cfg.emu_clk_freq, self.cfg.dbg_hub_clk_freq],
                                     ip_dir=self.ip_dir))
        self.v.use_templ(TemplVIO(outputs=[VioOutput(width=1)], ip_dir=self.ip_dir, ip_module_name=self.cfg.vivado_config.vio_name))

        # generate all IPs
        self.v.println('generate_target all [get_ips]')

        # run synthesis
        self.v.println('reset_run synth_1')
        self.v.println('launch_runs synth_1 -jobs {0}'.format(self.cfg.vivado_config.num_cores))
        self.v.println('wait_on_run synth_1')

        # extact probes from design
        self.v.use_templ(TemplPROBE_EXTRACT(cfg=self.cfg))

        self.v.run(vivado=self.cfg.vivado_config.vivado, build_dir=self.cfg.build_dir, filename=r"synthesis.tcl")

        # append const file with ILA according to extracted probes
        constrs.read_from_file(cpath)
        constrs.use_templ(TemplILA(probe_cfg_path=self.cfg.vivado_config.probe_cfg_path,
                                   depth=self.cfg.ila_depth, inst_name=self.cfg.vivado_config.ila_inst_name))

        constrs.use_templ(TemplDbgHub(dbg_hub_clk_freq=self.cfg.dbg_hub_clk_freq))
        constrs.write_to_file(cpath)

        # Open project
        self.v.println(f'open_project {back2fwd(os.path.join(self.cfg.build_dir, self.cfg.vivado_config.project_directory, self.cfg.vivado_config.project_name + r".xpr"))}')

        # launch the build and wait for it to finish
        self.v.println('launch_runs impl_1 -to_step write_bitstream -jobs {0}'.format(self.cfg.vivado_config.num_cores))
        self.v.println('wait_on_run impl_1')

        # self.v.println('refresh_design')
        # self.v.println('puts [get_nets - hier - filter {MARK_DEBUG}]')

        # run bitstream generation
        self.v.run(vivado=self.cfg.vivado_config.vivado, build_dir=self.cfg.build_dir, filename=r"bitstream.tcl")

    def run_FPGA(self):
        self.v.use_templ(TemplEXECUTE_FPGA_SIM(cfg=self.cfg))
        self.v.run(vivado=self.cfg.vivado_config.vivado, build_dir=self.cfg.build_dir, filename=r"run_FPGA.tcl")

    @property
    def ip_dir(self):
        return os.path.join(
            self.cfg.build_dir,
            self.cfg.vivado_config.project_directory,
            f'{self.cfg.vivado_config.project_name}.srcs',
            'sources_1',
            'ip'
        )