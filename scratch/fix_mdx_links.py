import os

replacements = {
    'docs/architecture.mdx': [
        ('/fonctionnalites/espace-gestionnaire', '/docs/fonctionnalites/espace-gestionnaire')
    ],
    'docs/installation/configuration.mdx': [
        ('/installation/prerequis', '/docs/installation/prerequis'),
        ('/installation/base-de-donnees', '/docs/installation/base-de-donnees')
    ],
    'docs/technique/supervision-observabilite.mdx': [
        ('/technique/devops-exploitation', '/docs/technique/devops-exploitation')
    ]
}

for filepath, pairs in replacements.items():
    full_path = os.path.join(r'c:/Users/nito1/Desktop/Projet_Final', filepath)
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in pairs:
        content = content.replace(old, new)
    with open(full_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print('Updated links in:', filepath)
