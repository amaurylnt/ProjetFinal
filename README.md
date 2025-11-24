Projet réalisé dans le cadre du module *Conteneurisation & Orchestration*.

Ce dépôt contient un **proof of concept** destiné à moderniser la plateforme interne de l’entreprise DataPress, actuellement monolithique et hébergée sur un seul serveur.  

L’objectif est de démontrer comment **Docker**, **Docker Compose** et **Kubernetes** permettent d’obtenir une architecture plus fiable, plus modulable et plus simple à exploiter.

---

#  1. Contexte du projet

DataPress est une PME qui fournit une plateforme interne d’indicateurs marketing (PDF, CSV, dashboards, synthèses…).  
Aujourd’hui :

- Front, API, base de données et cronjobs tournent sur **un seul serveur**.
- Une panne = **arrêt total du service**.
- Impossible de tester une nouvelle version sans impacter les utilisateurs.
- Documentation faible et déploiements difficiles.
- Infrastructure vieillissante → besoin de modernisation.

 Le DSI souhaite un **POC limité**, non productif, qui prouve :

- séparation **front / API**,  
- conteneurisation propre,  
- déploiement sur un cluster Kubernetes de recette,  
- bonne structuration du dépôt,  
- un début de CI/CD minimal,  
- documentation claire et exploitable.

Les attentes fonctionnelles minimales :

- **Front simple** affichant “DataPress – POC” + version.
- **API** minimaliste avec :
  - `/` → JSON
  - `/health` → probes Kubernetes
- Mode dev : **Docker Compose**
- Mode recette : **Kubernetes**
- Objets Kubernetes : namespace, Deployments, Services, ConfigMap, Secret, probes.
- Exploitabilité : commandes `kubectl`, events, logs, redémarrage automatique.
- Documentation + présentation orientée “client”.

---

#  2. Architecture proposée

## 2.1 Vue d’ensemble

Le POC repose sur une architecture **découplée** :

                   +------------------------+
                   |        FRONT           |
                   |   (Flask + Gunicorn)   |
                   +-----------+------------+
                               |
                               | HTTP (API_BASE_URL)
                               v
                   +------------------------+
                   |         API            |
                   |   (Flask + Gunicorn)   |
                   +------------------------+


Dev mode → Docker Compose
Recette → Kubernetes (namespace dédié)

---

## 2.2 Architecture – Mode Développement (Docker Compose)
En mode développement, l’architecture repose sur deux conteneurs Docker :
```
docker-compose.yml
│
├── front (Flask + Gunicorn)
│     ↳ Port exposé : 8080
│     ↳ Appelle l’API via http://api:8000
│
└── api (Flask + Gunicorn)
      ↳ Port exposé : 8000
      ↳ Endpoints : "/", "/health"
```
Caractéristiques :

- Pas besoin d’installer Python en local.
- Réseau Docker interne permettant de joindre l’API par http://api:8000.
- Utilisation de Dockerfile multi-stage + utilisateur non-root.

Objectifs atteints :

- environnement reproductible,
- isolation des services,
- réseau Docker interne,
- aucun besoin d’installer Python localement.

---

## 2.3 Architecture – Mode Recette (Kubernetes)

Namespace : **datapress-recette**

### Objets déployés :

| Objet | Rôle |
|-------|------|
| **Deployment API (2 replicas)** | haute disponibilité, probes |
| **Service API (ClusterIP)** | communication interne |
| **Deployment Front (1 replica)** | exposition du front |
| **Service Front (NodePort)** | accès externe (local) |
| **ConfigMap** | paramètres non sensibles |
| **Secret** | paramètre sensible API |
| **Probes** (`/health`) | readiness & liveness |
| **Requests/Limits mémoire** | protection du cluster |

### Workflow des requêtes :

Navigateur → NodePort → Front (pod)
Front → ClusterIP → API (pod)
API → répond JSON

Les deux réplicas d’API sont load-balancés automatiquement par le Service Kubernetes.

---

#  3. Containerisation & Mode Développement

## 3.1 API (Flask)

Endpoints :

- `/` → JSON avec timestamp, service, variables d’environnement
- `/health` → utilisé par les probes Kubernetes

Dockerfile :  
✔ Multi-stage  
✔ Runtime léger  
✔ User non-root  
✔ Gunicorn en production

