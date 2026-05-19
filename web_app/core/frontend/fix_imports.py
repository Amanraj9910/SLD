import os
import re
import glob

files = glob.glob('src/**/*.tsx', recursive=True) + glob.glob('src/**/*.ts', recursive=True)
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
    except UnicodeDecodeError:
        with open(f, 'r', encoding='utf-16') as file:
            content = file.read()
    
    # Replace from '... .tsx' with from '...'
    new_content = re.sub(r'(import .*? from\s+[\'"])(.*?)\.tsx?([\'"])', r'\1\2\3', content)
    
    if new_content != content:
        # Save back with same encoding
        try:
            with open(f, 'r', encoding='utf-8') as file:
                file.read()
            encoding = 'utf-8'
        except UnicodeDecodeError:
            encoding = 'utf-16'
            
        with open(f, 'w', encoding=encoding) as file:
            file.write(new_content)
        print(f"Updated {f}")
