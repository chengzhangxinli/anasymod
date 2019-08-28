#from anasymod.targets import FPGATarget, Target
from anasymod.enums import PortDir
from anasymod.gen_api import SVAPI
from anasymod.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.structures.structure_config import StructureConfig

class ModuleTop(JinjaTempl):
    """
    This is the generator for top.sv.
    """
    def __init__(self, target):
        super().__init__(trim_blocks=True, lstrip_blocks=True)
        scfg = target.str_cfg
        """ :type: StructureConfig """

        #####################################################
        # Create module interface
        #####################################################
        self.module_ifc = SVAPI()

        for port in scfg.clk_i_ports:
            port.direction = PortDir.IN
            self.module_ifc.gen_port(port)

        #####################################################
        # Instantiate clk management
        #####################################################

        # Add clk in signals for simulation case
        self.clk_in_sim_sigs = SVAPI()

        for port in scfg.clk_i_ports:
            self.clk_in_sim_sigs.gen_signal(port=port)

        # Add dbg clk signals
        self.dbg_clk_sigs = SVAPI()

        for port in scfg.clk_d_ports:
            self.dbg_clk_sigs.gen_signal(port=port)

        self.clk_ifc = SVAPI()

        for port in scfg.clk_i_ports + scfg.clk_o_ports + scfg.clk_m_ports + scfg.clk_d_ports + scfg.clk_g_ports:
            port.connection = port.name
            self.clk_ifc.println(f".{port.name}({port.connection})")

        #####################################################
        # Instantiate Ctrl Module
        #####################################################

        custom_ctrl_ios = scfg.analog_ctrl_inputs + scfg.analog_ctrl_outputs + scfg.digital_ctrl_inputs + \
                          scfg.digital_ctrl_outputs

        ctrl_ios = custom_ctrl_ios + scfg.dec_thr_ctrl + scfg.reset_ctrl

        ## Instantiate all ctrl signals
        self.inst_itl_ctlsigs = SVAPI()
        for ctrl_io in ctrl_ios:
            self.inst_itl_ctlsigs._gen_signal(io_obj=ctrl_io)

        ## Instantiate ctrl module
        self.ctrl_module_ifc = SVAPI()

        for ctrl_io in ctrl_ios:
            self.ctrl_module_ifc.println(f".{ctrl_io.name}({ctrl_io.name})")

        # add master clk to ctrl module
        self.ctrl_module_ifc.println(f".{scfg.clk_m_ports[0].name}({scfg.clk_m_ports[0].name})")

        ## Assign custom ctrl signals via abs paths into design
        self.assign_custom_ctlsigs = SVAPI()
        for ctrl_io in custom_ctrl_ios:
            self.assign_custom_ctlsigs.assign_to(io_obj=ctrl_io)

        #####################################################
        # Instantiate testbench
        #####################################################
        self.tb_ifc = SVAPI()

        tb_ports = scfg.clk_o_ports
        for port in tb_ports:
            port.connection = port.name
            self.tb_ifc.println(f".{port.name}({port.connection})")


    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`include "msdsl.sv"

`default_nettype none

module top(
    `ifndef SIMULATION_MODE_MSDSL
    {% for line in subst.module_ifc.text.splitlines() %}
        {{line}}{{ "," if not loop.last }}
    {% endfor %}
    `endif // `ifndef SIMULATION_MODE_MSDSL
);

// create ext_clk signal when running in simulation mode
`ifdef SIMULATION_MODE_MSDSL
    logic ext_clk;
    {% for line in subst.clk_in_sim_sigs.text.splitlines() %}
        {{line}}
    {% endfor %}
`endif // `ifdef SIMULATION_MODE_MSDSL

// debug clk declaration
{% for line in subst.dbg_clk_sigs.text.splitlines() %}
    {{line}}
{% endfor %}

// emulation clock declarations
logic emu_clk, emu_rst;

// Declaration of control signals
{{subst.inst_itl_ctlsigs.text}}

// Assignment of custom control signals via absolute paths to design signals
{{subst.assign_custom_ctlsigs.text}}

// VIO
//{% for line in subst.inst_itl_ctlsigs.text.splitlines() -%}
//    {{line}}
//{% endfor %}

// Instantiation of control wrapper
sim_ctrl_gen sim_ctrl_gen_i(
{% for line in subst.ctrl_module_ifc.text.splitlines() %}
    {{line}}{{ "," if not loop.last }}
{% endfor %}
);

// Clock generator
clk_gen clk_gen_i(
{% for line in subst.clk_ifc.text.splitlines() %}
    {{line}}{{ "," if not loop.last }}
{% endfor %}
);

// make probes needed for emulation control
`MAKE_EMU_CTRL_PROBES;

// instantiate testbench
tb tb_i(
{% for line in subst.tb_ifc.text.splitlines() %}
    {{line}}{{ "," if not loop.last }}
{% endfor %}
);

// simulation control
`ifdef SIMULATION_MODE_MSDSL
    // stop simulation after some time
    initial begin
        #((`TSTOP_MSDSL)*1s);
        $finish;
    end

    // dump waveforms to a specified VCD file
    `define ADD_QUOTES_TO_MACRO(macro) `"macro`"
    initial begin
        $dumpfile(`ADD_QUOTES_TO_MACRO(`VCD_FILE_MSDSL));
    end
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule

`default_nettype wire
'''

def main():
    print(ModuleTop(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()