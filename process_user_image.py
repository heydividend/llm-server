#!/usr/bin/env python3
"""
Process the user's uploaded image using Harvey's OCR capabilities.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.azure_document_intelligence import AzureDocumentIntelligence


def process_image_with_ocr(image_path: str):
    """Process image using Azure Document Intelligence OCR."""
    
    # Initialize Azure Document Intelligence
    ocr_service = AzureDocumentIntelligence()
    
    if not ocr_service.enabled:
        print("⚠️ Azure Document Intelligence is not configured in this environment")
        print("The OCR service requires Azure credentials that are configured on the production VM")
        return None
    
    try:
        # Read the image file
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        print(f"📄 Processing image: {image_path}")
        print(f"📏 File size: {len(image_bytes) / 1024:.2f} KB")
        
        # Extract text from image
        result = ocr_service.extract_from_image(
            image_bytes=image_bytes,
            file_name=os.path.basename(image_path),
            extract_tables=True
        )
        
        if result.success:
            print("\n✅ OCR Extraction Successful!")
            print(f"📊 Processing time: {result.processing_time_ms}ms")
            print(f"🔍 Confidence: {result.confidence:.2%}")
            print("\n" + "="*60)
            print("EXTRACTED TEXT:")
            print("="*60)
            print(result.text)
            
            if result.tables:
                print("\n" + "="*60)
                print(f"EXTRACTED TABLES ({len(result.tables)}):")
                print("="*60)
                for i, table in enumerate(result.tables, 1):
                    print(f"\nTable {i}:")
                    print(table)
            
            if result.structured_data:
                print("\n" + "="*60)
                print("STRUCTURED DATA:")
                print("="*60)
                print(result.structured_data)
            
            return result
        else:
            print(f"\n❌ OCR Extraction Failed: {result.error}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error processing image: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Process the user's uploaded image
    image_path = "attached_assets/IMG_3094_1762357548662.jpeg"
    
    if os.path.exists(image_path):
        result = process_image_with_ocr(image_path)
    else:
        print(f"❌ Image file not found: {image_path}")