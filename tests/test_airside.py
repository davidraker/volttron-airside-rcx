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

import unittest

from collections import defaultdict
from datetime import datetime, timedelta as td

from airside.diagnostics import common
from airside.diagnostics.sat_aircx import SupplyTempAIRCx
from airside.diagnostics.schedule_reset_aircx import SchedResetAIRCx
from airside.diagnostics.stcpr_aircx import DuctStaticAIRCx


def publish_results(timestamp, diagnostic_topic, diagnostic_result):
    return timestamp, diagnostic_topic, diagnostic_result

def send_autocorrect_command(point, value):
    return point, value


class TestDiagnosticsSupplyTempAIRCx(unittest.TestCase):
    """
    Contains all the tests for SupplyTempAIRCx Diagnostic
    """

    def test_temp_sensor_dx_creation(self):
        """test the creation of temp sensor diagnostic class"""
        diagnostic = SupplyTempAIRCx()
        if isinstance(diagnostic, SupplyTempAIRCx):
            assert True
        else:
            assert False

    def test_temp_sensor_dx_set_class_values(self):
        """test the creation of temp sensor diagnostic class"""
        diagnostic = SupplyTempAIRCx()
        data_window = td(minutes=1)
        diagnostic.set_class_values({}, 1, data_window, False, {}, 4.0, {}, {}, {}, 2, 3, {}, 5, "test")
        diagnostic.setup_platform_interfaces(publish_results, send_autocorrect_command)
        assert diagnostic.data_window == td(minutes=1)
        assert diagnostic.no_req_data == 1
        assert diagnostic.sat_stpt_cname == "test"
        assert diagnostic.max_sat_stpt == 5
        assert diagnostic.min_sat_stpt == 2
        assert diagnostic.sat_retuning == 3

    def test_temp_sensor_dx_reinitialize(self):
        """test the creation of temp sensor diagnostic class"""
        diagnostic = SupplyTempAIRCx()
        diagnostic.table_key = "test"
        diagnostic.timestamp_array = "test"
        diagnostic.sat_stpt_array = "test"
        diagnostic.sat_array = "test"
        diagnostic.rht_array = "test"
        diagnostic.percent_rht = "test"
        diagnostic.percent_dmpr ="test"
        diagnostic.reinitialize()
        assert diagnostic.table_key is None
        assert diagnostic.timestamp_array == []
        assert diagnostic.sat_stpt_array == []
        assert diagnostic.sat_array == []
        assert diagnostic.rht_array == []
        assert diagnostic.percent_rht == []
        assert diagnostic.percent_dmpr == defaultdict(list)

    def test_temp_sensor_dx_sat_aircx(self):
        """test the sat_aircx method"""
        diagnostic = SupplyTempAIRCx()
        data_window = td(minutes=1)
        cur_time = datetime.fromtimestamp(1036)
        diagnostic.set_class_values({}, 1, data_window, False, {}, 4.0, {}, {}, {}, 2, 3, {}, 5, "test")
        diagnostic.setup_platform_interfaces(publish_results, send_autocorrect_command)
        diagnostic.sat_aircx(cur_time, [4.0], [4.0], [4.0], [4.0])
        assert diagnostic.sat_array[0] == 4.0
        assert diagnostic.rht_array[0] == 4.0
        assert diagnostic.timestamp_array[0] == cur_time

    def test_temp_sensor_dx_low_sat(self):
        """test the clow_sat method"""
        diagnostic = SupplyTempAIRCx()
        data_window = td(minutes=1)
        cur_time = datetime.fromtimestamp(1036)
        diagnostic.set_class_values({}, 1, data_window, False, {}, 4.0, {}, {}, {}, 2, 3, {}, 5, "test")
        diagnostic.setup_platform_interfaces(publish_results, send_autocorrect_command)
        diagnostic.sat_aircx(cur_time, [4.0], [4.0], [4.0], [4.0])
        diagnostic.low_sat(4.0)
        assert diagnostic.sat_array[0] == 4.0
        assert diagnostic.rht_array[0] == 4.0
        assert diagnostic.timestamp_array[0] == cur_time

    def test_temp_sensor_dx_high_sat(self):
        """test the high sat method"""
        diagnostic = SupplyTempAIRCx()
        data_window = td(minutes=1)
        cur_time = datetime.fromtimestamp(1036)
        diagnostic.set_class_values({}, 1, data_window, False, {}, 4.0, {}, {}, {}, 2, 3, {}, 5, "test")
        diagnostic.setup_platform_interfaces(publish_results, send_autocorrect_command)
        diagnostic.sat_aircx(cur_time, [4.0], [4.0], [4.0], [4.0])
        diagnostic.high_sat(4.0)
        assert diagnostic.sat_array[0] == 4.0
        assert diagnostic.rht_array[0] == 4.0
        assert diagnostic.timestamp_array[0] == cur_time

