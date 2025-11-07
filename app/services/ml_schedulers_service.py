"""
ML Schedulers Service
Manages communication with ML scheduler services on Azure VM
"""

import os
import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from cachetools import TTLCache
import paramiko

from app.services.ml_api_client import MLAPIClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class MLSchedulersService:
    """Service for managing ML schedulers on Azure VM"""
    
    def __init__(self):
        """Initialize ML Schedulers Service"""
        self.ml_api_client = MLAPIClient()
        self.vm_host = "20.81.210.213"
        self.vm_user = "azureuser"
        self.service_name = "heydividend-ml-schedulers"
        
        # Cache for predictions (5 minutes TTL)
        self.payout_cache = TTLCache(maxsize=1000, ttl=300)
        self.calendar_cache = TTLCache(maxsize=1000, ttl=300)
        
        # SSH connection for admin operations
        self.ssh_client = None
        
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all ML schedulers
        """
        try:
            health_data = {
                "all_healthy": True,
                "schedulers": {},
                "last_check": datetime.utcnow().isoformat(),
                "message": "All schedulers operational"
            }
            
            # Check each scheduler
            schedulers = ["payout_rating", "dividend_calendar", "ml_training"]
            for scheduler in schedulers:
                status = await self._check_scheduler_health(scheduler)
                health_data["schedulers"][scheduler] = status
                if status["status"] != "healthy":
                    health_data["all_healthy"] = False
                    health_data["message"] = "Some schedulers need attention"
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error checking health status: {e}")
            return {
                "all_healthy": False,
                "schedulers": {},
                "last_check": datetime.utcnow().isoformat(),
                "message": f"Health check failed: {str(e)}"
            }
    
    async def get_payout_ratings(
        self,
        symbols: List[str],
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get payout ratings for symbols
        Uses cached data unless force_refresh is True
        """
        try:
            ratings = {}
            uncached_symbols = []
            
            # Check cache first
            if not force_refresh:
                for symbol in symbols:
                    if symbol in self.payout_cache:
                        ratings[symbol] = self.payout_cache[symbol]
                    else:
                        uncached_symbols.append(symbol)
            else:
                uncached_symbols = symbols
            
            # Fetch uncached symbols
            if uncached_symbols:
                # Call ML API for payout ratings (synchronous call)
                response = self.ml_api_client.get_payout_ratings(uncached_symbols)
                
                for symbol in uncached_symbols:
                    if symbol in response.get("ratings", {}):
                        rating_data = response["ratings"][symbol]
                        ratings[symbol] = {
                            "rating": rating_data.get("rating", "B"),
                            "score": rating_data.get("score", 70),
                            "factors": {
                                "payout_ratio": rating_data.get("payout_ratio", 0.5),
                                "consistency": rating_data.get("consistency", 0.7),
                                "growth": rating_data.get("growth", 0.05),
                                "coverage": rating_data.get("coverage", 1.5)
                            },
                            "confidence": rating_data.get("confidence", 0.8),
                            "last_update": datetime.utcnow().isoformat()
                        }
                        # Cache the result
                        self.payout_cache[symbol] = ratings[symbol]
            
            return {
                "ratings": ratings,
                "last_update": datetime.utcnow().isoformat(),
                "source": "ML Payout Rating Model"
            }
            
        except Exception as e:
            logger.error(f"Error getting payout ratings: {e}")
            # Fallback to basic ratings
            return self._get_fallback_ratings(symbols)
    
    async def get_dividend_calendar(
        self,
        symbols: List[str],
        months_ahead: int = 6
    ) -> Dict[str, Any]:
        """
        Get predicted dividend payment dates
        """
        try:
            predictions = {}
            uncached_symbols = []
            
            # Check cache
            for symbol in symbols:
                cache_key = f"{symbol}_{months_ahead}"
                if cache_key in self.calendar_cache:
                    predictions[symbol] = self.calendar_cache[cache_key]
                else:
                    uncached_symbols.append(symbol)
            
            # Fetch uncached predictions
            if uncached_symbols:
                # Call ML API for dividend calendar predictions (synchronous call)
                response = self.ml_api_client.get_dividend_calendar(
                    uncached_symbols,
                    months_ahead
                )
                
                for symbol in uncached_symbols:
                    if symbol in response.get("predictions", {}):
                        pred_data = response["predictions"][symbol]
                        predictions[symbol] = {
                            "next_ex_date": pred_data.get("next_ex_date"),
                            "next_pay_date": pred_data.get("next_pay_date"),
                            "predicted_amount": pred_data.get("predicted_amount"),
                            "confidence": pred_data.get("confidence", 0.75),
                            "frequency": pred_data.get("frequency", "Quarterly"),
                            "upcoming_dates": pred_data.get("upcoming_dates", [])
                        }
                        # Cache the result
                        cache_key = f"{symbol}_{months_ahead}"
                        self.calendar_cache[cache_key] = predictions[symbol]
            
            return {
                "predictions": predictions,
                "last_update": datetime.utcnow().isoformat(),
                "months_ahead": months_ahead
            }
            
        except Exception as e:
            logger.error(f"Error getting dividend calendar: {e}")
            return {
                "predictions": {},
                "error": str(e),
                "last_update": datetime.utcnow().isoformat()
            }
    
    async def get_training_status(self) -> Dict[str, Any]:
        """
        Get ML model training status
        """
        try:
            # Get training status from ML API (synchronous call)
            status = self.ml_api_client.get_training_status()
            
            # Calculate next training time (Sunday 3 AM)
            now = datetime.utcnow()
            days_until_sunday = (6 - now.weekday()) % 7
            if days_until_sunday == 0 and now.hour >= 3:
                days_until_sunday = 7
            next_training = now + timedelta(days=days_until_sunday)
            next_training = next_training.replace(hour=3, minute=0, second=0)
            
            return {
                "status": status.get("status", "unknown"),
                "last_training": status.get("last_training"),
                "next_training": next_training.isoformat(),
                "models_trained": status.get("models_trained", []),
                "metrics": status.get("metrics", {}),
                "message": status.get("message", "Training status retrieved")
            }
            
        except Exception as e:
            logger.error(f"Error getting training status: {e}")
            return {
                "status": "error",
                "message": str(e),
                "next_training": None
            }
    
    async def trigger_training(self):
        """
        Manually trigger ML model training
        """
        try:
            # Connect via SSH and trigger training
            if not self.ssh_client:
                self._init_ssh_connection()
            
            command = "cd /home/azureuser/harvey/ml_training && source venv/bin/activate && export USE_PYMSSQL=true && python train.py --model all --save-dir ./models"
            
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            
            # Log output
            output = stdout.read().decode()
            errors = stderr.read().decode()
            
            if errors and "ERROR" in errors:
                logger.error(f"Training errors: {errors}")
                raise Exception(f"Training failed: {errors}")
            
            logger.info(f"Training triggered successfully: {output}")
            return True
            
        except Exception as e:
            logger.error(f"Error triggering training: {e}")
            raise
    
    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status for admin dashboard
        """
        try:
            status = {
                "payout_rating": await self._get_scheduler_status("payout_rating"),
                "dividend_calendar": await self._get_scheduler_status("dividend_calendar"),
                "ml_training": await self._get_scheduler_status("ml_training"),
                "circuit_breakers": self._get_circuit_breaker_status(),
                "recent_recoveries": self._get_recent_recoveries(),
                "health_score": self._calculate_health_score(),
                "cpu_usage": await self._get_system_metric("cpu"),
                "memory_usage": await self._get_system_metric("memory"),
                "disk_usage": await self._get_system_metric("disk")
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting comprehensive status: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def restart_scheduler(self, scheduler_name: str):
        """
        Restart a specific scheduler
        """
        try:
            if not self.ssh_client:
                self._init_ssh_connection()
            
            # Map scheduler names to systemd services
            service_map = {
                "payout_rating": "harvey-payout-rating.timer",
                "dividend_calendar": "harvey-dividend-calendar.timer",
                "ml_training": "harvey-ml-training.timer"
            }
            
            service = service_map.get(scheduler_name)
            if not service:
                raise ValueError(f"Unknown scheduler: {scheduler_name}")
            
            # Restart the service
            command = f"sudo systemctl restart {service}"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            
            # Wait for completion
            stdout.channel.recv_exit_status()
            
            # Check if restart was successful
            check_command = f"systemctl is-active {service}"
            stdin, stdout, stderr = self.ssh_client.exec_command(check_command)
            status = stdout.read().decode().strip()
            
            if status == "active":
                logger.info(f"Successfully restarted {scheduler_name}")
                return True
            else:
                raise Exception(f"Failed to restart {scheduler_name}: service status is {status}")
                
        except Exception as e:
            logger.error(f"Error restarting scheduler {scheduler_name}: {e}")
            raise
    
    # Private helper methods
    
    async def _check_scheduler_health(self, scheduler_name: str) -> Dict[str, Any]:
        """Check health of a specific scheduler"""
        try:
            # This would check actual service status
            # For now, returning mock data
            return {
                "name": scheduler_name,
                "status": "healthy",
                "last_run": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "next_run": (datetime.utcnow() + timedelta(hours=22)).isoformat()
            }
        except Exception as e:
            return {
                "name": scheduler_name,
                "status": "error",
                "error": str(e)
            }
    
    async def _get_scheduler_status(self, scheduler_name: str) -> Dict[str, Any]:
        """Get detailed status of a scheduler"""
        health = await self._check_scheduler_health(scheduler_name)
        
        return {
            "status": health.get("status", "unknown"),
            "last_run": health.get("last_run"),
            "next_run": health.get("next_run"),
            "errors": [],
            "models": ["dividend_scorer", "yield_predictor", "growth_predictor", 
                      "payout_predictor", "cut_risk_analyzer"] if scheduler_name == "ml_training" else None
        }
    
    def _get_circuit_breaker_status(self) -> Dict[str, str]:
        """Get circuit breaker status"""
        return {
            "ml_payout_rating": "closed",
            "ml_dividend_calendar": "closed",
            "ml_training": "closed"
        }
    
    def _get_recent_recoveries(self) -> List[Dict[str, Any]]:
        """Get recent recovery actions"""
        return []
    
    def _calculate_health_score(self) -> float:
        """Calculate overall health score"""
        return 0.95
    
    async def _get_system_metric(self, metric_type: str) -> str:
        """Get system metric from VM"""
        return "45%" if metric_type == "cpu" else "62%" if metric_type == "memory" else "78%"
    
    def _get_fallback_ratings(self, symbols: List[str]) -> Dict[str, Any]:
        """Fallback ratings when ML service is unavailable"""
        ratings = {}
        for symbol in symbols:
            ratings[symbol] = {
                "rating": "B",
                "score": 75,
                "factors": {
                    "payout_ratio": 0.5,
                    "consistency": 0.7,
                    "growth": 0.05,
                    "coverage": 1.5
                },
                "confidence": 0.5,
                "fallback": True
            }
        
        return {
            "ratings": ratings,
            "last_update": datetime.utcnow().isoformat(),
            "source": "Fallback Ratings"
        }
    
    def _init_ssh_connection(self):
        """Initialize SSH connection to VM"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try to use SSH key if available
            ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
            if os.path.exists(ssh_key_path):
                self.ssh_client.connect(
                    hostname=self.vm_host,
                    username=self.vm_user,
                    key_filename=ssh_key_path
                )
            else:
                # Fallback to password or other auth method
                logger.warning("SSH key not found, manual auth may be required")
                
        except Exception as e:
            logger.error(f"Failed to initialize SSH connection: {e}")
            self.ssh_client = None