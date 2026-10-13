using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;

namespace QSparkLauncher
{
    // =========================================================================
    // 1. Windows JobObject 操作系统级进程树托管
    // =========================================================================
    public static class JobObject
    {
        [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
        private static extern IntPtr CreateJobObject(IntPtr lpJobAttributes, string lpName);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool SetInformationJobObject(IntPtr hJob, int JobObjectInfoClass, IntPtr lpJobObjectInfo, uint cbJobObjectInfoLength);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool AssignProcessToJobObject(IntPtr hJob, IntPtr hProcess);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool CloseHandle(IntPtr hObject);

        private const int JobObjectExtendedLimitInformation = 9;
        private const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000;

        [StructLayout(LayoutKind.Sequential)]
        private struct IO_COUNTERS
        {
            public ulong ReadOperationCount;
            public ulong WriteOperationCount;
            public ulong OtherOperationCount;
            public ulong ReadTransferCount;
            public ulong WriteTransferCount;
            public ulong OtherTransferCount;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct JOBOBJECT_BASIC_LIMIT_INFORMATION
        {
            public long PerProcessUserTimeLimit;
            public long PerJobUserTimeLimit;
            public uint LimitFlags;
            public UIntPtr MinimumWorkingSetSize;
            public UIntPtr MaximumWorkingSetSize;
            public uint ActiveProcessLimit;
            public UIntPtr Affinity;
            public uint PriorityClass;
            public uint SchedulingClass;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
        {
            public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
            public IO_COUNTERS IoInfo;
            public UIntPtr ProcessMemoryLimit;
            public UIntPtr JobMemoryLimit;
            public UIntPtr PeakProcessMemoryLimit;
            public UIntPtr PeakJobMemoryLimit;
        }

        private static IntPtr _jobHandle = IntPtr.Zero;

        public static void Initialize()
        {
            if (_jobHandle != IntPtr.Zero) return;
            _jobHandle = CreateJobObject(IntPtr.Zero, null);
            if (_jobHandle == IntPtr.Zero) return;

            JOBOBJECT_EXTENDED_LIMIT_INFORMATION info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;

            int length = Marshal.SizeOf(typeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION));
            IntPtr pInfo = Marshal.AllocHGlobal(length);
            try
            {
                Marshal.StructureToPtr(info, pInfo, false);
                SetInformationJobObject(_jobHandle, JobObjectExtendedLimitInformation, pInfo, (uint)length);
            }
            finally
            {
                Marshal.FreeHGlobal(pInfo);
            }
        }

        public static void AssignProcess(IntPtr hProcess)
        {
            if (_jobHandle != IntPtr.Zero && hProcess != IntPtr.Zero)
            {
                AssignProcessToJobObject(_jobHandle, hProcess);
            }
        }

        public static void Close()
        {
            if (_jobHandle != IntPtr.Zero)
            {
                CloseHandle(_jobHandle);
                _jobHandle = IntPtr.Zero;
            }
        }
    }

    // =========================================================================
    // 2. Q-Spark 核心守护进程与系统托盘管理
    // =========================================================================
    class Program
    {
        [DllImport("user32.dll")]
        private static extern bool IsIconic(IntPtr hWnd);

        [DllImport("user32.dll")]
        private static extern bool IsWindow(IntPtr hWnd);

        [DllImport("user32.dll")]
        private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);

        private const int SW_HIDE = 0;
        private const int SW_SHOW = 5;
        private const int SW_RESTORE = 9;

        private static Process _serverProcess = null;
        private static Process _edgeProcess = null;
        private static IntPtr _edgeHWnd = IntPtr.Zero;

        private static List<string> _logs = new List<string>();
        private static object _logLock = new object();
        private static bool _isRunning = false;
        private static HttpListener _listener = null;
        private static string _appDir = "";

        private static NotifyIcon _notifyIcon = null;
        private static System.Windows.Forms.Timer _minimizeWatcher = null;
        private static bool _isWindowHidden = false;
        private static bool _balloonShown = false;
        private static bool _isExiting = false;
        private static bool _windowLoaded = false;
        private static SynchronizationContext _uiContext = null;

        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                _uiContext = SynchronizationContext.Current ?? new WindowsFormsSynchronizationContext();

                _appDir = AppDomain.CurrentDomain.BaseDirectory;
                JobObject.Initialize();

                // 1. 杀死旧残留进程并清理端口
                KillResiduals();

                // 2. 静默拉起 Python 后台服务
                StartPythonService();

                // 3. 启动本地 40187 守护与静态 UI 桥接服务
                StartDaemonServer();

                // 4. 初始化系统托盘图标
                InitNotifyIcon();

                // 5. 以原生 App 模式拉起精美暗色 Shell 视窗
                LaunchAppWindow();

                // 6. 运行消息循环 (托盘与窗口最小化监控)
                Application.Run();

                // 7. 退出完全收尾
                if (_edgeProcess != null && !_edgeProcess.HasExited)
                {
                    try { _edgeProcess.Kill(); } catch { }
                }
                StopPythonService();
                JobObject.Close();
            }
            catch (Exception ex)
            {
                try
                {
                    File.WriteAllText(Path.Combine(_appDir, "crash.log"), ex.ToString());
                }
                catch { }
            }
        }

