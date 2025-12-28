# 🚀 Guide de Démarrage Rapide - MC INT

## ⚡ Démarrage 30 secondes

### Option 1: Docker (Recommandé)
```bash
# À la racine du projet
docker-compose up -d

# L'app sera disponible à http://localhost:4200
```

### Option 2: Manuel

#### Terminal 1 - Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Frontend
```bash
cd frontend
npm install
npm start
```

Puis ouvrez http://localhost:4200

---

## 📖 Workflow utilisateur

### Étape 1: Se connecter
1. Aller à http://localhost:4200
2. Entrer votre email
3. Cliquer "Recevoir le code"

### Étape 2: Vérifier le code
1. Consulter le code dans vos emails (dev: console backend)
2. Entrer les 6 chiffres
3. Les champs se remplissent automatiquement

### Étape 3: Réserver
*(Si vous êtes cotisant BDE)*
1. Sélectionner date et heure
2. Indiquer si vous habitez en résidence
3. Entrer adresse (résidence ou externe)
4. Cliquer "Continuer vers le paiement"

### Étape 4: Payer
1. Une réservation apparaît au dashboard
2. Cliquer le bouton "Payer"
3. Être redirigé vers HelloAsso

### Étape 5: Confirmation
1. Après paiement, la réservation passe à "paid"
2. Confirmation par email
3. Prêt à être livré!

---

## 🧪 Test en développement

### Simulations d'emails
Le backend local affiche les codes dans la console:
```
Verification code for user@example.com: 123456
```

Copiez ce code et collez-le dans l'interface de vérification.

### Bypass du check BDE
En développement, commentez la vérification BDE dans `backend/src/auth/service.py`:
```python
# user.is_cotisant_bde = await verify_with_bde(email)
user.is_cotisant_bde = True  # Force true pour tests
```

### Test du paiement
HelloAsso en dev utilise l'API sandbox - les vrais paiements ne sont pas débités.

---

## 🎨 Personnalisation du design

### Changer les couleurs
Éditez `frontend/src/app/pages/*/**.component.scss`:
```scss
$primary-color: #dc143c;     // Rouge
$secondary-color: #ffc72c;   // Jaune
$accent-color: #ff6b35;      // Orange
```

### Modifier les animations
Dans `frontend/src/app/pages/*/**.component.scss`:
```scss
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
```

### Ajouter vos logos
1. Placez les fichiers dans `frontend/src/assets/`
2. Référencez dans le template:
```html
<img src="assets/logo.png" alt="Logo">
```

---

## 🐛 Dépannage courant

### "Cannot GET /api"
Le backend n'est pas lancé. Vérifiez:
```bash
curl http://localhost:8000/api
# Doit retourner: {"status": "ok", "message": "MC INT API running"}
```

### CORS error
Assurez-vous que le frontend est sur le port 4200 et que CORS est configuré dans `backend/src/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    ...
)
```

### Code non reçu
Vérifiez l'SMTP configuré dans `.env`:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Page blanche après login
Vérifiez la console du navigateur (F12 → Console) pour les erreurs JavaScript.

---

## 📱 Tests multiappareils

### Depuis votre machine (localhost)
```
http://localhost:4200
```

### Depuis téléphone (même réseau)
```bash
# Obtenez votre IP
ip addr show

# Puis depuis téléphone:
http://<votre-ip>:4200
```

### Production
```bash
# Build
npm run build

# Servir depuis le dossier dist/frontend/
python -m http.server 8000 --directory dist/frontend/
```

---

## 📊 Monitoring

### Logs backend
```bash
# Activez les logs détaillés
export LOG_LEVEL=DEBUG

# Puis relancez:
uvicorn src.main:app --reload
```

### Logs frontend (DevTools)
- Ouvrez F12 dans le navigateur
- Allez à l'onglet "Console"
- Tous les logs Angular s'affichent ici

### Base de données
```bash
# Connexion directe PostgreSQL
psql postgresql://user:password@localhost/mcint

# Voir les tables
\dt

# Voir les utilisateurs
SELECT * FROM user;

# Voir les réservations  
SELECT * FROM reservation;
```

---

## 🔒 Sécurité en développement

⚠️ **Ne JAMAIS utiliser en production:**
- `uvicorn` en dev (utiliser gunicorn)
- Clés secrètes par défaut
- CORS permissifs
- Logs en DEBUG

---

## 📦 Déploiement production

### Avec Docker Compose
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Variables d'environnement
Créez un fichier `.env.prod`:
```
FRONTEND_URL=https://yourdomain.com
DATABASE_URL=postgresql://user:pass@db-host/mcint
JWT_SECRET_KEY=your-very-long-secret-key-here
# ... autres variables
```

### SSL/HTTPS
Utilisez Nginx comme reverse proxy:
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /api {
        proxy_pass http://backend:8000;
    }
    
    location / {
        proxy_pass http://frontend:80;
    }
}
```

---

## ✅ Checklist avant production

- [ ] Variables d'environnement configurées
- [ ] Base de données PostgreSQL prête
- [ ] SMTP configuré (Gmail App Password, etc.)
- [ ] HelloAsso API key en place
- [ ] BDE API connectée
- [ ] SSL/HTTPS configuré
- [ ] Firewall configuré (ports 80, 443)
- [ ] Backups base de données
- [ ] Monitoring & alertes en place
- [ ] Logs centralisés

---

## 📞 Support rapide

**Page blanche?** → Vérifiez les erreurs F12 → Console  
**Pas de code d'email?** → Vérifiez .env SMTP + console backend  
**CORS error?** → Vérifiez URL backend + configuration CORS  
**Base de données?** → Vérifiez DATABASE_URL + migrations Alembic  

---

Bon développement! 🚀
