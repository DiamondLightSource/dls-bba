"""This file contains slow BBA specific functions and classes"""

import logging as log

from bba.common import Algorithm, RawData, Results


class SBBA(Algorithm):
    def __init__(self, accelerator):
        super().__init__(accelerator)
        self.configure()

    def configure(self, quadrupole_scalar = 0.01, decimated = False):
        """These are optional arguments, which are used during testing."""
        self.quadrupole_scalar = quadrupole_scalar
        self.decimated = decimated
        #self.PLOT_GRAPHS = PLOT_GRAPHS

    def run(self, element, plane_info, max_orbit) -> RawData:
        method = "SBBA"
        log.info(f"{method} process started in plane {plane_info.axis}.")

        bpm, quad_list, corrector = self.select_elements(element, plane_info)
        quad_pv_list = [self._accelerator.element_to_pv_prefix(quad_element) for quad_element in quad_list]
        bpm_pv_prefix = self._accelerator.element_to_pv_prefix(bpm)
        corrector_pv_prefix = self._accelerator.element_to_pv_prefix(corrector, plane_info)
        log.info(f"Quads: {quad_pv_list}, BPM: {bpm_pv_prefix}, Corrector: {corrector_pv_prefix}.")
        raw_data = {}
        metadata = {
            "method" : method,
            "plane" : plane_info,
            "quad" : quad_pv_list,
            "bpm" : [bpm_pv_prefix, self._accelerator.bpms.index(bpm)],
            "corrector" : corrector_pv_prefix,
            "decimated" : self.decimated,
            "enabled_bpms" : self._accelerator.enabled_bpms}
        for quad in quad_list:
            self.toggle_feedbacks(max_orbit)
            original_offsets = self.zero_origins(bpm, plane_info)
            quad_step = self._accelerator.measure_quad(quad) * self.quadrupole_scalar
            # Changed for testing. 
            corr_amp = self._accelerator.microrads(corrector, plane_info)
            log.info(f"Quad step: {quad_step}, Corrector step: {corr_amp}.")
            # TODO: Slow BBA Process
            print("Not implimented yet")
            # Get Data
            #append to raw_data dict in terms of quad_pv.
            # raw_data[self._accelerator.element_to_pv_prefix(quad)+":High"] = selected_data[0]
            # reset quad
            # self._accelerator.set_quad(quad, quad_sp)
            self.restore_origins(original_offsets)

        return RawData(raw_data, method, metadata)
    
    def analyse_data(self, raw_data, plot_output, *args, **kwargs) -> Results:
        data = raw_data["raw_data"]
        algorithm = raw_data["algorithm"]
        metadata= raw_data["metadata"]
        results = {

        }
        offset = 0
        error = 0


        bpm_pv_prefix = metadata['bpm'][0]
        return Results(results, bpm_pv_prefix, metadata)
