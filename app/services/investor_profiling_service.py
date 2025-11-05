"""
Investor Profiling & Personalization Service
Processes investor questionnaire responses to create personalized dividend strategies.
Integrates with Harvey's training system for continuous learning.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

logger = logging.getLogger("investor_profiling")


class InvestorProfileTraining:
    """
    Converts investor profiling schema and responses into training data
    for Harvey's multi-model system.
    """
    
    # Complete investor profiling schema
    PROFILING_SCHEMA = {
        "intake_questions": [
            "What's your primary objective for passive income? (income-now/income-growth/balanced)",
            "What annual passive income (post-tax) are you targeting?",
            "When should the target income be fully reliable?",
            "What is your age?",
            "What is your investable net worth range?",
            "How many months of emergency fund do you have?",
            "What's your overall risk tolerance? (conservative/moderate/aggressive)",
            "What's the maximum drawdown you can tolerate?",
            "What annual income volatility can you accept?",
            "Any sectors/themes to exclude for ESG reasons?"
        ],
        
        "portfolio_questions": [
            "Which brokers/custodians do you use?",
            "How are dividends currently handled? (DRIP-all/DRIP-some/cash-all)",
            "Upload recent account statements for analysis",
            "Current portfolio composition and holdings"
        ],
        
        "strategy_questions": [
            "Preferred strategy mix: dividend-growth vs high-yield vs bonds vs options?",
            "Preference for ETFs vs individual stocks?",
            "Target portfolio yield today?",
            "Target portfolio yield in 5 years?",
            "Minimum acceptable dividend growth rate?",
            "Maximum payout ratio for common stocks?",
            "Maximum FFO payout ratio for REITs?",
            "Preferred dividend payment frequency?",
            "Should we smooth monthly cash flow?",
            "Policy if a holding cuts its dividend?",
            "Yield trap threshold to flag risky positions?",
            "Preference for qualified vs ordinary dividends?"
        ],
        
        "tax_questions": [
            "Country of tax residence?",
            "State/Province if applicable?",
            "Tax filing status?",
            "Top marginal tax rate?",
            "Account types available (taxable/IRA/401k)?",
            "K-1 tolerance for MLPs?",
            "Foreign withholding tax acceptance?"
        ],
        
        "execution_questions": [
            "How often do you add new cash?",
            "Dollar-cost averaging or lump sum investing?",
            "Rebalancing frequency?",
            "Maximum trades per month?",
            "DRIP policy going forward?",
            "Ex-dividend date alert preferences?"
        ],
        
        "instrument_questions": [
            "Accept REITs in portfolio?",
            "Accept BDCs (Business Development Companies)?",
            "Accept leveraged CEFs? Max leverage?",
            "Use covered call strategies?",
            "Build bond ladders?",
            "Target duration for bonds?",
            "Minimum credit quality?"
        ],
        
        "monitoring_questions": [
            "Alert triggers (dividend cuts, downgrades, etc)?",
            "Maximum single position yield before concern?",
            "Single issuer concentration cap?",
            "KPI dashboard preferences?",
            "Reporting detail level?"
        ]
    }
    
    # Sample investor profiles for training
    SAMPLE_PROFILES = [
        {
            "profile_name": "Growth-Focused Millennial",
            "characteristics": {
                "age": 35,
                "goal": "income-growth",
                "target_income": 60000,
                "target_date": "2035",
                "risk_band": "moderate",
                "net_worth": "$250k-$1m",
                "location": "California, USA"
            },
            "strategy": {
                "mix": {"dividend-growth": 55, "high-yield": 20, "bond-led": 15, "options": 5},
                "target_yield_today": 3.5,
                "target_yield_5y": 4.5,
                "min_div_growth": 7,
                "drip_policy": "DRIP-by-list"
            },
            "training_questions": [
                "Build a portfolio for a 35-year-old targeting $60k income by 2035",
                "Create dividend growth strategy with 7% minimum growth rate",
                "Design tax-efficient portfolio for California resident",
                "Optimize for qualified dividends with moderate risk",
                "Select stocks for DRIP: SCHD, VIG, O, LOW"
            ]
        },
        {
            "profile_name": "Pre-Retirement Income Seeker",
            "characteristics": {
                "age": 58,
                "goal": "income-now",
                "target_income": 90000,
                "target_date": "2026",
                "risk_band": "conservative",
                "net_worth": "$1m-$5m",
                "location": "Texas, USA"
            },
            "strategy": {
                "mix": {"dividend-growth": 20, "high-yield": 60, "bond-led": 35, "options": 10},
                "target_yield_today": 6.8,
                "target_yield_5y": 7.0,
                "min_div_growth": 3,
                "drip_policy": "cash-all"
            },
            "training_questions": [
                "Design high-yield portfolio for $90k annual income",
                "Create monthly income stream for retiree",
                "Build conservative portfolio with 6.8% yield",
                "Minimize volatility while maximizing current income",
                "Structure portfolio for Texas resident (no state tax)"
            ]
        },
        {
            "profile_name": "UK Balanced Investor",
            "characteristics": {
                "age": 72,
                "goal": "balanced",
                "target_income": 48000,
                "target_date": "2025",
                "risk_band": "moderate",
                "net_worth": "$1m-$5m",
                "location": "United Kingdom"
            },
            "strategy": {
                "mix": {"dividend-growth": 35, "high-yield": 25, "bond-led": 35, "options": 0},
                "target_yield_today": 4.2,
                "target_yield_5y": 5.0,
                "min_div_growth": 5,
                "drip_policy": "DRIP-by-list"
            },
            "training_questions": [
                "Build UK-focused dividend portfolio avoiding fossil fuels",
                "Create ISA-eligible dividend strategy",
                "Balance growth and income for UK retiree",
                "Optimize for UK tax efficiency with foreign holdings",
                "Select ETFs for 65% allocation: ULVR.L, DGE.L, O, JEPI"
            ]
        }
    ]
    
    def generate_profile_training_questions(self, profile: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate training questions based on investor profile.
        
        Creates personalized Q&A pairs for training Harvey on:
        - Portfolio construction
        - Risk management
        - Tax optimization
        - Income strategies
        """
        questions = []
        
        # Portfolio construction questions
        age = profile['characteristics']['age']
        goal = profile['characteristics']['goal']
        target_income = profile['characteristics']['target_income']
        target_date = profile['characteristics']['target_date']
        
        questions.append({
            "question": f"Build a dividend portfolio for a {age}-year-old investor targeting ${target_income:,} annual income by {target_date}",
            "category": "portfolio_construction",
            "complexity": 4
        })
        
        # Strategy questions based on mix
        strategy_mix = profile['strategy']['mix']
        yield_target = profile['strategy']['target_yield_today']
        
        questions.append({
            "question": f"Create a portfolio with {strategy_mix['dividend-growth']}% dividend growth, {strategy_mix['high-yield']}% high yield, targeting {yield_target}% overall yield",
            "category": "strategy_design",
            "complexity": 4
        })
        
        # Risk management questions
        risk_band = profile['characteristics']['risk_band']
        questions.append({
            "question": f"Design {risk_band} risk dividend portfolio for {goal} investor profile",
            "category": "risk_management",
            "complexity": 3
        })
        
        # Tax optimization questions
        location = profile['characteristics']['location']
        questions.append({
            "question": f"Optimize dividend portfolio for tax efficiency in {location}",
            "category": "tax_optimization",
            "complexity": 3
        })
        
        # DRIP strategy questions
        drip_policy = profile['strategy']['drip_policy']
        questions.append({
            "question": f"Implement {drip_policy} strategy for dividend reinvestment",
            "category": "drip_strategy",
            "complexity": 2
        })
        
        # Income smoothing questions
        questions.append({
            "question": f"Create monthly income stream of ${target_income/12:,.0f} from dividends",
            "category": "income_planning",
            "complexity": 3
        })
        
        # Sector allocation questions
        if 'exclusions' in profile.get('characteristics', {}):
            exclusions = profile['characteristics'].get('exclusions', [])
            if exclusions and exclusions != ['none']:
                questions.append({
                    "question": f"Build ESG-compliant portfolio excluding {', '.join(exclusions)}",
                    "category": "esg_constraints",
                    "complexity": 3
                })
        
        return questions
    
    def create_scenario_based_training(self) -> List[Dict[str, Any]]:
        """
        Create scenario-based training questions from investor profiles.
        
        These teach Harvey how to handle different investor situations:
        - Life stage transitions
        - Market conditions
        - Tax changes
        - Income needs evolution
        """
        scenarios = []
        
        # Scenario 1: Young professional building wealth
        scenarios.append({
            "scenario": "35-year-old software engineer in California with $500K to invest",
            "questions": [
                "How should I balance dividend growth vs high yield at age 35?",
                "What's the optimal DRIP strategy for long-term wealth building?",
                "How do I minimize California state taxes on dividends?",
                "Should I prioritize qualified dividends in a high tax state?",
                "What's the right mix of individual stocks vs ETFs for my age?"
            ],
            "profile_match": "Growth-Focused Millennial"
        })
        
        # Scenario 2: Pre-retiree transitioning to income
        scenarios.append({
            "scenario": "58-year-old executive retiring in 2 years, needs $90K income",
            "questions": [
                "How do I transition from growth to income before retirement?",
                "What yield should I target 2 years before retirement?",
                "Should I take dividends as cash or reinvest near retirement?",
                "How do I protect against dividend cuts in retirement?",
                "What's the right bond allocation for a pre-retiree?"
            ],
            "profile_match": "Pre-Retirement Income Seeker"
        })
        
        # Scenario 3: International investor with ESG constraints
        scenarios.append({
            "scenario": "UK retiree avoiding fossil fuels and weapons, needs £40K income",
            "questions": [
                "How do I build ESG-compliant dividend portfolio in the UK?",
                "What's the impact of avoiding fossil fuel dividends on yield?",
                "How do I handle withholding taxes on US dividends?",
                "Should I use ISA accounts for dividend investing?",
                "What's the optimal UK/international stock mix?"
            ],
            "profile_match": "UK Balanced Investor"
        })
        
        # Market condition scenarios
        scenarios.append({
            "scenario": "Rising interest rate environment",
            "questions": [
                "How do rising rates affect dividend stock valuations?",
                "Should I shift from dividend stocks to bonds when rates rise?",
                "Which dividend sectors perform best in rising rates?",
                "How do I protect dividend income from rate hikes?",
                "What's the impact on REIT dividends when rates rise?"
            ],
            "profile_match": "all"
        })
        
        # Tax change scenarios
        scenarios.append({
            "scenario": "Proposed increase in dividend tax rates",
            "questions": [
                "How do I prepare for higher dividend taxes?",
                "Should I accelerate dividend income before tax changes?",
                "What's the benefit of qualified vs ordinary dividends?",
                "How do I use tax-advantaged accounts for dividends?",
                "Should I shift to tax-exempt municipal bonds?"
            ],
            "profile_match": "all"
        })
        
        return scenarios
    
    def generate_decision_tree_training(self) -> Dict[str, Any]:
        """
        Create decision tree training for systematic portfolio construction.
        
        Teaches Harvey the logical flow:
        1. Assess investor profile
        2. Determine appropriate strategies
        3. Select suitable instruments
        4. Implement and monitor
        """
        decision_tree = {
            "start": "Determine primary goal",
            "branches": {
                "income-now": {
                    "priority": "Maximize current yield",
                    "strategies": ["high-yield stocks", "REITs", "BDCs", "covered calls"],
                    "target_yield": "6-8%",
                    "risk_controls": ["diversification", "quality screens", "yield trap avoidance"]
                },
                "income-growth": {
                    "priority": "Balance current income with growth",
                    "strategies": ["dividend growers", "dividend aristocrats", "quality ETFs"],
                    "target_yield": "3-5%",
                    "risk_controls": ["payout ratio limits", "earnings growth requirements"]
                },
                "balanced": {
                    "priority": "Steady income with capital preservation",
                    "strategies": ["mixed allocation", "bonds", "defensive dividends"],
                    "target_yield": "4-6%",
                    "risk_controls": ["asset allocation", "rebalancing", "quality focus"]
                }
            },
            "risk_assessment": {
                "conservative": {
                    "max_equity": 60,
                    "min_quality": "BBB",
                    "max_single_position": 5,
                    "preferred_instruments": ["dividend ETFs", "investment-grade bonds", "utilities"]
                },
                "moderate": {
                    "max_equity": 80,
                    "min_quality": "BB",
                    "max_single_position": 8,
                    "preferred_instruments": ["dividend stocks", "REITs", "high-yield bonds"]
                },
                "aggressive": {
                    "max_equity": 95,
                    "min_quality": "B",
                    "max_single_position": 12,
                    "preferred_instruments": ["high-yield stocks", "BDCs", "covered calls", "MLPs"]
                }
            },
            "tax_optimization": {
                "high_tax_bracket": ["prioritize qualified dividends", "use tax-advantaged accounts", "consider munis"],
                "moderate_tax_bracket": ["balance qualified and ordinary", "strategic account placement"],
                "low_tax_bracket": ["focus on total return", "maximize yield regardless of type"]
            }
        }
        
        return decision_tree
    
    def create_comprehensive_training_set(self) -> List[Dict[str, Any]]:
        """
        Create comprehensive training dataset combining:
        - Profile-based questions
        - Scenario-based questions
        - Decision tree logic
        - Real investor examples
        """
        training_set = []
        
        # Generate questions for each sample profile
        for profile in self.SAMPLE_PROFILES:
            profile_questions = self.generate_profile_training_questions(profile)
            for q in profile_questions:
                training_set.append({
                    "question_id": f"profile_{hashlib.md5(q['question'].encode()).hexdigest()[:8]}",
                    "question": q['question'],
                    "category": q['category'],
                    "complexity": q['complexity'],
                    "profile_context": profile['profile_name']
                })
        
        # Add scenario-based training
        scenarios = self.create_scenario_based_training()
        for scenario in scenarios:
            for question in scenario['questions']:
                training_set.append({
                    "question_id": f"scenario_{hashlib.md5(question.encode()).hexdigest()[:8]}",
                    "question": question,
                    "category": "scenario_based",
                    "complexity": 3,
                    "scenario_context": scenario['scenario']
                })
        
        # Add decision tree training questions
        decision_tree = self.generate_decision_tree_training()
        for goal, strategy in decision_tree['branches'].items():
            question = f"What's the optimal strategy for {goal} investor profile?"
            training_set.append({
                "question_id": f"decision_{hashlib.md5(question.encode()).hexdigest()[:8]}",
                "question": question,
                "category": "strategy_selection",
                "complexity": 4,
                "expected_elements": strategy
            })
        
        return training_set
    
    def generate_personalization_rules(self) -> Dict[str, Any]:
        """
        Generate rules for personalizing responses based on investor profile.
        
        These rules teach Harvey how to adapt recommendations.
        """
        rules = {
            "age_based": {
                "under_40": {
                    "focus": "growth and accumulation",
                    "drip_preference": "DRIP-all",
                    "risk_capacity": "higher",
                    "time_horizon": "20+ years"
                },
                "40_55": {
                    "focus": "balanced growth and income",
                    "drip_preference": "DRIP-selective",
                    "risk_capacity": "moderate",
                    "time_horizon": "10-20 years"
                },
                "55_65": {
                    "focus": "income with growth",
                    "drip_preference": "mixed",
                    "risk_capacity": "moderate-conservative",
                    "time_horizon": "5-10 years"
                },
                "over_65": {
                    "focus": "income and preservation",
                    "drip_preference": "cash",
                    "risk_capacity": "conservative",
                    "time_horizon": "5 years"
                }
            },
            "goal_based": {
                "income_now": {
                    "yield_priority": "maximize current",
                    "growth_priority": "secondary",
                    "instruments": ["high-yield", "REITs", "BDCs", "preferreds"],
                    "frequency": "monthly preferred"
                },
                "income_growth": {
                    "yield_priority": "moderate current",
                    "growth_priority": "primary",
                    "instruments": ["dividend growers", "aristocrats", "quality ETFs"],
                    "frequency": "quarterly acceptable"
                },
                "balanced": {
                    "yield_priority": "balanced",
                    "growth_priority": "balanced",
                    "instruments": ["mixed strategies", "core holdings", "bonds"],
                    "frequency": "flexible"
                }
            },
            "tax_based": {
                "high_bracket": {
                    "optimize_for": "qualified dividends",
                    "avoid": "ordinary income, REITs in taxable",
                    "use": "tax-advantaged accounts, munis"
                },
                "low_bracket": {
                    "optimize_for": "total return",
                    "flexible_on": "dividend type",
                    "use": "highest yielding options"
                }
            }
        }
        
        return rules


# Global instance
investor_profiling = InvestorProfileTraining()