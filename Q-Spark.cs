using System;
using System.Diagnostics;
using System.IO;

namespace QSparkLauncher
{
    class Program
    {
        static void Main(string[] args)
        {
            string appDir = AppDomain.CurrentDomain.BaseDirectory;
            string startBat = Path.Combine(appDir, "start.bat");

            ProcessStartInfo psi = new ProcessStartInfo();
            if (File.Exists(startBat))
            {
                psi.FileName = "cmd.exe";
                psi.Arguments = "/c \"\"" + startBat + "\"\"";
                psi.WorkingDirectory = appDir;
                psi.UseShellExecute = true;
            }
            else
            {
                string pyExe = Path.Combine(appDir, "python_embeded", "python.exe");
                if (!File.Exists(pyExe)) pyExe = "python";
                string appPy = Path.Combine(appDir, "app.py");

                psi.FileName = pyExe;
                psi.Arguments = "\"" + appPy + "\"";
                psi.WorkingDirectory = appDir;
                psi.UseShellExecute = true;
            }

            try
            {
                Process.Start(psi);
            }
            catch (Exception ex)
            {
                Console.WriteLine("启动失败: " + ex.Message);
            }
        }
    }
}
