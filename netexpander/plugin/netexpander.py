
from argparse import ArgumentParser
from anasymod.plugins import Plugin

class CustomPlugin(Plugin):
    def __init__(self, cfg_file, prj_root, build_root):
        super().__init__(cfg_file=cfg_file, prj_root=prj_root, build_root=build_root, name='netexplorer')

        # Parse command line arguments specific to MSDSL
        self.args = None
        self._parse_args()

        # Initialize netexplorer config

        # Update netexplorer config with netexplorer section in config file
        self.cfg.update_config(subsection=self._name)

        # Add defines according to command line arguments

        ###############################################################
        # Execute actions according to command line arguments
        ###############################################################

        # explore
        if self.args.explore:
            self.explore()

        # Setup Defines; after this step, defines shall not be added anymore in MSDSL

##### Functions exposed for user to exercise on Analysis Object

    def explore(self):
        """
        Convert SV or Verilog netlist input replacing IFX specific types such as ANALOG_T and CURRENT_T to svreal
        compliant data types als taking into account additional functionalities that need to be expressed by additional
        svreal operations.
        """
        pass

##### Utility Functions

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view
        """
        parser = ArgumentParser()
        parser.add_argument('--explore', action='store_true')

        self.args, _ = parser.parse_known_args()
