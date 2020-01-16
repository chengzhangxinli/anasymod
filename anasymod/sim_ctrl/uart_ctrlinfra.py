import serial
import io, os
import serial.tools.list_ports as ports
from anasymod.enums import CtrlOps
from anasymod.sim_ctrl.ctrlinfra import ControlInfrastructure
from anasymod.structures.module_uartsimctrl import ModuleUARTSimCtrl
from anasymod.structures.module_regmapsimctrl import ModuleRegMapSimCtrl
from anasymod.sources import VerilogSource, BDFile
from anasymod.files import get_from_anasymod
from anasymod.structures.structure_config import StructureConfig

class UARTControlInfrastructure(ControlInfrastructure):
    def __init__(self, prj_cfg):
        super().__init__(prj_cfg=prj_cfg)

        # Initialize internal variables
        self._simctrlregmap_path = os.path.join(prj_cfg.build_root, 'gen_ctrlregmap.sv')

        # Program Zynq PS for UART access
        self._program_zynq_ps()
        #HIER WEITER: #ToDo: add path to elf file and add structure for storing ctrl ifc dependent files, also including the BD; later test if .tcl script for creating BD would be beneficial/at least there should be a script for creating the .bd file for a new Vivado version, also add binary path to xsct interface
        self.vid_list = [1027]
        self.pid_list = [24592]
        self.port_list = []

    #User functions
    def init_control(self):
        """
        Initialize the control interface, this is usually done after the bitstream was programmed successfully on the FPGA.
        """
        if self.cfg.comport is None: # run auto search for finding the correct COM port
            # find all available COM ports
            comports = [port for port in ports.comports(include_links=True)]
            # check if any COM port is compliant to known vids and pids and if so store the device_id
            for port in comports:
                if ((port.vid in self.vid_list) and (port.pid in self.pid_list)):
                    self.port_list.append(port.device)

            for port in self.port_list:
                try:
                    self._init_handler(comport=port)
                except:
                    pass
            if self.cfg.comport is None:
                raise Exception(f"ERROR: No COM port could be opened to enable connection to FPGA, found ports were: {self.port_list}.")

        else:
            try:
                self._init_handler(comport=self.cfg.comport)
            except:
                raise Exception(f"ERROR: Provided COM port: {self.cfg.comport} could not ne opened for communication.")

    def write_parameter(self, addr, data):
        self._write(operation=CtrlOps.WRITE_PARAMETER, addr=addr, data=data)
        if self._read():
            raise Exception(f"ERROR: Couldn't properly write: {addr}={data} command to FPGA.")

    def read_parameter(self, addr):
        self._write(operation=CtrlOps.READ_PARAMETER, addr=addr)
        return self._read()

    #Utility functions
    def _init_handler(self, comport):
        self.ctrl_handler = serial.Serial(comport, int(self.cfg.baud_rate), timeout=self.cfg.timeout,
                                          parity=self.cfg.parity, stopbits=self.cfg.stopbits,
                                          bytesize=self.cfg.bytesize)
        self.cfg.comport = comport

    def _write(self, operation, addr, data=None):
        # check is space is in any of the give input strings
        if ' ' in [operation, addr, data]:
            raise Exception(f"Blanks in any of the provided argument strings;{operation}, {addr}, {data}; sent via control interface are not allowed!")

        self.ctrl_handler.write((' '.join([str(operation), str(addr), str(data) + '\r']).encode('utf-8')))
        self.ctrl_handler.flush()

    def _read(self, count=1):
        for idx in range(count):
            result = self.ctrl_handler.readline()

            if result not in ['', None]:
                return int(result.decode("utf-8").rstrip())
        raise Exception(f"ERROR: Couldn't read from FPGA after:{count} attempts.")

    def gen_ctrlwrapper(self, str_cfg: StructureConfig, content):
        """
        Generate RTL design for control infrastructure. This will generate the register map, add the block diagram
        including the zynq PS and add the firmware running on the zynq PS.
        """

        # Generate simulation control wrapper and add to target sources
        with (open(self._simctrlwrap_path, 'w')) as ctrl_file:
           ctrl_file.write(ModuleUARTSimCtrl(scfg=str_cfg).render())

        content['verilog_sources'] += [VerilogSource(files=self._simctrlwrap_path)]

    def gen_ctrl_infrastructure(self, str_cfg: StructureConfig, content):
        """
        Generate RTL design for FPGA specific control infrastructure, depending on the interface selected for communication.
        For UART_ZYNQ control a register map, ZYNQ CPU SS block diagram and the firmware running on the zynq PS
        need to be handled.

        """

        # Generate register map according to IO settings stored in structure config and add to target sources
        with (open(self._simctrlregmap_path, 'w')) as ctrl_file:
           ctrl_file.write(ModuleRegMapSimCtrl(scfg=str_cfg).render())

        content['verilog_sources'] += [VerilogSource(files=self._simctrlregmap_path)]

        # Add ZYNQ CPU subsystem to target sources for UART IO as a blockdiagram
        zynq_bd = BDFile(files=get_from_anasymod('verilog', 'zynq_uart.bd'))
        content['bd_files'].append(zynq_bd)

        #ToDo: Add firmware part here -> generate FW if needed and add it to target sources

    def _program_zynq_ps(self):
        """
        Program UART control application to Zynq PS to enable UART control interface.
        """
        pass
        #HIER WEITER

    def add_ip_cores(self, scfg, ip_dir):
        """
        Configures and adds IP cores that are necessary for selected IP cores. No IP core is configured and added.
        :return rendered template for configuring a vio IP core
        """
        return []

def main():
    ctrl = UARTControlInfrastructure(prj_cfg=EmuConfig(root='test', cfg_file=''))
    ctrl.write_parameter(addr=0, data=3)
    ctrl.write_parameter(addr=1, data=4)
    print(ctrl.read_parameter(addr=0))
    print(ctrl.read_parameter(addr=1))

if __name__ == "__main__":
    main()