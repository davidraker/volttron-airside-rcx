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

from datetime import timedelta as td

from volttron.utils import setup_logging
from volttron.utils.math_utils import mean

FAN_OFF = -99.3
DUCT_STC_RCX = "Duct Static Pressure Set Point Control Loop Dx"
DUCT_STC_RCX1 = "Low Duct Static Pressure Dx"
DUCT_STC_RCX2 = "High Duct Static Pressure Dx"
DX = "/diagnostic message"
SA_TEMP_RCX = "Supply-air Temperature Set Point Control Loop Dx"
SA_TEMP_RCX1 = "Low Supply-air Temperature Dx"
SA_TEMP_RCX2 = "High Supply-air Temperature Dx"
dx_list = [DUCT_STC_RCX, DUCT_STC_RCX1, DUCT_STC_RCX2, SA_TEMP_RCX, SA_TEMP_RCX1, SA_TEMP_RCX2]
dx_offsets = {SA_TEMP_RCX: 30.0, DUCT_STC_RCX: 0.0}

setup_logging()
_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s   %(levelname)-8s %(message)s",
                    datefmt="%m-%d-%y %H:%M:%S")


def check_date(current_time, timestamp_array):
    """
    Check current timestamp with previous timestamp to verify that there are no large missing data gaps.
    :param current_time:
    :param timestamp_array:
    :return:
    """
    if not timestamp_array:
        return False
    if current_time.date() != timestamp_array[-1].date():
        if (timestamp_array[-1].date() + td(days=1) != current_time.date() or
                (timestamp_array[-1].hour != 23 and current_time.hour == 0)):
            return True
        return False


def check_run_status(timestamp_array, current_time, no_required_data, minimum_diagnostic_time=None,
                     run_schedule="hourly", minimum_point_array=None):
    """
    The diagnostics run at a regular interval (some minimum elapsed amount of time) and have a
    minimum data count requirement (each time series of data must contain some minimum number of points).
    :param timestamp_array:
    :param current_time:
    :param no_required_data:
    :param minimum_diagnostic_time:
    :param run_schedule:
    :param minimum_point_array:
    :return:
    """
    def minimum_data():
        min_data_array = timestamp_array if minimum_point_array is None else minimum_point_array
        if len(min_data_array) < no_required_data:
            return None
        return True

    if minimum_diagnostic_time is not None and timestamp_array:
        sampling_interval = round(((timestamp_array[-1] - timestamp_array[0]) / len(timestamp_array)).total_seconds() / 60)
        sampling_interval = td(minutes=max(sampling_interval, 1))
        required_time = (timestamp_array[-1] - timestamp_array[0]) + sampling_interval

        if required_time >= minimum_diagnostic_time:
            return minimum_data()
        return False

    if run_schedule == "hourly":
        if timestamp_array and timestamp_array[-1].hour != current_time.hour:
            return minimum_data()
    elif run_schedule == "daily":
        if timestamp_array and timestamp_array[-1].date() != current_time.date():
            return minimum_data()
    return False


def setpoint_control_check(set_point_array, point_array, setpoint_deviation_threshold, dx_name):
    """
    Verify that point if tracking with set point - identify potential control or sensor problems.
    :param set_point_array:
    :param point_array:
    :param setpoint_deviation_threshold:
    :param dx_name:
    :return:
    """
    avg_set_point = None
    diagnostic_msg = {}
    for sensitivity, threshold in setpoint_deviation_threshold.items():
        if set_point_array:
            avg_set_point = mean(set_point_array)
            zipper = (set_point_array, point_array)
            set_point_tracking = [abs(x - y) for x, y in zip(*zipper)]
            set_point_error = mean(set_point_tracking)/avg_set_point*100.

            if set_point_error > threshold:
                # color_code = 'red'
                msg = '{} - {}: point deviating significantly from set point.'.format(sensitivity, dx_name)
                result = 1.1 + dx_offsets[dx_name]
            else:
                # color_code = 'green'
                msg = " {} - No problem detected for {} set".format(sensitivity, dx_name)
                result = 0.0 + dx_offsets[dx_name]
        else:
            # color_code = 'grey'
            msg = "{} - {} set point data is not available.".format(sensitivity, dx_name)
            result = 2.2 + dx_offsets[dx_name]
        _log.info(msg)
        diagnostic_msg.update({sensitivity: result})
    diagnostic_string = dx_name + DX
    return avg_set_point, diagnostic_string, diagnostic_msg


def pre_conditions(results_pub, message, dx_li, cur_time):
    """
    Check for persistence of failure to meet pre-conditions for diagnostics.
    :param results_pub:
    :param message:
    :param dx_li:
    :param cur_time:
    :return:
    """
    dx_msg = {"low": message, "normal": message, "high": message}
    for diagnostic in dx_li:
        _log.info(table_log_format(cur_time, (diagnostic + DX + ':' + str(dx_msg))))
        results_pub(cur_time, (diagnostic + DX), dx_msg)


def table_log_format(timestamp, data):
    """ Return a formatted string for use in the log"""
    return str(timestamp) + '->[' + str(data) + ']'


