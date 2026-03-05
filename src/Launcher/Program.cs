using System.Diagnostics;

var dir = AppContext.BaseDirectory;
var script = Path.Combine(dir, "heic_converter.py");
var quotedArgs = string.Join(" ", Environment.GetCommandLineArgs()[1..]
                               .Select(a => $"\"{a}\""));
Process.Start(new ProcessStartInfo("python", $"\"{script}\" {quotedArgs}")
    { UseShellExecute = false })?.WaitForExit();
