import os

directories = ['admin', 'customer']

for d in directories:
    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith('.html') or file.endswith('.js'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Temporarily replace correctly formed ones to prevent double-replacements
                new_content = content.replace('http://localhost:8000/api', 'TMP_API_URL')
                
                # Replace the old base URL with the new API-based one
                new_content = new_content.replace('http://localhost:8000', 'http://localhost:8000/api')
                
                # Restore the temporarily replaced strings
                new_content = new_content.replace('TMP_API_URL', 'http://localhost:8000/api')
                
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated {path}")
