import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.core.auth import verify_api_key
from app.utils.azure_vm_client import get_vm_client

logger = logging.getLogger(__name__)
router = APIRouter()


class CommandRequest(BaseModel):
    command: str = Field(..., description="Shell command to execute")
    timeout: int = Field(30, description="Command timeout in seconds", ge=1, le=300)


class TrainingJobRequest(BaseModel):
    script_path: str = Field(..., description="Path to the training script on the VM")
    args: str = Field("", description="Additional arguments for the script")


class LogRequest(BaseModel):
    log_file: str = Field("training.log", description="Path to the log file")
    lines: int = Field(50, description="Number of lines to tail", ge=1, le=1000)


class FileTransferRequest(BaseModel):
    local_path: str = Field(..., description="Local file path")
    remote_path: str = Field(..., description="Remote file path")


@router.post("/azure-vm/execute")
async def execute_command(request: CommandRequest, api_key: str = Depends(verify_api_key)):
    """
    Execute a shell command on the Azure VM.
    
    Args:
        request: Command execution request
        
    Returns:
        Command execution result with stdout and stderr
    """
    vm_client = get_vm_client()
    if not vm_client:
        raise HTTPException(
            status_code=503, 
            detail="Azure VM client not configured. Set AZURE_VM_IP, AZURE_VM_USER, and AZURE_VM_PASSWORD environment variables."
        )
    
    try:
        success, stdout, stderr = vm_client.execute_command(request.command, request.timeout)
        
        return {
            "success": success,
            "command": request.command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": 0 if success else 1
        }
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Command execution failed: {str(e)}")


@router.get("/azure-vm/gpu-status")
async def get_gpu_status(api_key: str = Depends(verify_api_key)):
    """
    Check GPU status on the Azure VM using nvidia-smi.
    
    Returns:
        GPU status information
    """
    vm_client = get_vm_client()
    if not vm_client:
        raise HTTPException(
            status_code=503, 
            detail="Azure VM client not configured. Set AZURE_VM_IP, AZURE_VM_USER, and AZURE_VM_PASSWORD environment variables."
        )
    
    try:
        success, stdout, stderr = vm_client.check_gpu_status()
        
        return {
            "success": success,
            "gpu_info": stdout if success else None,
            "error": stderr if not success else None
        }
    except Exception as e:
        logger.error(f"GPU status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"GPU status check failed: {str(e)}")


@router.get("/azure-vm/system-resources")
async def get_system_resources(api_key: str = Depends(verify_api_key)):
    """
    Check system resources (CPU, memory, disk, GPU) on the Azure VM.
    
    Returns:
        System resource information
    """
    vm_client = get_vm_client()
    if not vm_client:
        raise HTTPException(
            status_code=503, 
            detail="Azure VM client not configured. Set AZURE_VM_IP, AZURE_VM_USER, and AZURE_VM_PASSWORD environment variables."
        )
    
    try:
        success, stdout, stderr = vm_client.check_system_resources()
        
        return {
            "success": success,
            "resources": stdout if success else None,
            "error": stderr if not success else None
        }
    except Exception as e:
        logger.error(f"System resource check failed: {e}")
        raise HTTPException(status_code=500, detail=f"System resource check failed: {str(e)}")


@router.get("/azure-vm/training-jobs")
async def list_training_jobs(api_key: str = Depends(verify_api_key)):
    """
    List running training jobs (Python processes) on the Azure VM.
    
    Returns:
        List of running Python processes
    """
    vm_client = get_vm_client()
    if not vm_client:
        raise HTTPException(
            status_code=503, 
            detail="Azure VM client not configured. Set AZURE_VM_IP, AZURE_VM_USER, and AZURE_VM_PASSWORD environment variables."
        )
    
    try:
        success, stdout, stderr = vm_client.list_training_jobs()
        
        return {
            "success": success,
            "jobs": stdout if success else None,
            "error": stderr if not success else None
        }
    except Exception as e:
        logger.error(f"Training jobs listing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training jobs listing failed: {str(e)}")


@router.post("/azure-vm/start-training")
async def start_training_job(request: TrainingJobRequest, api_key: str = Depends(verify_api_key)):
    """
    Start a training job on the Azure VM.
    
    Args:
        request: Training job start request
        
    Returns:
        Training job start result
    """
    vm_client = get_vm_client()
    if not vm_client:
        raise HTTPException(
            status_code=503, 
            detail="Azure VM client not configured. Set AZURE_VM_IP, AZURE_VM_USER, and AZURE_VM_PASSWORD environment variables."
        )
    
    try:
        success, stdout, stderr = vm_client.start_training_job(request.script_path, request.args)
        
        return {
            "success": success,
            "message": "Training job started successfully" if success else "Failed to start training job",
            "script_path": request.script_path,
            "args": request.args,
            "output": stdout,
            "error": stderr if not success else None
        }
    except Exception as e:
        logger.error(f"Training job start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training job start failed: {str(e)}")


@router.post("/azure-vm/tail-log")
async def tail_log(request: LogRequest, api_key: str = Depends(verify_api_key)):
    """
    Tail a log file on the Azure VM.
    
    Args:
        request: Log tail request
        
    Returns:
        Log file contents
    """
    vm_client = get_vm_client()
    if not vm_client:
        raise HTTPException(
            status_code=503, 
            detail="Azure VM client not configured. Set AZURE_VM_IP, AZURE_VM_USER, and AZURE_VM_PASSWORD environment variables."
        )
    
    try:
        success, stdout, stderr = vm_client.tail_log(request.log_file, request.lines)
        
        return {
            "success": success,
            "log_file": request.log_file,
            "lines": request.lines,
            "content": stdout if success else None,
            "error": stderr if not success else None
        }
    except Exception as e:
        logger.error(f"Log tail failed: {e}")
        raise HTTPException(status_code=500, detail=f"Log tail failed: {str(e)}")


@router.get("/azure-vm/disk-usage")
async def get_disk_usage(api_key: str = Depends(verify_api_key)):
    """
    Check disk usage on the Azure VM.
    
    Returns:
        Disk usage information
    """
    vm_client = get_vm_client()
    if not vm_client:
        raise HTTPException(
            status_code=503, 
            detail="Azure VM client not configured. Set AZURE_VM_IP, AZURE_VM_USER, and AZURE_VM_PASSWORD environment variables."
        )
    
    try:
        success, stdout, stderr = vm_client.check_disk_usage()
        
        return {
            "success": success,
            "disk_usage": stdout if success else None,
            "error": stderr if not success else None
        }
    except Exception as e:
        logger.error(f"Disk usage check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Disk usage check failed: {str(e)}")


@router.get("/azure-vm/health")
async def check_vm_health():
    """
    Check if Azure VM client is configured and accessible.
    
    Returns:
        VM client health status
    """
    vm_client = get_vm_client()
    
    if not vm_client:
        return {
            "configured": False,
            "healthy": False,
            "message": "Azure VM client not configured. Set AZURE_VM_IP, AZURE_VM_USER, and AZURE_VM_PASSWORD."
        }
    
    try:
        success, stdout, stderr = vm_client.execute_command("echo 'health_check'", timeout=5)
        
        return {
            "configured": True,
            "healthy": success,
            "message": "Azure VM accessible" if success else f"Connection failed: {stderr}",
            "host": vm_client.host,
            "username": vm_client.username
        }
    except Exception as e:
        return {
            "configured": True,
            "healthy": False,
            "message": f"Health check failed: {str(e)}",
            "host": vm_client.host,
            "username": vm_client.username
        }
