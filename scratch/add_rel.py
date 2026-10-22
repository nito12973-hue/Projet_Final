import os, re

files = [
    'Plateform_medicale/templates/administrateur/supervision_systeme.html',
    'Plateform_medicale/templates/assure/mes_prises_en_charge.html',
    'Plateform_medicale/templates/assure/modifier_ayant_droit.html',
    'Plateform_medicale/templates/commun/liste_patients.html',
    'Plateform_medicale/templates/emails/activation_compte.html',
    'Plateform_medicale/templates/gestionnaire/liste_prises_en_charge.html',
    'Plateform_medicale/templates/gestionnaire/modifier_prise_en_charge.html',
    'Plateform_medicale/templates/gestionnaire/voir_bon_prise_en_charge.html'
]

for filepath in files:
    full_path = os.path.join(r'c:/Users/nito1/Desktop/Projet_Final', filepath)
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    def repl(match):
        tag = match.group(0)
        if 'rel=' not in tag:
            if 'target="_blank"' in tag:
                return tag.replace('target="_blank"', 'target="_blank" rel="noopener noreferrer"')
            elif "target='_blank'" in tag:
                return tag.replace("target='_blank'", "target='_blank' rel='noopener noreferrer'")
        return tag

    new_content = re.sub(r'<a\b[^>]*target=[\"\']_blank[\"\'][^>]*>', repl, content)
    if new_content != content:
        with open(full_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        print('Updated rel=noopener on:', filepath)
    else:
        print('No changes needed for:', filepath)
