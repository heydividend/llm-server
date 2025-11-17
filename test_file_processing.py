"""
Test script for enhanced file processing with uploaded portfolio files
"""

import asyncio
from app.services.enhanced_file_processor import enhanced_file_processor

async def test_file_processing():
    """Test file processing with actual uploaded files"""
    
    print("🧪 Testing Enhanced File Processing System\n")
    print("=" * 70)
    
    # Test files from attached_assets
    test_files = [
        {
            "path": "attached_assets/2025-08-18_19-27-5_1763417174504.pdf",
            "name": "Portfolio Statement PDF",
            "type": "pdf"
        },
        {
            "path": "attached_assets/2025-08-18_19-27-50_1763417174504.jpg",
            "name": "Portfolio Screenshot JPG",
            "type": "jpg"
        },
        {
            "path": "attached_assets/2025-08-18_19-27-50_1763417174505.png",
            "name": "Portfolio Screenshot PNG",
            "type": "png"
        }
    ]
    
    for test_file in test_files:
        print(f"\n📄 Testing: {test_file['name']}")
        print("-" * 70)
        
        try:
            # Read file
            with open(test_file["path"], "rb") as f:
                file_bytes = f.read()
            
            print(f"   File size: {len(file_bytes):,} bytes")
            
            # Process file
            result = enhanced_file_processor.process_file(
                file_bytes=file_bytes,
                file_name=test_file["path"].split("/")[-1],
                rid="test"
            )
            
            if result.success:
                print(f"   ✅ Processing successful!")
                print(f"   File type: {result.file_type.value}")
                print(f"   Source: {result.source.value}")
                print(f"   Holdings detected: {len(result.portfolio_holdings)}")
                
                if result.portfolio_holdings:
                    print(f"\n   📊 Detected Holdings:")
                    for holding in result.portfolio_holdings[:5]:  # Show first 5
                        print(f"      • {holding.ticker}: {holding.shares} shares @ ${holding.current_price}")
                    
                    if len(result.portfolio_holdings) > 5:
                        print(f"      ... and {len(result.portfolio_holdings) - 5} more")
                
                if result.metadata:
                    print(f"\n   📈 Metadata:")
                    for key, value in result.metadata.items():
                        print(f"      {key}: {value}")
            else:
                print(f"   ❌ Processing failed: {result.error}")
        
        except FileNotFoundError:
            print(f"   ⚠️  File not found: {test_file['path']}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ File Processing Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_file_processing())
