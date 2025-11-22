#!/usr/bin/env python3
"""
Python dependency validation script for clustering services
Tests if all required ML dependencies are available
"""
import json
import sys

def test_clustering_dependencies():
    """Test if all required clustering dependencies are available"""
    required_packages = {
        'numpy': 'NumPy for numerical computing',
        'pandas': 'Pandas for data manipulation',
        'scikit-learn': 'Scikit-learn for machine learning',
        'scipy': 'SciPy for scientific computing',
        'joblib': 'Joblib for persistence'
    }
    
    available = {}
    missing = []
    
    for package, description in required_packages.items():
        try:
            if package == 'scikit-learn':
                # Special case for scikit-learn
                module = __import__('sklearn')
                package_name = 'sklearn'
            else:
                module = __import__(package)
                package_name = package
                
            available[package] = {
                'version': getattr(module, '__version__', 'unknown'),
                'description': description,
                'import_name': package_name
            }
        except ImportError:
            missing.append(package)
    
    result = {
        'success': len(missing) == 0,
        'available': available,
        'missing': missing,
        'python_version': sys.version,
        'total_packages': len(required_packages),
        'available_count': len(available),
        'missing_count': len(missing)
    }
    
    return result

def test_basic_operations():
    """Test basic ML operations to ensure packages work correctly"""
    try:
        import numpy as np
        import pandas as pd
        from sklearn.cluster import KMeans
        from scipy import stats
        import joblib
        
        # Test basic numpy operations
        arr = np.array([1, 2, 3, 4, 5])
        mean_val = np.mean(arr)
        
        # Test basic pandas operations
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        corr = df.corr()
        
        # Test basic sklearn clustering
        X = np.array([[1, 2], [1, 4], [1, 0], [10, 2], [10, 4], [10, 0]])
        kmeans = KMeans(n_clusters=2, random_state=0, n_init=10).fit(X)
        
        # Test basic scipy stats
        stat, p_value = stats.ttest_1samp([1, 2, 3, 4, 5], 3)
        
        return {
            'success': True,
            'operations_tested': ['numpy', 'pandas', 'sklearn', 'scipy', 'joblib'],
            'test_results': {
                'numpy_mean': float(mean_val),
                'pandas_corr_shape': list(corr.shape),
                'sklearn_clusters': int(kmeans.n_clusters),
                'scipy_pvalue': float(p_value)
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }

if __name__ == '__main__':
    # Test dependency availability
    deps_result = test_clustering_dependencies()
    
    # Test basic operations if all dependencies are available
    ops_result = None
    if deps_result['success']:
        ops_result = test_basic_operations()
    
    final_result = {
        'dependency_check': deps_result,
        'operations_check': ops_result,
        'overall_success': deps_result['success'] and (ops_result['success'] if ops_result else False),
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }
    
    print(json.dumps(final_result, indent=2))