## 3.2 Front (Flask)

Affichage :

- titre : **“DataPress – POC”**
- version : variable d’environnement (`FRONT_VERSION`)
- test API : appel interne vers `/health`

Dockerfile :  
✔ Multi-stage  
✔ User non-root  
✔ Gunicorn

## 3.3 Docker Compose

Lancement :
```
docker compose up --build
```

Accès :

Front → http://localhost:8080

API → http://localhost:8000

Tests :
```
curl http://localhost:8000/health
curl http://localhost:8080
```

# 4. Déploiement Kubernetes – Mode Recette

## 4.1 Application des manifestes
```
kubectl apply -f k8s/namespace.yaml
kubectl apply -n datapress-recette -f k8s/configmap.yaml
kubectl apply -n datapress-recette -f k8s/secret.yaml
kubectl apply -n datapress-recette -f k8s/api-deployment.yaml
kubectl apply -n datapress-recette -f k8s/api-service.yaml
kubectl apply -n datapress-recette -f k8s/front-deployment.yaml
kubectl apply -n datapress-recette -f k8s/front-service.yaml
```

## 4.2 Vérification

Pods / Services / Deployments

```
kubectl get all -n datapress-recette
```

Attendus :

2 pods API → Running

1 pod Front → Running

Services front + API → OK

Events
```
kubectl get events -n datapress-recette --sort-by=.lastTimestamp
```
Logs
```
kubectl logs deploy/datapress-api -n datapress-recette
kubectl logs deploy/datapress-front -n datapress-recette
```
Test API via port-forward
```
kubectl port-forward svc/datapress-api 8000:80 -n datapress-recette
```
http://localhost:8000/health

Test Front

Via NodePort
```
http://localhost:30080
```
Ou port-forward
```
kubectl port-forward svc/datapress-front 8080:80 -n datapress-recette
```
http://localhost:8080

# 5. Guide d’exploitation

Démarrage (dev)
```
docker compose up --build
```
Arrêt
```
docker compose down
```
Déploiement Kubernetes
```
kubectl apply -f k8s/
```
Mise à jour d’un composant
```
kubectl rollout restart deploy/datapress-api -n datapress-recette
```
Debug
```
kubectl logs <pod> -n datapress-recette
kubectl describe pod <pod> -n datapress-recette
kubectl get events -n datapress-recette --sort-by=.lastTimestamp
```
Vérifier la haute disponibilité
```
kubectl delete pod <pod_api> -n datapress-recette
kubectl get pods -n datapress-recette
```
un nouveau pod API doit se recréer automatiquement.

# 6. Difficultés rencontrées
- GitHub Actions non détecté : le dossier .github/workflows n’était pas à la racine du dépôt → GitHub ne voyait aucun workflow.

- Build CI échoué : échec du build de l’image API lors des tests (erreur Dockerfile).

- Résolution des DNS Docker interne : api:8000 fonctionne dans Docker/K8s mais pas dans le navigateur → nécessité d’ajouter API_PUBLIC_URL.

- Port-forward obligatoire pour tester l’API en ClusterIP.

- Organisation du projet : nécessité de structurer proprement les dossiers pour Docker, Kubernetes et la documentation.

- Ces difficultés ont été corrigées / documentées dans ce README.

# 7. Pistes d’amélioration
Pour une future version du projet, il serait pertinent d’ajouter :

- Ingress + Cert-Manager + TLS

- Monitoring complet : Prometheus, Grafana, Loki

- Traçage distribué : Jaeger

- HPA (Horizontal Pod Autoscaler) basé sur la charge

- Tests unitaires Python

- Pipeline CI/CD complète :

  - build

  - tests

  - push dans un registry

  - déploiement auto sur cluster de recette

- Base de données conteneurisée

- NetworkPolicies pour renforcer la sécurité réseau K8s

- Images optimisées (distroless / alpine)

# 8. Conclusion
Ce POC démontre la faisabilité d’une architecture moderne pour DataPress :

- séparation front / API,

- conteneurisation propre,

- déploiement Kubernetes complet,

- configuration via ConfigMap & Secret,

- probes, ressources, haute disponibilité,

- documentation claire et exploitable.

Il constitue une base solide pour construire une infrastructure plus robuste, scalable et sécurisée.
