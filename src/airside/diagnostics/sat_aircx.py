# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Installable Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2022 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}

import logging

from collections import defaultdict

from volttron.utils import setup_logging
from volttron.utils.math_utils import mean

from airside.diagnostics import common


setup_logging()
_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s   %(levelname)-8s %(message)s",
                    datefmt="%m-%d-%y %H:%M:%S")


INCONSISTENT_DATE = -89.2
INSUFFICIENT_DATA = -79.2
SA_VALIDATE = "Supply-air Temperature ACCx"
SA_TEMP_RCX = "Supply-air Temperature Set Point Control Loop Dx"
SA_TEMP_RCX1 = "Low Supply-air Temperature Dx"
SA_TEMP_RCX2 = "High Supply-air Temperature Dx"
DX = "/diagnostic message"

DX_LIST = [SA_TEMP_RCX, SA_TEMP_RCX1, SA_TEMP_RCX2]


class SupplyTempAIRCx(object):
    """Air-side HVAC Self-Correcting Diagnostic: Detect and correct supply-air
    temperature problems.

    Fields:
        timestamp_array (List[datetime]): timestamps for analysis period.
        sat_stpt_arr (List[float]): supply-air temperature set point
            for analysis period.
        satemp_arr (List[float]): supply-air temperature for analysis period.
        rht_arr (List[float]): terminal box reheat command for analysis period.

    """
    def __init__(self):
        self.timestamp_array = []
        self.sat_stpt_array = []
        self.sat_array = []
        self.rht_array = []
        self.percent_rht = []
        self.percent_dmpr = defaultdict(list)
        self.table_key = None
        self.command_tuple = []

        # Common RCx parameters
        self.publish_results = None
        self.send_autocorrect_command = None
        self.sat_stpt_cname = ""
        self.no_req_data = 0
        self.auto_correct_flag = False
        self.stpt_deviation_thr = None
        self.rht_on_thr = None
        self.percent_rht_thr = None
        self.data_window = 0

        # Low SAT RCx thresholds
        self.rht_valve_thr = None
        self.max_sat_stpt = None

        # High SAT RCx thresholds
        self.high_dmpr_thr = None
        self.percent_dmpr_thr = None
        self.min_sat_stpt = None
        self.sat_retuning = None

    def set_class_values(self, command_tuple, no_req_data, data_window, auto_correct_flag, stpt_deviation_thr, rht_on_thr, high_dmpr_thr,
                         percent_dmpr_thr, percent_rht_thr, min_sat_stpt, sat_retuning, rht_valve_thr, max_sat_stpt, sat_stpt_cname):
        """Set the values needed for doing the diagnostics"""

        self.command_tuple = command_tuple
        self.sat_stpt_cname = sat_stpt_cname
        self.no_req_data = no_req_data
        self.auto_correct_flag = False
        if isinstance(auto_correct_flag, str) and auto_correct_flag in ["low", "normal", "high"]:
            self.auto_correct_flag = auto_correct_flag
        self.stpt_deviation_thr = stpt_deviation_thr
        self.rht_on_thr = rht_on_thr
        self.percent_rht_thr = percent_rht_thr
        self.data_window = data_window
        # Low SAT RCx thresholds
        self.rht_valve_thr = rht_valve_thr
        self.max_sat_stpt = max_sat_stpt

        # High SAT RCx thresholds
        self.high_dmpr_thr = high_dmpr_thr
        self.percent_dmpr_thr = percent_dmpr_thr
        self.min_sat_stpt = min_sat_stpt
        self.sat_retuning = sat_retuning

    def setup_platform_interfaces(self, publish_method, autocorrect_method):
        self.publish_results = publish_method
        self.send_autocorrect_command = autocorrect_method

    def reinitialize(self):
        """
        Reinitialize data arrays.
        :return:
        """
        self.table_key = None
        self.timestamp_array = []
        self.sat_stpt_array = []
        self.sat_array = []
        self.rht_array = []
        self.percent_rht = []
        self.percent_dmpr = defaultdict(list)

    def sat_aircx(self, current_time, sat_data, sat_stpt_data,
                  zone_rht_data, zone_dmpr_data):
        """Manages supply-air diagnostic data sets.

        Args:
            current_time (datetime): current timestamp for trend data.
            sat_data (lst of floats): supply-air temperature measurement for
                AHU.
            sat_stpt_data (List[floats]): supply-air temperature set point
                data for AHU.
            zone_rht_data (List[floats]): reheat command for terminal boxes
                served by AHU.
            zone_dmpr_data (List[floats]): damper command for terminal boxes
                served by AHU.

        Returns:
            Status of diagnostic (dx_status)

        """
        tot_rht = sum(1 if val > self.rht_on_thr else 0 for val in zone_rht_data)
        count_rht = len(zone_rht_data)
        tot_dmpr = {}
        for key, thr in self.high_dmpr_thr.items():
            tot_dmpr[key] = sum(1 if val > thr else 0 for val in zone_dmpr_data)
        count_damper = len(zone_dmpr_data)

        if common.check_date(current_time, self.timestamp_array):
            common.pre_conditions(self.publish_results, INCONSISTENT_DATE, DX_LIST, current_time)
            self.reinitialize()

        run_status = common.check_run_status(self.timestamp_array, current_time, self.no_req_data, self.data_window)

        if run_status is None:
            _log.info("{} - Insufficient data to produce a valid diagnostic result.".format(current_time))
            common.pre_conditions(self.publish_results, INSUFFICIENT_DATA, DX_LIST, current_time)
            self.reinitialize()

        if run_status:
            avg_sat_stpt, dx_string, dx_msg = common.setpoint_control_check(self.sat_stpt_array, self.sat_array, self.stpt_deviation_thr, SA_TEMP_RCX)
            _log.info(common.table_log_format(current_time, dx_string + str(dx_msg)))
            self.publish_results(current_time, dx_string, dx_msg)
            if self.percent_rht and self.rht_array:
                self.low_sat(avg_sat_stpt)
                self.high_sat(avg_sat_stpt)
            else:
                diagnostic_msg = {"low": 89.2, "normal": 89.2, "high": 89.2}
                self.publish_results(self.timestamp_array[-1], SA_TEMP_RCX1 + DX, diagnostic_msg)
                self.publish_results(self.timestamp_array[-1], SA_TEMP_RCX2 + DX, diagnostic_msg)
            self.reinitialize()

        self.sat_array.append(mean(sat_data))
        if sat_stpt_data:
            self.sat_stpt_array.append(mean(sat_stpt_data))
        if zone_rht_data and count_rht > 0:
            self.percent_rht.append(tot_rht / count_rht)
            self.rht_array.append(mean(zone_rht_data))
        self.timestamp_array.append(current_time)
        for key in self.high_dmpr_thr:
            self.percent_dmpr[key].append(tot_dmpr[key] / count_damper)

    def low_sat(self, avg_sat_stpt):
        """
        Diagnostic to identify and correct low supply-air temperature
        (correction by modifying SAT set point).
        :param avg_sat_stpt:
        :return:
        """
        avg_zones_rht = mean(self.percent_rht)*100.0
        rht_avg = mean(self.rht_array)
        thresholds = zip(self.rht_valve_thr.items(), self.percent_rht_thr.items())
        diagnostic_msg = {}

        for (key, rht_valve_thr), (key2, percent_rht_thr) in thresholds:
            if rht_avg > rht_valve_thr and avg_zones_rht > percent_rht_thr:
                if avg_sat_stpt is None:
                    # Create diagnostic message for fault
                    # when supply-air temperature set point
                    # is not available.
                    msg = "{} - The SAT too low but SAT set point data is not available.".format(key)
                    result = 44.1
                elif self.auto_correct_flag and self.auto_correct_flag == key:
                    aircx_sat_stpt = avg_sat_stpt + self.sat_retuning
                    if aircx_sat_stpt <= self.max_sat_stpt:
                        self.send_autocorrect_command(self.sat_stpt_cname, aircx_sat_stpt)
                        sat_stpt = "%s" % float("%.2g" % aircx_sat_stpt)
                        msg = "{} - SAT too low. SAT set point increased to: {}F".format(key, sat_stpt)
                        result = 41.1
                    else:
                        self.send_autocorrect_command(self.sat_stpt_cname, self.max_sat_stpt)
                        sat_stpt = "%s" % float("%.2g" % self.max_sat_stpt)
                        sat_stpt = str(sat_stpt)
                        msg = "{} - SAT too low. Auto-correcting to max SAT set point {}F".format(key, sat_stpt)
                        result = 42.1
                else:
                    msg = "{} - SAT detected to be too low but auto-correction is not enabled.".format(key)
                    result = 43.1
            else:
                msg = "{} - No retuning opportunities detected for Low SAT diagnostic.".format(key)
                result = 40.0
            diagnostic_msg.update({key: result})
            _log.info(msg)

        _log.info(common.table_log_format(self.timestamp_array[-1], (SA_TEMP_RCX1 + DX + ": " + str(diagnostic_msg))))
        self.publish_results(self.timestamp_array[-1], SA_TEMP_RCX1 + DX, diagnostic_msg)

    def high_sat(self, avg_sat_stpt):
        """
        Diagnostic to identify and correct high supply-air temperature
        (correction by modifying SAT set point).
        :param avg_sat_stpt:
        :return:
        """
        avg_zones_rht = mean(self.percent_rht)*100.0
        thresholds = zip(self.percent_dmpr_thr.items(), self.percent_rht_thr.items())
        diagnostic_msg = {}

        for (key, percent_dmpr_thr), (key2, percent_rht_thr) in thresholds:
            avg_zone_dmpr_data = mean(self.percent_dmpr[key]) * 100.0
            if avg_zone_dmpr_data > percent_dmpr_thr and avg_zones_rht < percent_rht_thr:
                if avg_sat_stpt is None:
                    # Create diagnostic message for fault
                    # when supply-air temperature set point
                    # is not available.
                    msg = "{} - The SAT too high but SAT set point data is not available.".format(key)
                    result = 54.1
                elif self.auto_correct_flag and self.auto_correct_flag == key:
                    aircx_sat_stpt = avg_sat_stpt - self.sat_retuning
                    # Create diagnostic message for fault condition
                    # with auto-correction
                    if aircx_sat_stpt >= self.min_sat_stpt:
                        self.send_autocorrect_command(self.sat_stpt_cname, aircx_sat_stpt)
                        sat_stpt = "%s" % float("%.2g" % aircx_sat_stpt)
                        msg = "{} - SAT too high. SAT set point decreased to: {}F".format(key, sat_stpt)
                        result = 51.1
                    else:
                        # Create diagnostic message for fault condition
                        # where the maximum SAT has been reached
                        self.send_autocorrect_command(self.sat_stpt_cname, self.min_sat_stpt)
                        sat_stpt = "%s" % float("%.2g" % self.min_sat_stpt)
                        msg = "{} - SAT too high. Auto-correcting to min SAT set point {}F".format(key, sat_stpt)
                        result = 52.1
                else:
                    # Create diagnostic message for fault condition
                    # without auto-correction
                    msg = "{} - The SAT too high but auto-correction is not enabled.".format(key)
                    result = 53.1
            else:
                msg = "{} - No problem detected for High SAT diagnostic.".format(key)
                result = 50.0
            diagnostic_msg.update({key: result})
            _log.info(msg)

        _log.info(common.table_log_format(self.timestamp_array[-1], (SA_TEMP_RCX2 + DX + ": " + str(diagnostic_msg))))
        self.publish_results(self.timestamp_array[-1], SA_TEMP_RCX2 + DX, diagnostic_msg)

