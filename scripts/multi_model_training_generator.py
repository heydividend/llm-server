"""
Harvey AI - Multi-Model Training Data Generator
Uses ALL 4 AI models (GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro) to train Harvey

Vision: Harvey will eventually stand alone. Until then, let the masters teach the student.

Architecture:
1. GPT-5: Complex reasoning, comprehensive analysis
2. Grok-4: Fast reasoning, real-time insights  
3. DeepSeek-R1: Quantitative analysis, mathematical modeling
4. Gemini 2.5 Pro: Multimodal, sustainability, strategic analysis

All 4 models generate training data → Harvey learns from diverse perspectives
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv(override=True)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.model_router import QueryRouter, ModelType, QueryType
from app.core.llm_providers import oai_client, gemini_stream
from app.services.training_ingestion_service import training_ingestion

class MultiModelTrainingGenerator:
    """
    Generate training data using all 4 AI models.
    Each model contributes its unique perspective to train Harvey.
    """
    
    def __init__(self):
        """Initialize multi-model training generator"""
        self.router = QueryRouter()
        
        # Model configurations (using available models)
        self.models = {
            "GPT-5": {
                "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "HarveyGPT-5"),
                "specialization": "Complex reasoning, comprehensive financial analysis",
                "type": ModelType.GPT5
            },
            "Grok-4": {
                "deployment": "grok-4-fast-reasoning",
                "specialization": "Fast reasoning, real-time market insights",
                "type": ModelType.GROK4
            },
            "DeepSeek-R1": {
                "deployment": "DeepSeek-R1-0528",
                "specialization": "Quantitative analysis, mathematical modeling",
                "type": ModelType.DEEPSEEK
            },
            "Gemini-2.5-Pro": {
                "deployment": "gemini-2.5-pro",
                "specialization": "Dividend sustainability, risk assessment, portfolio optimization",
                "type": ModelType.GEMINI
            }
        }
        
        # Dividend-focused question templates
        self.question_categories = {
            "dividend_analysis": [
                "What makes {ticker} a quality dividend stock?",
                "Analyze {ticker}'s dividend sustainability",
                "Is {ticker}'s payout ratio healthy?",
                "How does {ticker}'s dividend growth compare to peers?"
            ],
            "income_strategies": [
                "How can I build a $3000/month dividend portfolio?",
                "What's the best allocation for dividend income?",
                "Should I use DRIP or take dividends in cash?",
                "How to create a monthly dividend income ladder?"
            ],
            "risk_assessment": [
                "What are the risks of high-yield dividend stocks?",
                "How to identify dividend cut risks?",
                "Is {ticker}'s dividend safe during a recession?",
                "How to diversify dividend portfolio risk?"
            ],
            "technical_timing": [
                "Should I buy {ticker} before or after ex-dividend date?",
                "How does ex-dividend date affect stock price?",
                "Best timing for dividend capture strategy?",
                "When to sell a dividend stock?"
            ],
            "etf_funds": [
                "Compare SCHD vs VYM for dividend income",
                "Best dividend ETFs for retirement income?",
                "How do dividend ETFs differ from individual stocks?",
                "Should I invest in dividend growth or high-yield ETFs?"
            ],
            "tax_optimization": [
                "How are qualified dividends taxed?",
                "Tax-efficient dividend investing strategies?",
                "REIT dividends vs qualified dividends taxation?",
                "How to minimize taxes on dividend income?"
            ],
            "quantitative_analysis": [
                "Calculate optimal portfolio allocation for $10k/year dividend income",
                "Model dividend growth using compound annual growth rate",
                "Backtest dividend aristocrats performance",
                "Optimize portfolio using Sharpe ratio for dividend stocks"
            ],
            "global_dividends": [
                "Best international dividend stocks?",
                "How to handle foreign dividend withholding taxes?",
                "Compare US vs European dividend yields",
                "Currency risk in international dividend investing?"
            ]
        }
        
        # Sample tickers for questions
        self.sample_tickers = ["AAPL", "MSFT", "JNJ", "PG", "KO", "PEP", "VZ", "T", "O", "SCHD"]
    
    def generate_from_model(
        self,
        model_name: str,
        category: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate training questions from a specific model.
        
        Args:
            model_name: Name of model (GPT-5, Grok-4, DeepSeek-R1, Gemini-2.5-Pro)
            category: Question category
            count: Number of questions to generate
            
        Returns:
            List of training questions with answers
        """
        print(f"\n🤖 {model_name}: Generating {count} questions for '{category}'...")
        
        model_config = self.models.get(model_name)
        if not model_config:
            print(f"   ❌ Unknown model: {model_name}")
            return []
        
        deployment = model_config["deployment"]
        specialization = model_config["specialization"]
        
        # Craft a specialized prompt based on model strengths
        system_prompt = self._get_system_prompt(model_name, category, specialization)
        
        try:
            # Generate questions using the model
            if model_name == "Gemini-2.5-Pro":
                questions = self._generate_with_gemini(system_prompt, category, count)
            else:
                questions = self._generate_with_azure(deployment, system_prompt, category, count)
            
            print(f"   ✅ Generated {len(questions)} questions from {model_name}")
            return questions
            
        except Exception as e:
            print(f"   ❌ Failed to generate from {model_name}: {e}")
            return []
    
    def _get_system_prompt(self, model_name: str, category: str, specialization: str) -> str:
        """Create specialized system prompt for each model"""
        base_prompt = f"""You are {model_name}, a specialized AI model training Harvey, a dividend investing assistant.

Your Specialization: {specialization}

Task: Generate {5} high-quality dividend investing questions for the '{category}' category.
Focus on your unique strengths while maintaining dividend investing context.

Requirements:
1. Questions should be practical and actionable
2. Cover real-world dividend investing scenarios
3. Demonstrate your specialized expertise ({specialization})
4. Use specific company tickers when relevant
5. Include both simple and complex questions

Output Format (JSON):
{{
  "questions": [
    {{
      "question": "Your question here",
      "category": "{category}",
      "complexity": "simple|moderate|advanced",
      "model_source": "{model_name}"
    }}
  ]
}}

Generate exactly 5 diverse questions. Return ONLY valid JSON."""
        
        return base_prompt
    
    def _generate_with_azure(
        self,
        deployment: str,
        system_prompt: str,
        category: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """Generate questions using Azure OpenAI models with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = oai_client.chat.completions.create(  # type: ignore[arg-type]
                    model=deployment,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Generate {count} dividend investing questions for '{category}' category."}
                    ],
                    temperature=0.8,  # Higher for creativity
                    max_tokens=2000,
                    timeout=30
                )
                
                content = (response.choices[0].message.content or "").strip()
                
                if not content:
                    print(f"      ⚠️  Empty response (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay)
                        continue
                    return []
                
                # Parse JSON response
                try:
                    # Extract JSON from response
                    start_idx = content.find("{")
                    end_idx = content.rfind("}") + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = content[start_idx:end_idx]
                        data = json.loads(json_str)
                        questions = data.get("questions", [])
                        if questions:
                            return questions
                        else:
                            print(f"      ⚠️  No questions in JSON (attempt {attempt + 1}/{max_retries})")
                    else:
                        print(f"      ⚠️  No JSON found in response (attempt {attempt + 1}/{max_retries})")
                except json.JSONDecodeError as e:
                    print(f"      ⚠️  JSON parse error: {e} (attempt {attempt + 1}/{max_retries})")
                
                # Retry if we didn't get valid questions
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                return []
                    
            except Exception as e:
                print(f"      ❌ Azure API error: {e} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                else:
                    return []
        
        return []
    
    def _generate_with_gemini(
        self,
        system_prompt: str,
        category: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """Generate questions using Gemini 2.5 Pro with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Combine system prompt and user prompt for Gemini
                full_prompt = f"{system_prompt}\n\nUser: Generate {count} dividend investing questions for '{category}' category."
                
                messages = [
                    {"role": "user", "content": full_prompt}
                ]
                
                # Consume the stream into a single string
                chunks = []
                for chunk in gemini_stream(messages, temperature=0.8, max_tokens=2000):
                    chunks.append(chunk)
                
                content = "".join(chunks).strip()
                
                if not content:
                    print(f"      ⚠️  Empty response from Gemini (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay)
                        continue
                    return []
                
                # Parse JSON response
                try:
                    start_idx = content.find("{")
                    end_idx = content.rfind("}") + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = content[start_idx:end_idx]
                        data = json.loads(json_str)
                        questions = data.get("questions", [])
                        if questions:
                            return questions
                        else:
                            print(f"      ⚠️  No questions in JSON (attempt {attempt + 1}/{max_retries})")
                    else:
                        print(f"      ⚠️  No JSON found in response (attempt {attempt + 1}/{max_retries})")
                except json.JSONDecodeError as e:
                    print(f"      ⚠️  JSON parse error: {e} (attempt {attempt + 1}/{max_retries})")
                
                # Retry if we didn't get valid questions
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                return []
                    
            except Exception as e:
                print(f"      ❌ Gemini API error: {e} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                else:
                    return []
        
        return []
    
    def generate_ensemble_training_data(
        self,
        category: str = "all",
        questions_per_model: int = 25
    ) -> Dict[str, Any]:
        """
        Generate training data from ALL 4 models.
        
        Args:
            category: Category to focus on, or 'all' for all categories
            questions_per_model: Questions per model per category
            
        Returns:
            Generation results with questions from all models
        """
        print("=" * 80)
        print("Harvey AI - Multi-Model Training Data Generation")
        print("Training Harvey using 4 AI Models: GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro")
        print("=" * 80)
        
        all_questions = []
        stats = {
            "total_questions": 0,
            "by_model": {},
            "by_category": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Determine categories to process
        categories = list(self.question_categories.keys()) if category == "all" else [category]
        
        for cat in categories:
            print(f"\n📚 Category: {cat}")
            print("-" * 80)
            
            # Generate from each model
            for model_name in self.models.keys():
                questions = self.generate_from_model(
                    model_name,
                    cat,
                    count=questions_per_model if category == "all" else questions_per_model * len(categories)
                )
                
                # Add to collection
                for q in questions:
                    q["generated_at"] = datetime.now(timezone.utc).isoformat()
                    q["training_source"] = "multi_model_ensemble"
                    all_questions.append(q)
                
                # Update stats
                if model_name not in stats["by_model"]:
                    stats["by_model"][model_name] = 0
                stats["by_model"][model_name] += len(questions)
                
                if cat not in stats["by_category"]:
                    stats["by_category"][cat] = 0
                stats["by_category"][cat] += len(questions)
        
        stats["total_questions"] = len(all_questions)
        
        # Summary
        print("\n" + "=" * 80)
        print("Generation Summary")
        print("=" * 80)
        print(f"Total Questions: {stats['total_questions']}")
        print(f"\nBy Model:")
        for model, count in stats["by_model"].items():
            print(f"  • {model}: {count} questions")
        print(f"\nBy Category:")
        for cat, count in stats["by_category"].items():
            print(f"  • {cat}: {count} questions")
        
        return {
            "questions": all_questions,
            "stats": stats
        }


def main():
    parser = argparse.ArgumentParser(description="Multi-Model Training Data Generator for Harvey")
    parser.add_argument(
        "--category",
        type=str,
        default="all",
        choices=["all", "dividend_analysis", "income_strategies", "risk_assessment",
                 "technical_timing", "etf_funds", "tax_optimization",
                 "quantitative_analysis", "global_dividends"],
        help="Category to generate questions for"
    )
    parser.add_argument(
        "--questions-per-model",
        type=int,
        default=25,
        help="Number of questions per model per category"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="multi_model_training_data.json",
        help="Output JSON file"
    )
    parser.add_argument(
        "--to-database",
        action="store_true",
        help="Ingest questions into training database"
    )
    
    args = parser.parse_args()
    
    # Generate training data
    generator = MultiModelTrainingGenerator()
    result = generator.generate_ensemble_training_data(
        category=args.category,
        questions_per_model=args.questions_per_model
    )
    
    # Save to file
    output_path = os.path.join("training_data", args.output)
    os.makedirs("training_data", exist_ok=True)
    
    try:
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ Saved to: {output_path}")
    except Exception as e:
        print(f"\n❌ Failed to save file: {e}")
    
    # Ingest to database if requested
    if args.to_database:
        print("\n📥 Ingesting into training database...")
        try:
            # Convert to training_ingestion format (matching ingest_gemini_questions signature)
            questions_for_db = [
                {
                    "question": q["question"],  # Required field
                    "category": q.get("category", "general"),  # Required field
                    # Note: 'answer' is optional - we don't provide it since these are training prompts
                }
                for q in result["questions"]
            ]
            
            ingest_result = training_ingestion.ingest_gemini_questions(
                questions=questions_for_db,
                prevent_duplicates=True
            )
            
            if ingest_result.get("success"):
                print(f"   ✅ Ingested {ingest_result['ingested']} questions")
                print(f"   ℹ️  Duplicates skipped: {ingest_result['duplicates']}")
                print(f"   ⚠️  Errors: {ingest_result['errors']}")
            else:
                print(f"   ❌ Ingestion failed: {ingest_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Database ingestion error: {e}")
    
    print("\n" + "=" * 80)
    print(f"🎓 Harvey Training Complete - {result['stats']['total_questions']} questions generated")
    print("   Harvey is learning from 4 AI masters to eventually stand alone!")
    print("=" * 80)


if __name__ == "__main__":
    main()
