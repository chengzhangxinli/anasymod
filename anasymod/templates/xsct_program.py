from anasymod.util import back2fwd

# References:
# 1. https://www.xilinx.com/html_docs/xilinx2018_1/SDK_Doc/xsct/use_cases/xsdb_standalone_app_debug.html
# 2. https://github.com/Digilent/Arty-Z7-20-linux_bd/blob/master/sdk/.sdk/launch_scripts/xilinx_c-c%2B%2B_application_(system_debugger)/system_debugger_using_debug_video.elf_on_local.tcl
# 3. https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/18842240/Programming+QSPI+from+U-boot+ZC702

class TemplXSCTProgram:
    def __init__(self, sdk_path, bit_path, hw_path, tcl_path, cpu_filter='"ARM*#0"',
                 sw_name='sw', program_fpga=True, reset_system=True):

        # initialize text
        self.text = ''

        # apply commands

        self.connect()

        if program_fpga:
            self.program_fpga(bit_path)

        self.select_cpu(cpu_filter)

        if reset_system:
            self.reset_system()

        self.loadhw(hw_path)

        #test
        # Connect to hardware
        #self.line('puts "open_hw"')
        #self.line('open_hw')
        #self.line('puts "connect_hw_server"')
        #self.line('connect_hw_server')
        #self.line('set_property PARAM.FREQUENCY {{subst.jtag_freq}} [get_hw_targets]')
        #self.line('open_hw_target')

        # Configure files to be programmed
        #self.line('set my_hw_device [get_hw_devices {{subst.device_name}}*]')
        #self.line('current_hw_device $my_hw_device')
        #self.line('refresh_hw_device $my_hw_device')
        #self.line('set_property PROGRAM.FILE "{{subst.bit_file}}" $my_hw_device')
        #self.line('set_property PROBES.FILE "{{subst.ltx_file}}" $my_hw_device')
        #self.line('set_property FULL_PROBES.FILE "{{subst.ltx_file}}" $my_hw_device')
        #end


        self.init_cpu(tcl_path)

        self.download(str(sdk_path / sw_name / 'Debug' / sw_name) + '.elf')

        self.run()

        self.puts("Program started.")

    def line(self, s='', nl='\n'):
        self.text += f'{s}{nl}'

    def puts(self, s):
        self.line(f'puts "{s}"')

    def connect(self):
        self.puts('Connecting to the HW server...')
        self.line('connect')
        self.line()

    def select_cpu(self, cpu_filter):
        self.puts('Selecting the CPU...')
        self.line(f'targets -set -filter {{name =~ {cpu_filter}}}')
        self.line()

    def reset_system(self):
        self.puts('Resetting the system...')
        self.line('rst')
        self.line()

    def program_fpga(self, bit_path):
        self.puts('Programming the FPGA...')
        self.line(f'fpga "{bit_path.as_posix()}"')
        self.line()

    def loadhw(self, hw_path):
        self.puts('Setting up the debugger...')
        hw_path_hdf = hw_path.with_suffix('.hdf')
        self.line(f'loadhw "{hw_path_hdf.as_posix()}"')
        self.line()

    def init_cpu(self, tcl_path):
        self.puts('Initializing the processor...')
        self.line(f'source "{tcl_path.as_posix()}"')
        self.line('ps7_init')
        self.line('ps7_post_config')
        self.line()

    def download(self, elf_path):
        self.puts('Downloading the program...')
        self.line(f'dow "{back2fwd(elf_path)}"')
        self.line()

    def run(self):
        self.puts('Starting the program...')
        self.line('con')
        self.line()