class TestDiagnosticsDuctStaticAIRCx(unittest.TestCase):
    """
    Contains all the tests for DuctStaticAIRCx Diagnostic
    """

    def test_duct_static_dx_creation(self):
        """test the creation of duct static diagnostic class"""
        diagnostic = DuctStaticAIRCx()
        if isinstance(diagnostic, DuctStaticAIRCx):
            assert True
        else:
            assert False

    def test_duct_static_dx_set_class_values(self):
        """test the creation of duct static diagnostic class"""
        diagnostic = DuctStaticAIRCx()
        data_window = td(minutes=1)
        diagnostic.set_class_values({}, 1, data_window, False, {}, 4.0, 4.0, {}, {}, {}, 3, "test")
        assert diagnostic.data_window == td(minutes=1)
        assert diagnostic.no_req_data == 1
        assert diagnostic.stcpr_stpt_cname == "test"
        assert diagnostic.max_stcpr_stpt == 4.0
        assert diagnostic.min_stcpr_stpt == 3.0
        assert diagnostic.stcpr_retuning == 4.0

    def test_duct_static_dx_reinitialize(self):
        """test the creation of duct static diagnostic class"""
        diagnostic = DuctStaticAIRCx()
        diagnostic.table_key = "test"
        diagnostic.timestamp_array = "test"
        diagnostic.stcpr_stpt_array = "test"
        diagnostic.stcpr_array = "test"
        diagnostic.ls_dmpr_low_avg = "test"
        diagnostic.ls_dmpr_high_avg = "test"
        diagnostic.hs_dmpr_high_avg ="test"
        diagnostic.low_sf_condition = "test"
        diagnostic.high_sf_condition = "test"
        diagnostic.reinitialize()
        assert diagnostic.table_key is None
        assert diagnostic.timestamp_array == []
        assert diagnostic.stcpr_stpt_array == []
        assert diagnostic.stcpr_array == []
        assert diagnostic.ls_dmpr_low_avg == []
        assert diagnostic.ls_dmpr_high_avg == []
        assert diagnostic.hs_dmpr_high_avg == []
        assert diagnostic.low_sf_condition == []
        assert diagnostic.high_sf_condition == []

    def test_duct_static_dx_stcpr_aircx(self):
        """test the sat_aircx method"""
        diagnostic = DuctStaticAIRCx()
        data_window = td(minutes=1)
        cur_time = datetime.fromtimestamp(1036)
        diagnostic.set_class_values({}, 1, data_window, False, {}, 4.0, 4.0, {}, {}, {}, 3, "test")
        diagnostic.stcpr_aircx(cur_time, [4.0], [4.0], [4.0], 1, 1)
        assert diagnostic.low_sf_condition[0] == 1
        assert diagnostic.high_sf_condition[0] == 1
        assert diagnostic.timestamp_array[0] == cur_time

    def test_duct_static_dx_low_sat(self):
        """test the clow_sat method"""
        diagnostic = DuctStaticAIRCx()
        data_window = td(minutes=1)
        cur_time = datetime.fromtimestamp(1036)
        diagnostic.set_class_values({}, 1, data_window, False, {}, 4.0, 4.0, {}, {}, {}, 3, "test")
        diagnostic.setup_platform_interfaces(publish_results, send_autocorrect_command)
        diagnostic.stcpr_aircx(cur_time, [4.0], [4.0], [4.0], 1, 1)
        diagnostic.low_stcpr_aircx(4.0)
        assert diagnostic.timestamp_array[0] == cur_time
        assert diagnostic.command_tuple == {}

    def test_duct_static_dx_high_sat(self):
        """test the high sat method"""
        diagnostic = DuctStaticAIRCx()
        data_window = td(minutes=1)
        cur_time = datetime.fromtimestamp(1036)
        diagnostic.set_class_values({}, 1, data_window, False, {}, 4.0, 4.0, {}, {}, {}, 3, "test")
        diagnostic.setup_platform_interfaces(publish_results, send_autocorrect_command)
        diagnostic.stcpr_aircx(cur_time, [4.0], [4.0], [4.0], 1, 1)
        diagnostic.high_stcpr_aircx(4.0)
        assert diagnostic.timestamp_array[0] == cur_time
        assert diagnostic.command_tuple == {}

