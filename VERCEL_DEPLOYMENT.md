# Déploiement sur Vercel

Ce guide explique comment déployer l'application Django Plateforme Médicale sur Vercel.

## Prérequis

- Un compte Vercel (https://vercel.com)
- Un repository Git (GitHub, GitLab, ou Bitbucket)
- Une base de données PostgreSQL (recommandée pour la production)

## Variables d'environnement requises

Configurez ces variables dans les settings de votre projet Vercel:

### Sécurité
- `SECRET_KEY`: Clé secrète Django (générez-en une forte et unique)
- `DEBUG`: `False` (obligatoire en production)
- `ALLOWED_HOSTS`: Domaine Vercel (ex: `votre-app.vercel.app`) et domaines personnalisés

### Base de données
- `DB_ENGINE`: `postgresql` (recommandé) ou `sqlite`
- `DB_NAME`: Nom de la base de données
- `DB_USER`: Utilisateur PostgreSQL
- `DB_PASSWORD`: Mot de passe PostgreSQL
- `DB_HOST`: Hôte PostgreSQL (ex: `aws-0-region.pooler.supabase.com`)
- `DB_PORT`: Port PostgreSQL (défaut: `5432`)

### Autre
- `DJANGO_SETTINGS_MODULE`: `config.settings` (déjà configuré dans vercel.json)

## Étapes de déploiement

### 1. Préparer le repository

Assurez-vous que votre code est sur un repository Git distant:

```bash
git add .
git commit -m "Préparation déploiement Vercel"
git push origin main
```

### 2. Importer sur Vercel

1. Connectez-vous sur https://vercel.com
2. Cliquez sur "Add New Project"
3. Importez votre repository Git
4. Vercel détectera automatiquement que c'est un projet Python grâce à `vercel.json`

### 3. Configurer les variables d'environnement

Dans les settings du projet Vercel:
1. Allez dans "Settings" → "Environment Variables"
2. Ajoutez toutes les variables listées ci-dessus
3. Sélectionnez les environnements (Production, Preview, Development)

### 4. Déployer

Cliquez sur "Deploy". Vercel va:
- Installer les dépendances depuis `requirements.txt`
- Exécuter `python manage.py collectstatic` automatiquement
- Démarrer l'application Django

### 5. Exécuter les migrations

Après le premier déploiement, vous devez exécuter les migrations de la base de données:

Option 1: Via Vercel CLI
```bash
vercel env pull .env.local
python manage.py migrate
```

Option 2: Via la console Vercel (si disponible)
- Utilisez la fonctionnalité "Shell" de Vercel pour exécuter les commandes

## Configuration de la base de données

### Option recommandée: Supabase (PostgreSQL gratuit)

1. Créez un compte sur https://supabase.com
2. Créez un nouveau projet
3. Récupérez les informations de connexion dans Settings → Database
4. Configurez les variables d'environnement Vercel avec ces valeurs

### Option alternative: Vercel Postgres

1. Dans votre projet Vercel, allez dans "Storage"
2. Créez une base de données Postgres
3. Vercel configurera automatiquement les variables d'environnement

## Domaine personnalisé (optionnel)

1. Allez dans "Settings" → "Domains"
2. Ajoutez votre domaine personnalisé
3. Mettez à jour `ALLOWED_HOSTS` dans les variables d'environnement

## Dépannage

### Erreur 500 sur les pages
- Vérifiez que `DEBUG=False` en production
- Vérifiez les logs dans l'onglet "Logs" de Vercel
- Assurez-vous que `ALLOWED_HOSTS` contient le domaine Vercel

### Fichiers statiques ne s'affichent pas
- Whitenoise est configuré pour gérer les fichiers statiques
- Vérifiez que `collectstatic` s'est exécuté correctement lors du déploiement

### Problèmes de base de données
- Vérifiez que les variables d'environnement DB_* sont correctes
- Assurez-vous que la base de données est accessible depuis Vercel
- Exécutez les migrations si nécessaire

## Déploiements automatiques

Chaque push sur votre repository déclenchera automatiquement un nouveau déploiement sur Vercel. Pour désactiver:
- Allez dans "Settings" → "Git"
- Désactivez "Automatic Deployments"
