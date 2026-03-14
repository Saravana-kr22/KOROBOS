## **KOROBOS – Infrastructure & Deployment Specification**

This document provides a comprehensive overview of the **KOROBOS Infrastructure**, detailing the cloud-native environment, network topology, and resource management strategies required to support an enterprise-level "Second Brain" platform.

### ---

**1\. Infrastructure Architecture Overview**

KOROBOS utilizes a **Cloud-Native Microservices Architecture**. The system is designed to be highly available, scalable, and secure, leveraging container orchestration and distributed data layers.

#### **1.1 Core Infrastructure Components**

* **API Gateway**: Acts as the single entry point for all client requests, handling routing, rate limiting, and SSL termination.  
* **Kubernetes (K8s) Cluster**: The primary orchestration layer where all microservices (Auth, Notes, Habit, etc.) reside as containerized pods.  
* **Database Cluster**: High-availability PostgreSQL cluster for relational data and structured databases.  
* **Cache Layer**: Redis cluster used for session management, dashboard widget caching, and real-time state.  
* **Object Storage**: S3-compatible storage for markdown file backups, user-uploaded images, and static assets.

### ---

**2\. Network & Security Topology**

The infrastructure is segmented into public and private subnets to ensure the principle of least privilege.

* **Public Subnet**: Contains the Load Balancer and Bastion Host.  
* **Private Subnet**: Contains the Kubernetes nodes, PostgreSQL instances, and Redis cache.  
* **Traffic Flow**:  
  1. User traffic hits the **Cloud Load Balancer** via HTTPS.  
  2. Requests are routed to the **API Gateway** inside the K8s cluster.  
  3. Internal service-to-service communication is managed via a **Service Mesh** (e.g., Istio) for encrypted mTLS communication.

### ---

**3\. Scaling & Resiliency Strategy**

To meet the target of **100k concurrent users**, KOROBOS employs multiple scaling vectors:

| Component | Scaling Strategy | Trigger |
| :---- | :---- | :---- |
| **Microservices** | Horizontal Pod Autoscaling (HPA) | CPU \> 70% or Memory \> 80% |
| **Worker Nodes** | Cluster Autoscaler | Pending pods due to resource exhaustion |
| **Databases** | Read Replicas | High read latency on the primary node |
| **Search Engine** | Sharding & Clustering | Large index size or high query latency |

### ---

**4\. Storage & Data Persistence**

KOROBOS utilizes a polyglot persistence approach to handle diverse data types:

* **Relational Data (PostgreSQL)**: Handles Users, Notes metadata, Habit logs, and Learning sessions.  
* **Unstructured Data (Object Storage)**: Stores raw markdown files and media embeds.  
* **Search Index (Meilisearch/Elasticsearch)**: Stores inverted indices for full-text search and tag filtering.  
* **Graph Data**: Managed via specialized indices within PostgreSQL or a dedicated Graph Database for the Knowledge Graph visualization.

### ---

**5\. Deployment & DevOps**

The deployment pipeline follows a strict **GitOps** methodology.

* **Continuous Integration**: GitHub Actions runs unit tests, linting, and security scans on every PR.  
* **Continuous Deployment**: Successful builds trigger an update to the Kubernetes manifests via **ArgoCD** or **Helm charts**.  
* **Environment Strategy**:  
  * **Development**: Ephemeral environments for feature testing.  
  * **Staging**: A mirror of production for final QA and load testing.  
  * **Production**: Multi-region deployment for international low-latency access.

### ---

**6\. Disaster Recovery & Backup**

* **RPO (Recovery Point Objective)**: 15 minutes.  
* **RTO (Recovery Time Objective)**: 30 minutes.  
* **Backup Schedule**:  
  * **Database**: Automated daily snapshots \+ continuous WAL (Write-Ahead Logging) archiving.  
  * **Configuration**: All K8s manifests and Terraform code stored in version control.

---