class TestDiagnosticsScheduleResetAIRCx(unittest.TestCase):
    """
    Contains all the tests for SchedResetAIRCx Diagnostic
    """

    def test_schedule_reset_dx_creation(self):
        """test the creation of schedule reset diagnostic class"""
        diagnostic = SchedResetAIRCx()
        if isinstance(diagnostic, SchedResetAIRCx):
            assert True
        else:
            assert False

    def test_duct_static_dx_set_class_values(self):
        """test the creation of schedule reset diagnostic class"""
        diagnostic = SchedResetAIRCx()
        diagnostic.set_class_values({1.0}, {2.0}, {}, {}, {}, {}, {}, {}, {}, 1, {3.0}, {4.0})
        assert diagnostic.no_req_data == 1
        assert diagnostic.unocc_time_thr == {1.0}
        assert diagnostic.unocc_stcpr_thr == {2.0}
        assert diagnostic.stcpr_reset_thr == {3.0}
        assert diagnostic.sat_reset_thr == {4.0}
        assert diagnostic.monday_sch == []

    def test_temp_sensor_dx_reinitialize(self):
        """test the creation of schedule reset reinitialize"""
        diagnostic = SchedResetAIRCx()
        diagnostic.stcpr_array = "test"
        diagnostic.fan_status_array = "test"
        diagnostic.schedule_time_array = "test"
        diagnostic.reinitialize_sched()
        assert diagnostic.stcpr_array == []
        assert diagnostic.fan_status_array == []
        assert diagnostic.schedule_time_array == []

    def test_temp_sensor_dx_schedule_reset(self):
        """test the creation of schedule reset """
        diagnostic = SchedResetAIRCx()
        diagnostic.set_class_values({1.0}, {2.0}, ["0:00", "23:59"], ["0:00", "23:59"], ["0:00", "23:59"], ["0:00", "23:59"], ["0:00", "23:59"], ["0:00", "23:59"], ["0:00", "23:59"], 1, {3.0}, {4.0})
        cur_time = datetime.fromtimestamp(1036)
        diagnostic.schedule_reset_aircx(cur_time, [4.0], [5.0], [6.0], 1)
        assert diagnostic.timestamp_array[0] == cur_time
        assert diagnostic.fan_status_array == []
        assert diagnostic.schedule_time_array == []


class TestDiagnosticsCommon(unittest.TestCase):
    """
    Contains all the tests for common Diagnostic
    """

    def test_common_check_date(self):
        """test the common check date"""
        cur_time = datetime.fromtimestamp(1036)
        timestamp_array = []
        response = common.check_date(cur_time, timestamp_array)
        assert response is False

    def test_common_check_run_status(self):
        """test the common check run status"""
        cur_time = datetime.fromtimestamp(1036)
        timestamp_array = []
        response = common.check_run_status(timestamp_array, cur_time, 1, None, "hourly", None)
        assert response is False

    def test_common_setpoint_control_check(self):
        """test the common check setpoint control"""
        thr_dict = {
            "low": 1 * 1.5,
            "normal": 1,
            "high": 1 * 0.5
        }
        avg, dx_string, dx_msg = common.setpoint_control_check([1, 2, 3], [1, 2, 3], thr_dict, "Duct Static Pressure Set Point Control Loop Dx")
        assert avg == 2.0
        assert dx_string == "Duct Static Pressure Set Point Control Loop Dx/diagnostic message"
        print(dx_msg)
        assert dx_msg == {'low': 0.0, 'normal': 0.0, 'high': 0.0}
