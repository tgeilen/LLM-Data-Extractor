#!/usr/bin/env python3
"""
Code Analysis Tool for finding duplicates, unused code, and dependencies
"""

import os
import ast
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
import difflib

class CodeAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.python_files = []
        self.notebook_files = []
        self.functions = defaultdict(list)  # function_name -> [(file, code)]
        self.classes = defaultdict(list)    # class_name -> [(file, code)]
        self.imports = defaultdict(set)     # file -> set of imports
        self.function_calls = defaultdict(set)  # file -> set of function calls
        
    def scan_files(self):
        """Scan all Python files in the project (excluding notebooks)"""
        for py_file in self.project_root.rglob("*.py"):
            if 'venv' not in str(py_file) and '__pycache__' not in str(py_file):
                self.python_files.append(py_file)
        
        for nb_file in self.project_root.rglob("*.ipynb"):
            self.notebook_files.append(nb_file)
        
        print(f"Found {len(self.python_files)} Python files")
        print(f"Found {len(self.notebook_files)} notebook files (analysis only - not checked for duplicates)")
    
    def extract_functions_and_classes(self, file_path: Path):
        """Extract function and class definitions from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_code = ast.get_source_segment(content, node)
                    if func_code:
                        self.functions[node.name].append((str(file_path), func_code))
                
                elif isinstance(node, ast.ClassDef):
                    class_code = ast.get_source_segment(content, node)
                    if class_code:
                        self.classes[node.name].append((str(file_path), class_code))
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.imports[str(file_path)].add(alias.name)
                    else:  # ImportFrom
                        module = node.module or ""
                        for alias in node.names:
                            self.imports[str(file_path)].add(f"{module}.{alias.name}")
                
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        self.function_calls[str(file_path)].add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        self.function_calls[str(file_path)].add(node.func.attr)
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    def analyze_notebooks(self):
        """Analyze notebook files for code patterns"""
        notebook_functions = {}
        
        for nb_file in self.notebook_files:
            try:
                with open(nb_file, 'r', encoding='utf-8') as f:
                    nb_content = json.load(f)
                
                functions_in_nb = []
                
                for cell in nb_content.get('cells', []):
                    if cell.get('cell_type') == 'code':
                        source = ''.join(cell.get('source', []))
                        
                        # Extract function definitions
                        func_matches = re.findall(r'def\s+(\w+)\s*\(', source)
                        functions_in_nb.extend(func_matches)
                
                notebook_functions[str(nb_file)] = functions_in_nb
                
            except Exception as e:
                print(f"Error processing notebook {nb_file}: {e}")
        
        return notebook_functions
    
    def find_duplicate_functions(self, similarity_threshold=0.8):
        """Find duplicate or very similar functions"""
        duplicates = []
        
        for func_name, implementations in self.functions.items():
            if len(implementations) > 1:
                # Check for exact duplicates
                for i, (file1, code1) in enumerate(implementations):
                    for j, (file2, code2) in enumerate(implementations[i+1:], i+1):
                        similarity = difflib.SequenceMatcher(None, code1, code2).ratio()
                        
                        if similarity > similarity_threshold:
                            duplicates.append({
                                'function': func_name,
                                'file1': file1,
                                'file2': file2,
                                'similarity': similarity,
                                'code1_lines': len(code1.split('\n')),
                                'code2_lines': len(code2.split('\n'))
                            })
        
        return duplicates
    
    def find_unused_files(self):
        """Find files that might be unused"""
        # Files that are likely main entry points (shouldn't be marked unused)
        entry_points = {
            'run_tests.py', 'arxiv_downloader.py',
            'ocr_analysis.py', 'discovery_pipeline.py'
        }
        
        imported_modules = set()
        
        # Collect all imports
        for file_path, imports in self.imports.items():
            for imp in imports:
                # Extract module name
                module_parts = imp.split('.')
                if module_parts[0] not in ['os', 'sys', 'json', 'time', 'requests', 'numpy', 'pandas']:
                    imported_modules.add(module_parts[0])
        
        unused_files = []
        
        for py_file in self.python_files:
            file_stem = py_file.stem
            relative_path = py_file.relative_to(self.project_root)
            
            # Skip if it's an entry point
            if py_file.name in entry_points:
                continue
            
            # Skip test files (they're used for testing)
            if 'test' in py_file.name.lower():
                continue
            
            # Check if this file is imported anywhere
            is_imported = any(
                file_stem in imp or str(relative_path).replace('/', '.').replace('.py', '') in imp
                for imp in imported_modules
            )
            
            if not is_imported:
                unused_files.append(str(py_file))
        
        return unused_files
    
    def find_unused_functions(self):
        """Find functions that are defined but never called"""
        all_called_functions = set()
        
        # Collect all function calls
        for file_path, calls in self.function_calls.items():
            all_called_functions.update(calls)
        
        unused_functions = []
        
        for func_name, implementations in self.functions.items():
            # Skip special methods and common entry points
            if func_name.startswith('_') or func_name in ['main', 'run', 'setup', 'test']:
                continue
            
            if func_name not in all_called_functions:
                unused_functions.append({
                    'function': func_name,
                    'files': [impl[0] for impl in implementations]
                })
        
        return unused_functions
    
    def analyze_file_dependencies(self):
        """Analyze which files depend on which other files"""
        dependencies = defaultdict(set)
        
        for file_path, imports in self.imports.items():
            file_name = Path(file_path).name
            
            for imp in imports:
                # Check if this import refers to another file in the project
                for py_file in self.python_files:
                    if py_file.stem in imp or py_file.name.replace('.py', '') in imp:
                        dependencies[file_name].add(py_file.name)
        
        return dict(dependencies)
    
    def generate_report(self):
        """Generate a comprehensive analysis report"""
        print("=" * 80)
        print("CODE ANALYSIS REPORT")
        print("=" * 80)
        
        # Scan all files
        self.scan_files()
        
        # Analyze Python files
        for py_file in self.python_files:
            self.extract_functions_and_classes(py_file)
        
        # Find duplicates
        print("\n1. DUPLICATE FUNCTIONS:")
        print("-" * 40)
        duplicates = self.find_duplicate_functions()
        
        if duplicates:
            for dup in duplicates[:10]:  # Show top 10
                print(f"Function '{dup['function']}' ({dup['similarity']:.1%} similar):")
                print(f"  - {Path(dup['file1']).name} ({dup['code1_lines']} lines)")
                print(f"  - {Path(dup['file2']).name} ({dup['code2_lines']} lines)")
                print()
        else:
            print("No significant duplicates found!")
        
        # Find unused files
        print("\n2. POTENTIALLY UNUSED FILES:")
        print("-" * 40)
        unused_files = self.find_unused_files()
        
        if unused_files:
            for file_path in unused_files[:15]:  # Show top 15
                print(f"  - {Path(file_path).name}")
        else:
            print("All files appear to be in use!")
        
        # Find unused functions
        print("\n3. POTENTIALLY UNUSED FUNCTIONS:")
        print("-" * 40)
        unused_functions = self.find_unused_functions()
        
        if unused_functions:
            for func in unused_functions[:15]:  # Show top 15
                files = [Path(f).name for f in func['files']]
                print(f"  - {func['function']} (in {', '.join(files)})")
        else:
            print("All functions appear to be in use!")
        
        # Analyze notebooks (summary only)
        print("\n4. NOTEBOOK SUMMARY:")
        print("-" * 40)
        notebook_functions = self.analyze_notebooks()
        
        print("Notebooks are orchestration layers that call .py functions:")
        for nb_file, functions in notebook_functions.items():
            nb_name = Path(nb_file).name
            print(f"  - {nb_name}: {len(functions)} functions (orchestration only)")
        
        print("\n Note: Notebooks excluded from duplication analysis as they typically")
        print("   just call functions from .py files for analysis and visualization.")
        
        # File dependencies
        print("\n5. FILE DEPENDENCIES:")
        print("-" * 40)
        dependencies = self.analyze_file_dependencies()
        
        for file, deps in list(dependencies.items())[:10]:
            if deps:
                print(f"{file} depends on: {', '.join(list(deps)[:3])}")
        
        # Summary statistics
        print("\n6. SUMMARY STATISTICS:")
        print("-" * 40)
        print(f"Total Python files: {len(self.python_files)}")
        print(f"Total notebook files: {len(self.notebook_files)}")
        print(f"Total functions found: {len(self.functions)}")
        print(f"Total classes found: {len(self.classes)}")
        print(f"Duplicate functions: {len(duplicates)}")
        print(f"Potentially unused files: {len(unused_files)}")
        print(f"Potentially unused functions: {len(unused_functions)}")
        
        return {
            'duplicates': duplicates,
            'unused_files': unused_files,
            'unused_functions': unused_functions,
            'notebook_functions': notebook_functions,
            'dependencies': dependencies
        }

if __name__ == "__main__":
    analyzer = CodeAnalyzer(".")
    results = analyzer.generate_report()