        private static void InitNotifyIcon()
        {
            string icoPath = Path.Combine(_appDir, "app.ico");
            _notifyIcon = new NotifyIcon();
            _notifyIcon.Text = "Q-Spark Studio 服务监控";

            if (File.Exists(icoPath))
            {
                try { _notifyIcon.Icon = new Icon(icoPath); } catch { }
            }

            ContextMenuStrip menu = new ContextMenuStrip();
            menu.Items.Add("显示监控窗口", null, (s, e) => RestoreAppWindow());
            menu.Items.Add("打开 Web 界面", null, (s, e) => Process.Start("http://127.0.0.1:40188/"));
            menu.Items.Add("释放显存", null, (s, e) => {
                ThreadPool.QueueUserWorkItem(state => {
                    try {
                        HttpWebRequest req = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:40188/api/vram/flush");
                        req.Method = "POST";
                        using (req.GetResponse()) { }
                    } catch { }
                });
            });
            menu.Items.Add(new ToolStripSeparator());
            menu.Items.Add("退出程序", null, (s, e) => {
                _isExiting = true;
                if (_edgeProcess != null && !_edgeProcess.HasExited)
                {
                    try { _edgeProcess.Kill(); } catch { }
                }
                if (_notifyIcon != null)
                {
                    _notifyIcon.Visible = false;
                    _notifyIcon.Dispose();
                }
                Application.Exit();
            });

            _notifyIcon.ContextMenuStrip = menu;
            _notifyIcon.Visible = true;
            _notifyIcon.DoubleClick += (s, e) => RestoreAppWindow();
        }

        private static void RestoreAppWindow()
        {
            if (_edgeHWnd != IntPtr.Zero && IsWindow(_edgeHWnd))
            {
                _isWindowHidden = false;
                ShowWindow(_edgeHWnd, SW_RESTORE);
                ShowWindow(_edgeHWnd, SW_SHOW);
                SetForegroundWindow(_edgeHWnd);
            }
            else
            {
                _edgeHWnd = IntPtr.Zero;
                LaunchAppWindow();
            }
        }

        private static void HideAppWindow()
        {
            if (_edgeHWnd != IntPtr.Zero && IsWindow(_edgeHWnd))
            {
                _isWindowHidden = true;
                ShowWindow(_edgeHWnd, SW_HIDE);
                if (!_balloonShown)
                {
                    _balloonShown = true;
                    try
                    {
                        _notifyIcon.ShowBalloonTip(1500, "Q-Spark Studio", "已最小化至系统托盘，双击托盘图标即可唤出窗口", ToolTipIcon.Info);
                    }
                    catch { }
                }
            }
        }

