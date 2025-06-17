import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
from waitress import serve
from app import create_app  # Make sure this path is correct for your project

class MRIReserveService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MRIRESERVE"
    _svc_display_name_ = "MRI Reservation Service"
    _svc_description_ = "A Flask-based web service for MRI reservation management."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.app = create_app()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.main()

    def main(self):
        serve(self.app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(MRIReserveService)
