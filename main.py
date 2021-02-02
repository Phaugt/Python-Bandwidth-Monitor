import threading, time, psutil, os, sys, rumps



class BandWidthMon(rumps.App):
    """rumps - statusbar module"""

    @rumps.timer(0.25)
    def updateTitle(self, _):
        thread = threading.Thread(target=net_usage)

        thread.start()

        self.title = net_usage()


def net_usage():
    """netusage monitor calculates usage of the network card"""

    while True:
        net_stat = psutil.net_io_counters()
        net_in_1 = net_stat.bytes_recv
        net_out_1 = net_stat.bytes_sent

        time.sleep(0.65)

        net_stat = psutil.net_io_counters()
        net_in_2 = net_stat.bytes_recv
        net_out_2 = net_stat.bytes_sent

        net_in = round((net_in_2 - net_in_1) / 1024 / 1024, 2)
        net_out = round((net_out_2 - net_out_1) / 1024 / 1024, 2)
        return f"IN: {net_in} MB/s, OUT: {net_out} MB/s"


if __name__ == "__main__":
    BandWidthMon("Loading...").run()