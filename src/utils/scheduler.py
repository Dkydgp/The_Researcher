import time
import subprocess
import sys
import datetime
import os

# ANSI Colors for Professional Output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    print(f"{Colors.HEADER}================================================={Colors.ENDC}")
    print(f"{Colors.BOLD}   NIFTY-5 AI AUTOMATION SCHEDULER               {Colors.ENDC}")
    print(f"{Colors.HEADER}================================================={Colors.ENDC}")
    print(f"{Colors.CYAN}• Target Time:{Colors.ENDC} 19:00 (7:00 PM) Daily")
    print(f"{Colors.CYAN}• Action:{Colors.ENDC}      Full Data Pipeline (News -> Prices -> AI)")
    print(f"{Colors.CYAN}• Status:{Colors.ENDC}      {Colors.GREEN}ACTIVE{Colors.ENDC}")
    print(f"{Colors.HEADER}================================================={Colors.ENDC}\n")

def run_pipeline():
    print(f"\n{Colors.WARNING}[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚀 Triggering Scheduled Pipeline...{Colors.ENDC}")
    
    start_time = time.time()
    try:
        # Run the pipeline script
        result = subprocess.run(
            [sys.executable, "run_pipeline.py"],
            capture_output=True,
            text=True
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}[SUCCESS] Pipeline completed in {duration:.1f}s{Colors.ENDC}")
            print(f"{Colors.BLUE}Next run scheduled for tomorrow at 19:00.{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}[ERROR] Pipeline failed!{Colors.ENDC}")
            print(result.stderr)
            
    except Exception as e:
        print(f"{Colors.FAIL}[EXCEPTION] {str(e)}{Colors.ENDC}")

def get_seconds_until_target(target_hour, target_minute):
    now = datetime.datetime.now()
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    if now >= target:
        # If target time passed today, schedule for tomorrow
        target += datetime.timedelta(days=1)
        
    return (target - now).total_seconds()

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    
    TARGET_HOUR = 19
    TARGET_MINUTE = 00
    
    while True:
        seconds_wait = get_seconds_until_target(TARGET_HOUR, TARGET_MINUTE)
        next_run = datetime.datetime.now() + datetime.timedelta(seconds=seconds_wait)
        
        print(f"\r{Colors.CYAN}[WAITING]{Colors.ENDC} Next run at {next_run.strftime('%Y-%m-%d %H:%M:%S')} (in {int(seconds_wait//3600)}h {int((seconds_wait%3600)//60)}m)   ", end="", flush=True)
        
        # Sleep in short bursts to allow for cleaner exit or status updates if needed
        # But for efficiency, we can just sleep most of the way
        if seconds_wait > 60:
            time.sleep(60)
        else:
            time.sleep(seconds_wait)
            run_pipeline()
            time.sleep(1) # Prevent double triggering

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Scheduler stopped by user.{Colors.ENDC}")
