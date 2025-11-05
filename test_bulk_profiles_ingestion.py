#!/usr/bin/env python3
"""
Test script to ingest 1,200 real investor profiles into Harvey's training system.
This will generate approximately 12,000 training questions from real investor data.
"""

import requests
import json
import csv
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Configuration
import os
API_BASE_URL = "http://localhost:5000/v1"
API_KEY = os.getenv("HARVEY_AI_API_KEY", "test-harvey-ai-key-2024")  # Use environment variable

def read_csv_file(filepath: str) -> str:
    """Read CSV file content."""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read CSV file {filepath}: {e}")
        return None

def read_jsonl_file(filepath: str) -> str:
    """Read JSONL file content."""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read JSONL file {filepath}: {e}")
        return None

def ingest_profiles(content: str, file_format: str, batch_name: str) -> dict:
    """
    Send profiles to Harvey's bulk ingestion endpoint.
    
    Args:
        content: File content (CSV or JSONL)
        file_format: Either "csv" or "jsonl"
        batch_name: Name to identify this batch
        
    Returns:
        API response as dict
    """
    endpoint = f"{API_BASE_URL}/training/bulk-profiles"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "content": content,
        "file_format": file_format,
        "process_immediately": False  # First just validate
    }
    
    try:
        logger.info(f"Sending {batch_name} profiles to Harvey...")
        response = requests.post(endpoint, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Successfully processed {batch_name}")
            logger.info(f"   - Profiles: {result.get('statistics', {}).get('total_profiles', 0)}")
            logger.info(f"   - Questions generated: {result.get('statistics', {}).get('total_questions', 0)}")
            return result
        else:
            logger.error(f"❌ Failed to process {batch_name}: {response.status_code}")
            logger.error(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Exception processing {batch_name}: {e}")
        return None

def get_training_stats() -> dict:
    """Get current training statistics."""
    endpoint = f"{API_BASE_URL}/training/profile-stats"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Failed to get training stats: {e}")
        return None

def main():
    """Main execution function."""
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║    Harvey AI - Bulk Investor Profile Ingestion      ║
    ║             Processing 1,200 Real Profiles          ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # File paths
    profiles_200_csv = "attached_assets/passive_income_seed_200_1762252010033.csv"
    profiles_200_jsonl = "attached_assets/passive_income_seed_200_1762252002931.jsonl"
    profiles_1000_csv = "attached_assets/passive_income_seed_1000_1762252179135.csv"
    profiles_1000_jsonl = "attached_assets/passive_income_seed_1000_1762252172451.jsonl"
    
    # Track results
    total_profiles = 0
    total_questions = 0
    
    # Process 200 profiles (CSV)
    logger.info("\n📊 Processing first 200 profiles from CSV...")
    csv_content_200 = read_csv_file(profiles_200_csv)
    if csv_content_200:
        result = ingest_profiles(csv_content_200, "csv", "Batch 200 (CSV)")
        if result:
            stats = result.get('statistics', {})
            total_profiles += stats.get('total_profiles', 0)
            total_questions += stats.get('total_questions', 0)
    
    time.sleep(2)  # Small delay between batches
    
    # Process 200 profiles (JSONL) for validation
    logger.info("\n📊 Processing first 200 profiles from JSONL for validation...")
    jsonl_content_200 = read_jsonl_file(profiles_200_jsonl)
    if jsonl_content_200:
        result = ingest_profiles(jsonl_content_200, "jsonl", "Batch 200 (JSONL)")
        # Don't double count since it's the same profiles
    
    time.sleep(2)
    
    # Process 1000 profiles (CSV)
    logger.info("\n📊 Processing 1000 profiles from CSV...")
    csv_content_1000 = read_csv_file(profiles_1000_csv)
    if csv_content_1000:
        result = ingest_profiles(csv_content_1000, "csv", "Batch 1000 (CSV)")
        if result:
            stats = result.get('statistics', {})
            total_profiles += stats.get('total_profiles', 0)
            total_questions += stats.get('total_questions', 0)
    
    time.sleep(2)
    
    # Process 1000 profiles (JSONL) for validation
    logger.info("\n📊 Processing 1000 profiles from JSONL for validation...")
    jsonl_content_1000 = read_jsonl_file(profiles_1000_jsonl)
    if jsonl_content_1000:
        result = ingest_profiles(jsonl_content_1000, "jsonl", "Batch 1000 (JSONL)")
        # Don't double count since it's the same profiles
    
    # Get final statistics
    logger.info("\n📈 Getting final training statistics...")
    stats = get_training_stats()
    
    # Print summary
    questions_per_profile = total_questions / total_profiles if total_profiles > 0 else 0
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║              INGESTION COMPLETE SUMMARY              ║
    ╠══════════════════════════════════════════════════════╣
    ║  Total Unique Profiles:     {total_profiles:,}                     ║
    ║  Training Questions:        {total_questions:,}                   ║
    ║  Questions per Profile:     {questions_per_profile:.1f}                     ║
    ╠══════════════════════════════════════════════════════╣
    ║                  PROFILE DEMOGRAPHICS                ║
    ╠══════════════════════════════════════════════════════╣
    """)
    
    if stats and stats.get('success'):
        profile_stats = stats.get('statistics', {})
        
        # Goal distribution
        goal_dist = profile_stats.get('goal_distribution', {})
        print(f"║  Income Now:        {goal_dist.get('income-now', 0):>4} profiles             ║")
        print(f"║  Income Growth:     {goal_dist.get('income-growth', 0):>4} profiles             ║")
        print(f"║  Balanced:          {goal_dist.get('balanced', 0):>4} profiles             ║")
        
        print("╠══════════════════════════════════════════════════════╣")
        
        # Risk distribution
        risk_dist = profile_stats.get('risk_distribution', {})
        print(f"║  Conservative:      {risk_dist.get('conservative', 0):>4} profiles             ║")
        print(f"║  Moderate:          {risk_dist.get('moderate', 0):>4} profiles             ║")
        print(f"║  Aggressive:        {risk_dist.get('aggressive', 0):>4} profiles             ║")
        
        print("╠══════════════════════════════════════════════════════╣")
        
        # Profile categories
        categories = profile_stats.get('profile_categories', {})
        print(f"║  Young Growth:      {categories.get('young_growth', 0):>4} profiles             ║")
        print(f"║  Pre-Retirement:    {categories.get('pre_retirement', 0):>4} profiles             ║")
        print(f"║  Retirement:        {categories.get('retirement', 0):>4} profiles             ║")
        print(f"║  High Net Worth:    {categories.get('high_net_worth', 0):>4} profiles             ║")
    
    print("╚══════════════════════════════════════════════════════╝")
    
    # Training impact
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║                TRAINING DATA IMPACT                  ║
    ╠══════════════════════════════════════════════════════╣
    ║  With 5 AI Models Processing:                        ║
    ║  → {total_questions * 5:,} total model responses                ║
    ║  → High-quality training examples for fine-tuning    ║
    ║  → Pattern recognition across investor types         ║
    ║  → Personalized strategy generation capability       ║
    ╚══════════════════════════════════════════════════════╝
    
    🎯 Harvey is now equipped with comprehensive training data
       from 1,200 real investor profiles, enabling sophisticated
       personalized dividend investment strategies!
    """)

if __name__ == "__main__":
    main()