        private static void KillResiduals()
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo("taskkill", "/F /IM sd-server.exe /IM sd-cli.exe /T");
                psi.CreateNoWindow = true;
                psi.UseShellExecute = false;
                using (Process p = Process.Start(psi)) { if (p != null) p.WaitForExit(600); }
            }
            catch { }

            FreePort(40188);
            FreePort(40187);
        }

        private static void FreePort(int port)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo("cmd.exe", "/c netstat -ano | findstr :" + port + " | findstr LISTENING");
                psi.CreateNoWindow = true;
                psi.UseShellExecute = false;
                psi.RedirectStandardOutput = true;
                using (Process p = Process.Start(psi))
                {
                    string outStr = p.StandardOutput.ReadToEnd();
                    p.WaitForExit(600);
                    if (!string.IsNullOrEmpty(outStr))
                    {
                        string[] parts = outStr.Trim().Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                        if (parts.Length > 0)
                        {
                            int pid;
                            if (int.TryParse(parts[parts.Length - 1], out pid) && pid > 0)
                            {
                                ProcessStartInfo killPsi = new ProcessStartInfo("taskkill", "/F /PID " + pid + " /T");
                                killPsi.CreateNoWindow = true;
                                killPsi.UseShellExecute = false;
                                using (Process kp = Process.Start(killPsi)) { kp.WaitForExit(500); }
                            }
                        }
                    }
                }
            }
            catch { }
        }

        private static string ResolvePythonExe()
        {
            string localPy = Path.Combine(_appDir, "python_embeded", "python.exe");
            if (File.Exists(localPy)) return localPy;
            return "python.exe";
        }

        private static void StartPythonService()
        {
            if (_serverProcess != null && !_serverProcess.HasExited) return;

            string pyExe = ResolvePythonExe();
            string appPy = Path.Combine(_appDir, "app.py");

            AppendLog("[Supervisor] 正在拉起 Python 服务: " + pyExe + " app.py ...");

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = pyExe;
            psi.Arguments = "-u -s \"" + appPy + "\"";
            psi.WorkingDirectory = _appDir;
            psi.CreateNoWindow = true;
            psi.UseShellExecute = false;
            psi.RedirectStandardOutput = true;
            psi.RedirectStandardError = true;
            psi.StandardOutputEncoding = Encoding.UTF8;
            psi.StandardErrorEncoding = Encoding.UTF8;

            psi.EnvironmentVariables["NO_BROWSER"] = "1";

            try
            {
                _serverProcess = new Process();
                _serverProcess.StartInfo = psi;
                _serverProcess.EnableRaisingEvents = true;

                _serverProcess.OutputDataReceived += (s, e) => {
                    if (!string.IsNullOrEmpty(e.Data) && !e.Data.Contains("/api/metrics"))
                    {
                        AppendLog(e.Data);
                    }
                };
                _serverProcess.ErrorDataReceived += (s, e) => {
                    if (!string.IsNullOrEmpty(e.Data) && !e.Data.Contains("/api/metrics"))
                    {
                        AppendLog("[STDERR] " + e.Data);
                    }
                };
                _serverProcess.Exited += (s, e) => {
                    _isRunning = false;
                    AppendLog("[Supervisor] 服务进程已退出。");
                };

                _serverProcess.Start();
                JobObject.AssignProcess(_serverProcess.Handle);

                _serverProcess.BeginOutputReadLine();
                _serverProcess.BeginErrorReadLine();

                _isRunning = true;
                AppendLog("[Supervisor] 后台服务启动成功 (PID: " + _serverProcess.Id + ")");
            }
            catch (Exception ex)
            {
                AppendLog("[Supervisor Error] 启动失败: " + ex.Message);
                _isRunning = false;
            }
        }

        private static void StopPythonService()
        {
            if (_serverProcess == null || _serverProcess.HasExited)
            {
                _isRunning = false;
                return;
            }

            AppendLog("[Supervisor] 正在停止服务并释放显存...");
            try
            {
                HttpWebRequest req = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:40188/api/vram/flush");
                req.Method = "POST";
                req.Timeout = 1500;
                using (req.GetResponse()) { }
            }
            catch { }

            try
            {
                if (!_serverProcess.HasExited)
                {
                    ProcessStartInfo psi = new ProcessStartInfo("taskkill", "/F /PID " + _serverProcess.Id + " /T");
                    psi.CreateNoWindow = true;
                    psi.UseShellExecute = false;
                    using (Process p = Process.Start(psi)) { if (p != null) p.WaitForExit(1000); }
                }
            }
            catch { }

            KillResiduals();
            _isRunning = false;
            AppendLog("[Supervisor] 服务已彻底停止。");
        }

        private static void AppendLog(string line)
        {
            lock (_logLock)
            {
                if (_logs.Count > 1000)
                {
                    _logs.RemoveRange(0, 200);
                }
                _logs.Add("[" + DateTime.Now.ToString("HH:mm:ss") + "] " + line);
            }
        }

        private static void StartDaemonServer()
        {
            try
            {
                _listener = new HttpListener();
                _listener.Prefixes.Add("http://127.0.0.1:40187/");
                _listener.Start();

                Thread t = new Thread(() => {
                    while (_listener != null && _listener.IsListening)
                    {
                        try
                        {
                            var ctx = _listener.GetContext();
                            ThreadPool.QueueUserWorkItem((state) => HandleRequest((HttpListenerContext)state), ctx);
                        }
                        catch { break; }
                    }
                });
                t.IsBackground = true;
                t.Start();
            }
            catch (Exception ex)
            {
                AppendLog("[Daemon Error] 40187 监听失败: " + ex.Message);
            }
        }

        private static void HandleRequest(HttpListenerContext ctx)
        {
            try
            {
                string path = ctx.Request.Url.AbsolutePath;
                ctx.Response.Headers.Add("Access-Control-Allow-Origin", "*");
                ctx.Response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
                ctx.Response.Headers.Add("Access-Control-Allow-Headers", "*");
                ctx.Response.Headers.Add("Cache-Control", "no-cache, no-store, must-revalidate");

                if (ctx.Request.HttpMethod == "OPTIONS")
                {
                    ctx.Response.StatusCode = 200;
                    ctx.Response.Close();
                    return;
                }

                if (path == "/" || path == "/index.html")
                {
                    string htmlPath = Path.Combine(_appDir, "static", "shell.html");
                    byte[] data;
                    if (File.Exists(htmlPath))
                    {
                        data = File.ReadAllBytes(htmlPath);
                    }
                    else
                    {
                        data = Encoding.UTF8.GetBytes("<h1>Q-Spark Shell HTML not found</h1>");
                    }
                    ctx.Response.ContentType = "text/html; charset=utf-8";
                    ctx.Response.ContentLength64 = data.Length;
                    ctx.Response.OutputStream.Write(data, 0, data.Length);
                    ctx.Response.Close();
                }
                else if (path == "/app.ico" || path == "/favicon.ico")
                {
                    string icoPath = Path.Combine(_appDir, "app.ico");
                    if (File.Exists(icoPath))
                    {
                        byte[] data = File.ReadAllBytes(icoPath);
                        ctx.Response.ContentType = "image/x-icon";
                        ctx.Response.ContentLength64 = data.Length;
                        ctx.Response.OutputStream.Write(data, 0, data.Length);
                    }
                    else
                    {
                        ctx.Response.StatusCode = 404;
                    }
                    ctx.Response.Close();
                }
                else if (path == "/api/status")
                {
                    int pid = (_serverProcess != null && !_serverProcess.HasExited) ? _serverProcess.Id : 0;
                    string json = "{\"running\":" + (_isRunning ? "true" : "false") + ",\"pid\":" + pid + "}";
                    byte[] res = Encoding.UTF8.GetBytes(json);
                    ctx.Response.ContentType = "application/json";
                    ctx.Response.OutputStream.Write(res, 0, res.Length);
                    ctx.Response.Close();
                }
                else if (path == "/api/minimize")
                {
                    HideAppWindow();
                    byte[] res = Encoding.UTF8.GetBytes("{\"minimized\":true}");
                    ctx.Response.ContentType = "application/json";
                    ctx.Response.OutputStream.Write(res, 0, res.Length);
                    ctx.Response.Close();
                }
                else if (path == "/api/quit" || path == "/api/exit")
                {
                    byte[] res = Encoding.UTF8.GetBytes("{\"quitting\":true}");
                    ctx.Response.ContentType = "application/json";
                    ctx.Response.OutputStream.Write(res, 0, res.Length);
                    ctx.Response.Close();

                    ThreadPool.QueueUserWorkItem(state => {
                        Thread.Sleep(150);
                        _isExiting = true;
                        if (_edgeProcess != null && !_edgeProcess.HasExited)
                        {
                            try { _edgeProcess.Kill(); } catch { }
                        }
                        if (_notifyIcon != null)
                        {
                            _notifyIcon.Visible = false;
                            _notifyIcon.Dispose();
                        }
                        Application.Exit();
                    });
                }
                else if (path == "/api/power")
                {
                    if (_isRunning) StopPythonService();
                    else StartPythonService();

                    int pid = (_serverProcess != null && !_serverProcess.HasExited) ? _serverProcess.Id : 0;
                    byte[] res = Encoding.UTF8.GetBytes("{\"running\":" + (_isRunning ? "true" : "false") + ",\"pid\":" + pid + "}");
                    ctx.Response.ContentType = "application/json";
                    ctx.Response.OutputStream.Write(res, 0, res.Length);
                    ctx.Response.Close();
                }
                else if (path == "/api/restart")
                {
                    StopPythonService();
                    Thread.Sleep(600);
                    StartPythonService();

                    int pid = (_serverProcess != null && !_serverProcess.HasExited) ? _serverProcess.Id : 0;
                    byte[] res = Encoding.UTF8.GetBytes("{\"success\":true,\"pid\":" + pid + "}");
                    ctx.Response.ContentType = "application/json";
                    ctx.Response.OutputStream.Write(res, 0, res.Length);
                    ctx.Response.Close();
                }
                else if (path == "/api/logs")
                {
                    string allLogs;
                    lock (_logLock)
                    {
                        allLogs = string.Join(Environment.NewLine, _logs.ToArray());
                    }
                    byte[] res = Encoding.UTF8.GetBytes(allLogs);
                    ctx.Response.ContentType = "text/plain; charset=utf-8";
                    ctx.Response.OutputStream.Write(res, 0, res.Length);
                    ctx.Response.Close();
                }
                else
                {
                    ctx.Response.StatusCode = 404;
                    ctx.Response.Close();
                }
            }
            catch { }
        }

        private static void LaunchAppWindow()
        {
            if (_edgeProcess != null && !_edgeProcess.HasExited && _edgeHWnd != IntPtr.Zero && IsWindow(_edgeHWnd))
            {
                RestoreAppWindow();
                return;
            }

            string edge = @"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe";
            if (!File.Exists(edge)) edge = @"C:\Program Files\Microsoft\Edge\Application\msedge.exe";

            if (File.Exists(edge))
            {
                string profileDir = Path.Combine(_appDir, ".data", "edge_profile");
                if (!Directory.Exists(profileDir))
                {
                    try { Directory.CreateDirectory(profileDir); } catch { }
                }

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = edge;
                psi.Arguments = "--app=\"http://127.0.0.1:40187/\" --user-data-dir=\"" + profileDir.TrimEnd('\\') + "\" --window-size=980,620";
                try
                {
                    _windowLoaded = false;
                    _isWindowHidden = false;
                    _edgeProcess = Process.Start(psi);
                    if (_edgeProcess != null)
                    {
                        try { JobObject.AssignProcess(_edgeProcess.Handle); } catch { }
                        _edgeProcess.EnableRaisingEvents = true;
                        _edgeProcess.Exited += (s, e) => {
                            if (_isExiting || !_windowLoaded) return;

                            if (_uiContext != null)
                            {
                                _uiContext.Post(state => OnAppWindowClosed(), null);
                            }
                            else
                            {
                                OnAppWindowClosed();
                            }
                        };

                        if (_minimizeWatcher == null)
                        {
                            _minimizeWatcher = new System.Windows.Forms.Timer();
                            _minimizeWatcher.Interval = 150;
                            _minimizeWatcher.Tick += (s, e) => {
                                if (_edgeHWnd == IntPtr.Zero || !IsWindow(_edgeHWnd))
                                {
                                    if (_edgeProcess != null && !_edgeProcess.HasExited)
                                    {
                                        _edgeProcess.Refresh();
                                        IntPtr hWnd = _edgeProcess.MainWindowHandle;
                                        if (hWnd != IntPtr.Zero)
                                        {
                                            _edgeHWnd = hWnd;
                                            _windowLoaded = true;
                                        }
                                    }
                                }
                                else
                                {
                                    if (!_isWindowHidden && IsIconic(_edgeHWnd))
                                    {
                                        HideAppWindow();
                                    }
                                }
                            };
                            _minimizeWatcher.Start();
                        }
                    }
                }
                catch (Exception ex)
                {
                    AppendLog("[App Error] Edge App Mode 启动异常: " + ex.Message);
                }
            }
            else
            {
                Process.Start("http://127.0.0.1:40187/");
            }
        }

        private static void OnAppWindowClosed()
        {
            if (_isExiting) return;

            _edgeHWnd = IntPtr.Zero;
            _edgeProcess = null;
            _windowLoaded = false;
            _isWindowHidden = true;

            if (!_balloonShown)
            {
                _balloonShown = true;
                try
                {
                    _notifyIcon.ShowBalloonTip(1500, "Q-Spark Studio", "窗口已关闭，服务在后台继续运行，双击托盘可重新打开", ToolTipIcon.Info);
                }
                catch { }
            }
        }
    }
}
