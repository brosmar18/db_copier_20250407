import subprocess
import threading
import time
import os

def is_admin():
    """Check if the application is running with administrator privileges"""
    try:
        # This will fail with an AccessDenied error if not admin
        return os.getuid() == 0
    except AttributeError:
        # For Windows systems
        try:
            return subprocess.run(["net", "session"], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL).returncode == 0
        except Exception:
            return False

def get_all_services():
    """
    Fetch all services from the system.
    Returns a list of dictionaries with service details.
    """
    try:
        # Use PowerShell to get services with detailed information
        cmd = ["powershell", "-Command", 
               "Get-Service | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Csv -NoTypeInformation"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Failed to retrieve services: {result.stderr}")
        
        # Process output
        services = []
        lines = result.stdout.strip().split('\n')
        
        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue
            
            # Split CSV line, handle quotes
            parts = [p.strip('"') for p in line.split(',')]
            if len(parts) >= 4:
                service = {
                    'name': parts[0],
                    'display_name': parts[1],
                    'status': parts[2],
                    'start_type': parts[3]
                }
                services.append(service)
        
        return services
    except Exception as e:
        print(f"Error retrieving services: {e}")
        return []

def extract_powershell_error(stderr):
    """Extract a more user-friendly error message from PowerShell stderr output"""
    if not stderr:
        return "Unknown error occurred"
    
    # Try to extract the main error message
    lines = stderr.strip().split('\n')
    
    # Look for lines that contain error descriptions
    for line in lines:
        if ":" in line and not line.startswith("-") and not line.startswith("At "):
            parts = line.split(":", 1)
            if len(parts) >= 2 and parts[1].strip():
                return parts[1].strip()
    
    # If no specific error found, return the first line
    return lines[0] if lines else "Unknown error occurred"

def start_service(service_name, callback=None):
    """
    Start a Windows service.
    
    Args:
        service_name: Name of the service to start
        callback: Optional function to call with result
    
    Returns:
        (success, message) tuple
    """
    def _execute():
        try:
            # Check if admin and prepare warning message
            admin_warning = "" if is_admin() else "\n\nNote: Some services require administrator privileges to control."
            
            # Use PowerShell to start the service
            cmd = ["powershell", "-Command", f"Start-Service -Name '{service_name}' -ErrorAction Stop; Write-Output 'Service started successfully'"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                success = True
                message = "Service started successfully"
            else:
                success = False
                error_msg = extract_powershell_error(result.stderr)
                message = f"Failed to start service: {error_msg}{admin_warning}"
                
            if callback:
                callback(success, message)
            return success, message
            
        except Exception as e:
            message = f"Error starting service: {str(e)}"
            if callback:
                callback(False, message)
            return False, message
    
    # Run in a thread to avoid blocking the UI
    thread = threading.Thread(target=_execute)
    thread.daemon = True
    thread.start()
    return thread

def stop_service(service_name, callback=None):
    """
    Stop a Windows service with force parameter to ensure more reliable stopping.
    
    Args:
        service_name: Name of the service to stop
        callback: Optional function to call with result
    
    Returns:
        (success, message) tuple
    """
    def _execute():
        try:
            # Check if admin and prepare warning message
            admin_warning = "" if is_admin() else "\n\nNote: Some services require administrator privileges to control."
            
            # Use PowerShell to stop the service with -Force parameter
            cmd = ["powershell", "-Command", f"Stop-Service -Name '{service_name}' -Force -ErrorAction Stop; Write-Output 'Service stopped successfully'"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                success = True
                message = "Service stopped successfully"
            else:
                success = False
                error_msg = extract_powershell_error(result.stderr)
                message = f"Failed to stop service: {error_msg}{admin_warning}"
                
            if callback:
                callback(success, message)
            return success, message
            
        except Exception as e:
            message = f"Error stopping service: {str(e)}"
            if callback:
                callback(False, message)
            return False, message
    
    # Run in a thread to avoid blocking the UI
    thread = threading.Thread(target=_execute)
    thread.daemon = True
    thread.start()
    return thread

def restart_service(service_name, callback=None):
    """
    Restart a Windows service.
    
    Args:
        service_name: Name of the service to restart
        callback: Optional function to call with result
    
    Returns:
        (success, message) tuple
    """
    def _execute():
        try:
            # Check if admin and prepare warning message
            admin_warning = "" if is_admin() else "\n\nNote: Some services require administrator privileges to control."
            
            # Use PowerShell to restart the service
            cmd = ["powershell", "-Command", f"Restart-Service -Name '{service_name}' -Force -ErrorAction Stop; Write-Output 'Service restarted successfully'"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                success = True
                message = "Service restarted successfully"
            else:
                success = False
                error_msg = extract_powershell_error(result.stderr)
                message = f"Failed to restart service: {error_msg}{admin_warning}"
                
            if callback:
                callback(success, message)
            return success, message
            
        except Exception as e:
            message = f"Error restarting service: {str(e)}"
            if callback:
                callback(False, message)
            return False, message
    
    # Run in a thread to avoid blocking the UI
    thread = threading.Thread(target=_execute)
    thread.daemon = True
    thread.start()
    return thread

def get_service_status(service_name):
    """
    Get the current status of a service.
    
    Args:
        service_name: Name of the service
    
    Returns:
        Status string or None if error
    """
    try:
        cmd = ["powershell", "-Command", f"(Get-Service -Name '{service_name}').Status"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
            
    except Exception as e:
        print(f"Error getting service status: {e}")
        return None