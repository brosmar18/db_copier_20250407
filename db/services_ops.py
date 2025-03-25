import subprocess
import threading
import time

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
            # Use PowerShell to start the service
            cmd = ["powershell", "-Command", f"Start-Service -Name '{service_name}' -ErrorAction Stop; Write-Output 'Service started successfully'"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                success = True
                message = "Service started successfully"
            else:
                success = False
                message = result.stderr.strip() or "Failed to start service"
                
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
    Stop a Windows service.
    
    Args:
        service_name: Name of the service to stop
        callback: Optional function to call with result
    
    Returns:
        (success, message) tuple
    """
    def _execute():
        try:
            # Use PowerShell to stop the service
            cmd = ["powershell", "-Command", f"Stop-Service -Name '{service_name}' -ErrorAction Stop; Write-Output 'Service stopped successfully'"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                success = True
                message = "Service stopped successfully"
            else:
                success = False
                message = result.stderr.strip() or "Failed to stop service"
                
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
            # Use PowerShell to restart the service
            cmd = ["powershell", "-Command", f"Restart-Service -Name '{service_name}' -ErrorAction Stop; Write-Output 'Service restarted successfully'"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                success = True
                message = "Service restarted successfully"
            else:
                success = False
                message = result.stderr.strip() or "Failed to restart service"
                
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