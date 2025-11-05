"""
Bulk Profile Ingestion Service
Processes 200 real investor profiles from CSV/JSONL for training Harvey.
"""

import json
import csv
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import pandas as pd
from io import StringIO

logger = logging.getLogger("bulk_profile_ingestion")


class BulkProfileIngestion:
    """
    Processes bulk investor profiles for training Harvey.
    Converts real investor data into comprehensive training questions.
    """
    
    def process_csv_profiles(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Process investor profiles from CSV content.
        
        Args:
            csv_content: CSV string containing investor profiles
            
        Returns:
            List of parsed investor profiles
        """
        profiles = []
        try:
            # Use pandas for robust CSV parsing
            df = pd.read_csv(StringIO(csv_content))
            
            for index, row in df.iterrows():
                profile = {
                    "profile_id": f"real_profile_{index + 1}",
                    "goal": {
                        "primary": row.get("goal.primary", "balanced"),
                        "target_income": row.get("goal.target_income_amount", 50000),
                        "target_date": row.get("goal.target_income_start_date", "2030-01-01")
                    },
                    "demographics": {
                        "age": row.get("kyc.age", 50),
                        "country": row.get("tax.residence_country", "United States"),
                        "state": row.get("tax.residence_state", "")
                    },
                    "risk": {
                        "band": row.get("risk.band", "moderate"),
                        "max_drawdown": row.get("risk.max_drawdown_tolerance", 20),
                        "income_volatility": row.get("risk.income_volatility_tolerance", 10)
                    },
                    "financial": {
                        "net_worth": row.get("finance.net_worth_investable", "$250k-$1m"),
                        "emergency_months": row.get("finance.emergency_fund_months", 6)
                    },
                    "strategy": {
                        "dividend_growth": row.get("strategy.mix_preference.dividend-growth", 40),
                        "high_yield": row.get("strategy.mix_preference.high-yield", 30),
                        "bond_led": row.get("strategy.mix_preference.bond-led", 20),
                        "options": row.get("strategy.mix_preference.options-aided", 10),
                        "target_yield_today": row.get("div.target_yield_today", 4.5),
                        "target_yield_5y": row.get("div.target_yield_in_5y", 5.5),
                        "drip_policy": row.get("div.drip_policy_forward", "DRIP-some")
                    },
                    "constraints": {
                        "exclusions": self._parse_list_field(row.get("constraints.exclusions", "[]")),
                        "brokers": self._parse_list_field(row.get("portfolio.brokers", "[]"))
                    },
                    "tax": {
                        "filing_status": row.get("tax.filing_status", "single"),
                        "marginal_rate": row.get("tax.top_marginal_rate", 24)
                    }
                }
                profiles.append(profile)
                
            logger.info(f"Processed {len(profiles)} profiles from CSV")
            return profiles
            
        except Exception as e:
            logger.error(f"Error processing CSV profiles: {e}")
            return []
    
    def process_jsonl_profiles(self, jsonl_content: str) -> List[Dict[str, Any]]:
        """
        Process investor profiles from JSONL content.
        
        Args:
            jsonl_content: JSONL string with one profile per line
            
        Returns:
            List of parsed investor profiles
        """
        profiles = []
        try:
            lines = jsonl_content.strip().split('\n')
            
            for index, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                data = json.loads(line)
                responses = data.get("responses", {})
                
                profile = {
                    "profile_id": f"real_profile_{index + 1}",
                    "goal": {
                        "primary": responses.get("goal.primary", "balanced"),
                        "target_income": responses.get("goal.target_income_amount", 50000),
                        "target_date": responses.get("goal.target_income_start_date", "2030-01-01")
                    },
                    "demographics": {
                        "age": responses.get("kyc.age", 50),
                        "country": responses.get("tax.residence_country", "United States"),
                        "state": responses.get("tax.residence_state", "")
                    },
                    "risk": {
                        "band": responses.get("risk.band", "moderate"),
                        "max_drawdown": responses.get("risk.max_drawdown_tolerance", 20),
                        "income_volatility": responses.get("risk.income_volatility_tolerance", 10)
                    },
                    "financial": {
                        "net_worth": responses.get("finance.net_worth_investable", "$250k-$1m"),
                        "emergency_months": responses.get("finance.emergency_fund_months", 6)
                    },
                    "strategy": {
                        "dividend_growth": responses.get("strategy.mix_preference", {}).get("dividend-growth", 40),
                        "high_yield": responses.get("strategy.mix_preference", {}).get("high-yield", 30),
                        "bond_led": responses.get("strategy.mix_preference", {}).get("bond-led", 20),
                        "options": responses.get("strategy.mix_preference", {}).get("options-aided", 10),
                        "target_yield_today": responses.get("div.target_yield_today", 4.5),
                        "target_yield_5y": responses.get("div.target_yield_in_5y", 5.5),
                        "drip_policy": responses.get("div.drip_policy_forward", "DRIP-some")
                    },
                    "constraints": {
                        "exclusions": responses.get("constraints.exclusions", []),
                        "brokers": responses.get("portfolio.brokers", [])
                    },
                    "tax": {
                        "filing_status": responses.get("tax.filing_status", "single"),
                        "marginal_rate": responses.get("tax.top_marginal_rate", 24)
                    }
                }
                profiles.append(profile)
                
            logger.info(f"Processed {len(profiles)} profiles from JSONL")
            return profiles
            
        except Exception as e:
            logger.error(f"Error processing JSONL profiles: {e}")
            return []
    
    def _parse_list_field(self, field_value: str) -> List[str]:
        """Parse a list field that might be a string representation."""
        if isinstance(field_value, list):
            return field_value
        if isinstance(field_value, str):
            try:
                # Try to parse as JSON array
                if field_value.startswith('['):
                    return json.loads(field_value)
                # Otherwise return as single item list
                return [field_value] if field_value else []
            except:
                return []
        return []
    
    def generate_training_questions_from_profile(self, profile: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate training questions from a real investor profile.
        
        Each profile generates 10-15 specific training questions.
        """
        questions = []
        
        # Basic portfolio construction
        age = profile['demographics']['age']
        goal = profile['goal']['primary']
        target_income = profile['goal']['target_income']
        target_date = profile['goal']['target_date']
        country = profile['demographics']['country']
        state = profile['demographics']['state']
        
        # Question 1: Overall portfolio design
        questions.append({
            "question": f"Design a dividend portfolio for a {age}-year-old {goal} investor in {country} {state or ''} targeting ${target_income:,} annual income by {target_date[:4]}",
            "category": "portfolio_construction",
            "complexity": 5,
            "profile_id": profile['profile_id']
        })
        
        # Question 2: Strategy mix
        div_growth = profile['strategy']['dividend_growth']
        high_yield = profile['strategy']['high_yield']
        bond_led = profile['strategy']['bond_led']
        
        questions.append({
            "question": f"Create optimal allocation with {div_growth}% dividend growth, {high_yield}% high yield, {bond_led}% bonds for {goal} investor",
            "category": "asset_allocation",
            "complexity": 4,
            "profile_id": profile['profile_id']
        })
        
        # Question 3: Risk management
        risk_band = profile['risk']['band']
        max_drawdown = profile['risk']['max_drawdown']
        
        questions.append({
            "question": f"Implement {risk_band} risk strategy with {max_drawdown}% maximum drawdown tolerance",
            "category": "risk_management",
            "complexity": 3,
            "profile_id": profile['profile_id']
        })
        
        # Question 4: Yield targeting
        yield_today = profile['strategy']['target_yield_today']
        yield_5y = profile['strategy']['target_yield_5y']
        
        questions.append({
            "question": f"Build portfolio targeting {yield_today}% yield today growing to {yield_5y}% in 5 years",
            "category": "yield_optimization",
            "complexity": 4,
            "profile_id": profile['profile_id']
        })
        
        # Question 5: Tax optimization
        tax_rate = profile['tax']['marginal_rate']
        filing_status = profile['tax']['filing_status']
        
        questions.append({
            "question": f"Optimize dividend taxes for {filing_status} filer in {tax_rate}% bracket",
            "category": "tax_optimization",
            "complexity": 3,
            "profile_id": profile['profile_id']
        })
        
        # Question 6: DRIP strategy
        drip_policy = profile['strategy']['drip_policy']
        
        questions.append({
            "question": f"Implement {drip_policy} reinvestment strategy for {age}-year-old {goal} investor",
            "category": "drip_strategy",
            "complexity": 2,
            "profile_id": profile['profile_id']
        })
        
        # Question 7: Net worth allocation
        net_worth = profile['financial']['net_worth']
        emergency_months = profile['financial']['emergency_months']
        
        questions.append({
            "question": f"Allocate {net_worth} portfolio with {emergency_months} months emergency fund",
            "category": "wealth_management",
            "complexity": 3,
            "profile_id": profile['profile_id']
        })
        
        # Question 8: Constraint handling
        exclusions = profile['constraints']['exclusions']
        if exclusions and exclusions != ['none']:
            questions.append({
                "question": f"Build ESG-compliant portfolio excluding {', '.join(exclusions)}",
                "category": "esg_constraints",
                "complexity": 3,
                "profile_id": profile['profile_id']
            })
        
        # Question 9: Income volatility
        income_vol = profile['risk']['income_volatility']
        
        questions.append({
            "question": f"Design stable dividend stream with maximum {income_vol}% annual income volatility",
            "category": "income_stability",
            "complexity": 4,
            "profile_id": profile['profile_id']
        })
        
        # Question 10: Broker optimization
        brokers = profile['constraints']['brokers']
        if brokers:
            questions.append({
                "question": f"Optimize portfolio for {', '.join(brokers[:2])} platform capabilities",
                "category": "platform_optimization",
                "complexity": 2,
                "profile_id": profile['profile_id']
            })
        
        return questions
    
    def create_profile_clusters(self, profiles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Cluster profiles by similar characteristics for pattern learning.
        
        This helps Harvey learn patterns across similar investor types.
        """
        clusters = {
            "young_growth": [],      # Age < 40, income-growth
            "pre_retirement": [],    # Age 50-65, balanced/income-now
            "retirement": [],        # Age 65+, income-now
            "high_net_worth": [],    # $1m+ investable
            "conservative": [],      # Conservative risk band
            "aggressive": [],        # Aggressive risk band
            "high_yield_seekers": [], # Target yield > 6%
            "dividend_growers": [],  # Dividend growth > 50% allocation
            "international": []      # Non-US investors
        }
        
        for profile in profiles:
            age = profile['demographics']['age']
            goal = profile['goal']['primary']
            net_worth = profile['financial']['net_worth']
            risk_band = profile['risk']['band']
            target_yield = profile['strategy']['target_yield_today']
            div_growth_pct = profile['strategy']['dividend_growth']
            country = profile['demographics']['country']
            
            # Age-based clustering
            if age < 40 and goal == 'income-growth':
                clusters['young_growth'].append(profile)
            elif 50 <= age < 65:
                clusters['pre_retirement'].append(profile)
            elif age >= 65:
                clusters['retirement'].append(profile)
            
            # Wealth-based clustering
            if '$1m' in net_worth or '$5m' in net_worth:
                clusters['high_net_worth'].append(profile)
            
            # Risk-based clustering
            if risk_band == 'conservative':
                clusters['conservative'].append(profile)
            elif risk_band == 'aggressive':
                clusters['aggressive'].append(profile)
            
            # Strategy-based clustering
            if target_yield > 6:
                clusters['high_yield_seekers'].append(profile)
            if div_growth_pct > 50:
                clusters['dividend_growers'].append(profile)
            
            # Geography-based clustering
            if country != 'United States':
                clusters['international'].append(profile)
        
        # Log cluster statistics
        for cluster_name, cluster_profiles in clusters.items():
            if cluster_profiles:
                logger.info(f"Cluster '{cluster_name}': {len(cluster_profiles)} profiles")
        
        return clusters
    
    def generate_cluster_training_questions(self, clusters: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, str]]:
        """
        Generate training questions based on profile clusters.
        
        These teach Harvey to recognize patterns across investor types.
        """
        questions = []
        
        for cluster_name, cluster_profiles in clusters.items():
            if not cluster_profiles:
                continue
            
            # Calculate cluster averages
            avg_age = sum(p['demographics']['age'] for p in cluster_profiles) / len(cluster_profiles)
            avg_income_target = sum(p['goal']['target_income'] for p in cluster_profiles) / len(cluster_profiles)
            avg_yield = sum(p['strategy']['target_yield_today'] for p in cluster_profiles) / len(cluster_profiles)
            
            # Generate cluster-specific questions
            if cluster_name == 'young_growth':
                questions.append({
                    "question": f"What's the optimal dividend strategy for investors under 40 targeting growth?",
                    "category": "demographic_strategy",
                    "complexity": 4,
                    "cluster": cluster_name,
                    "cluster_size": len(cluster_profiles)
                })
            
            elif cluster_name == 'pre_retirement':
                questions.append({
                    "question": f"How should pre-retirees aged 50-65 balance income and growth with average ${avg_income_target:,.0f} target?",
                    "category": "lifecycle_planning",
                    "complexity": 4,
                    "cluster": cluster_name,
                    "cluster_size": len(cluster_profiles)
                })
            
            elif cluster_name == 'retirement':
                questions.append({
                    "question": f"Design income strategy for retirees averaging {avg_age:.0f} years old targeting {avg_yield:.1f}% yield",
                    "category": "retirement_income",
                    "complexity": 4,
                    "cluster": cluster_name,
                    "cluster_size": len(cluster_profiles)
                })
            
            elif cluster_name == 'high_net_worth':
                questions.append({
                    "question": f"Optimize dividend strategy for high-net-worth investors ($1M+) balancing tax efficiency and income",
                    "category": "wealth_management",
                    "complexity": 5,
                    "cluster": cluster_name,
                    "cluster_size": len(cluster_profiles)
                })
            
            elif cluster_name == 'conservative':
                questions.append({
                    "question": f"Build defensive dividend portfolio for conservative investors prioritizing capital preservation",
                    "category": "risk_management",
                    "complexity": 3,
                    "cluster": cluster_name,
                    "cluster_size": len(cluster_profiles)
                })
            
            elif cluster_name == 'aggressive':
                questions.append({
                    "question": f"Design high-growth dividend strategy for aggressive investors accepting volatility",
                    "category": "growth_strategy",
                    "complexity": 4,
                    "cluster": cluster_name,
                    "cluster_size": len(cluster_profiles)
                })
            
            elif cluster_name == 'high_yield_seekers':
                questions.append({
                    "question": f"Create portfolio achieving {avg_yield:.1f}% yield while managing dividend sustainability risks",
                    "category": "yield_optimization",
                    "complexity": 4,
                    "cluster": cluster_name,
                    "cluster_size": len(cluster_profiles)
                })
            
            elif cluster_name == 'international':
                questions.append({
                    "question": f"Optimize dividend strategy for international investors considering withholding taxes and currency risk",
                    "category": "international_strategy",
                    "complexity": 5,
                    "cluster": cluster_name,
                    "cluster_size": len(cluster_profiles)
                })
        
        return questions
    
    def process_bulk_profiles(self, content: str, file_format: str = "csv") -> Dict[str, Any]:
        """
        Process bulk profiles and generate comprehensive training data.
        
        Args:
            content: File content (CSV or JSONL)
            file_format: Format of the file ("csv" or "jsonl")
            
        Returns:
            Training data statistics and questions
        """
        # Parse profiles based on format
        if file_format.lower() == "csv":
            profiles = self.process_csv_profiles(content)
        elif file_format.lower() in ["jsonl", "json"]:
            profiles = self.process_jsonl_profiles(content)
        else:
            return {"error": f"Unsupported format: {file_format}"}
        
        if not profiles:
            return {"error": "No profiles processed"}
        
        # Generate training questions for each profile
        all_questions = []
        for profile in profiles:
            questions = self.generate_training_questions_from_profile(profile)
            all_questions.extend(questions)
        
        # Create profile clusters
        clusters = self.create_profile_clusters(profiles)
        
        # Generate cluster-based questions
        cluster_questions = self.generate_cluster_training_questions(clusters)
        all_questions.extend(cluster_questions)
        
        # Calculate statistics
        stats = {
            "total_profiles": len(profiles),
            "total_questions": len(all_questions),
            "questions_per_profile": len(all_questions) / len(profiles) if profiles else 0,
            "profile_demographics": {
                "age_range": f"{min(p['demographics']['age'] for p in profiles)}-{max(p['demographics']['age'] for p in profiles)}",
                "countries": len(set(p['demographics']['country'] for p in profiles)),
                "avg_income_target": sum(p['goal']['target_income'] for p in profiles) / len(profiles)
            },
            "goal_distribution": {},
            "risk_distribution": {},
            "cluster_sizes": {name: len(profs) for name, profs in clusters.items() if profs}
        }
        
        # Calculate distributions
        for profile in profiles:
            goal = profile['goal']['primary']
            risk = profile['risk']['band']
            stats['goal_distribution'][goal] = stats['goal_distribution'].get(goal, 0) + 1
            stats['risk_distribution'][risk] = stats['risk_distribution'].get(risk, 0) + 1
        
        return {
            "success": True,
            "profiles": profiles,
            "questions": all_questions,
            "statistics": stats,
            "clusters": {k: len(v) for k, v in clusters.items()}
        }


# Global instance
bulk_ingestion = BulkProfileIngestion()