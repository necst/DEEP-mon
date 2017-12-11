from __future__ import print_function
from bpf_collector import BpfCollector
from proc_topology import ProcTopology
from sample_controller import SampleController
from process_table import ProcTable
from rapl import rapl
import argparse
import time

class MonitorMain():

    def __init__(self, parse_args):
        self.topology = ProcTopology()
        self.collector = BpfCollector(self.topology, False)
        self.sample_controller = SampleController(self.topology.get_hyperthread_count())

        self.process_table = ProcTable()

        self.collector.start_capture(self.sample_controller.get_timeslice())
        self.rapl_monitor = rapl.RaplMonitor(self.topology)
        self.output_format = parse_args

    def get_sample(self):
        sample = self.collector.get_new_sample(self.sample_controller, self.rapl_monitor)
        # add stuff to cumulative process table
        self.process_table.add_process_from_sample(sample)

        # Now, extract containers!
        container_list = self.process_table.get_container_dictionary()

        return [sample, container_list, self.process_table.get_proc_table()]


    def monitor_loop(self):
        time_to_sleep = self.sample_controller.get_sleep_time()

        while True:

            time.sleep(time_to_sleep)
            start_time = time.time()

            sample_array = self.get_sample()
            sample = sample_array[0]
            container_list = sample_array[1]

            if output_format == "json":
                for key, value in container_list.iteritems():
                    print(value.to_json())
                print
                print(sample.get_log_json())
            else:
                for key, value in container_list.iteritems():
                    print(value)
                print
                print(sample.get_log_line())

            time_to_sleep = self.sample_controller.get_sleep_time() \
                - (time.time() - start_time)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--format", type=str,
                        help="Output format", required=False)
    args = parser.parse_args()
    output_format = args.format
    monitor = MonitorMain(output_format)
    monitor.monitor_loop()