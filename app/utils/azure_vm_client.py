import os
import paramiko
import logging
from typing import Tuple, Optional
from io import StringIO

logger = logging.getLogger(__name__)

class AzureVMClient:
    """
    Simple SSH client for Azure VM management.
    
    Environment Variables Required:
    - AZURE_VM_IP: VM IP address or hostname
    - AZURE_VM_USER: SSH username
    - AZURE_VM_PASSWORD: SSH password
    """
    
    def __init__(self):
        self.host = os.getenv("AZURE_VM_IP")
        self.username = os.getenv("AZURE_VM_USER")
        self.password = os.getenv("AZURE_VM_PASSWORD")
        self.port = int(os.getenv("AZURE_VM_PORT", "22"))
        
        if not all([self.host, self.username, self.password]):
            missing = []
            if not self.host: missing.append("AZURE_VM_IP")
            if not self.username: missing.append("AZURE_VM_USER")
            if not self.password: missing.append("AZURE_VM_PASSWORD")
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Execute a command on the Azure VM via SSH.
        
        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds (default: 30)
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        ssh = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            logger.info(f"Connecting to Azure VM {self.host}...")
            ssh.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
                banner_timeout=10
            )
            
            logger.info(f"Executing command: {command[:100]}...")
            stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
            
            stdout_text = stdout.read().decode('utf-8')
            stderr_text = stderr.read().decode('utf-8')
            exit_status = stdout.channel.recv_exit_status()
            
            success = exit_status == 0
            
            if success:
                logger.info(f"Command completed successfully (exit code: {exit_status})")
            else:
                logger.warning(f"Command failed with exit code: {exit_status}")
            
            return success, stdout_text, stderr_text
            
        except paramiko.AuthenticationException as e:
            logger.error(f"Authentication failed: {e}")
            return False, "", f"Authentication failed: {str(e)}"
        except paramiko.SSHException as e:
            logger.error(f"SSH error: {e}")
            return False, "", f"SSH error: {str(e)}"
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return False, "", f"Error: {str(e)}"
        finally:
            if ssh:
                ssh.close()
    
    def check_gpu_status(self) -> Tuple[bool, str, str]:
        """
        Check GPU status using nvidia-smi.
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        return self.execute_command("nvidia-smi")
    
    def check_disk_usage(self) -> Tuple[bool, str, str]:
        """
        Check disk usage.
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        return self.execute_command("df -h")
    
    def list_training_jobs(self, directory: str = "~") -> Tuple[bool, str, str]:
        """
        List running Python processes (potential training jobs).
        
        Args:
            directory: Directory to check (default: home directory)
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        command = "ps aux | grep python | grep -v grep"
        return self.execute_command(command)
    
    def check_system_resources(self) -> Tuple[bool, str, str]:
        """
        Check system resources (CPU, memory, disk).
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        command = """
        echo '=== CPU INFO ===' && \
        top -bn1 | head -5 && \
        echo '' && \
        echo '=== MEMORY INFO ===' && \
        free -h && \
        echo '' && \
        echo '=== DISK USAGE ===' && \
        df -h && \
        echo '' && \
        echo '=== GPU INFO ===' && \
        nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv 2>/dev/null || echo 'No GPU available'
        """
        return self.execute_command(command.strip(), timeout=60)
    
    def start_training_job(self, script_path: str, args: str = "") -> Tuple[bool, str, str]:
        """
        Start a training job in the background.
        
        Args:
            script_path: Path to the training script
            args: Additional arguments for the script
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        command = f"nohup python {script_path} {args} > training.log 2>&1 &"
        return self.execute_command(command)
    
    def tail_log(self, log_file: str = "training.log", lines: int = 50) -> Tuple[bool, str, str]:
        """
        Tail a log file.
        
        Args:
            log_file: Path to the log file
            lines: Number of lines to tail (default: 50)
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        command = f"tail -n {lines} {log_file}"
        return self.execute_command(command)
    
    def upload_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        """
        Upload a file to the Azure VM using SFTP.
        
        Args:
            local_path: Local file path
            remote_path: Remote file path
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        ssh = None
        sftp = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            logger.info(f"Connecting to Azure VM {self.host} for file upload...")
            ssh.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            
            sftp = ssh.open_sftp()
            logger.info(f"Uploading {local_path} to {remote_path}...")
            sftp.put(local_path, remote_path)
            
            logger.info(f"File uploaded successfully")
            return True, f"File uploaded successfully to {remote_path}"
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return False, f"Upload failed: {str(e)}"
        finally:
            if sftp:
                sftp.close()
            if ssh:
                ssh.close()
    
    def download_file(self, remote_path: str, local_path: str) -> Tuple[bool, str]:
        """
        Download a file from the Azure VM using SFTP.
        
        Args:
            remote_path: Remote file path
            local_path: Local file path
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        ssh = None
        sftp = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            logger.info(f"Connecting to Azure VM {self.host} for file download...")
            ssh.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            
            sftp = ssh.open_sftp()
            logger.info(f"Downloading {remote_path} to {local_path}...")
            sftp.get(remote_path, local_path)
            
            logger.info(f"File downloaded successfully")
            return True, f"File downloaded successfully to {local_path}"
            
        except Exception as e:
            logger.error(f"File download failed: {e}")
            return False, f"Download failed: {str(e)}"
        finally:
            if sftp:
                sftp.close()
            if ssh:
                ssh.close()


def get_vm_client() -> Optional[AzureVMClient]:
    """
    Get Azure VM client instance.
    
    Returns:
        AzureVMClient instance or None if credentials not configured
    """
    try:
        return AzureVMClient()
    except ValueError as e:
        logger.warning(f"Azure VM client not available: {e}")
        return None
