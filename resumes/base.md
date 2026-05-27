# PARIKSHIT DABAS
+91 95603 07106 | parikshit.p2002@gmail.com | Delhi, India | linkedin.com/in/parikshit-dabas | github.com/parikshit-dabas

## SUMMARY

Software Engineer with 2+ years at Arcesium building **backend systems**, **data platforms**, and **cloud-native infrastructure** for institutional clients. Strong across **Java/Kotlin**, **Spring Boot**, **Kubernetes**, **AWS**, **Spark**, **Delta Lake**, and observability. Experienced in owning production services from design and implementation through deployment, on-call support, reliability work, and client-facing platform features.

## EXPERIENCE

**Arcesium — Software Engineer** | Gurugram, India | Jun 2024 – Present
- Built a **multi-tenant data ingestion platform** in **Java/Kotlin** and **Spring Boot** for securely moving client data from external **SFTP/HTTP sources** into an internal data platform, with authentication, source-specific handling, schema validation, and tenant isolation.
- Developed and maintained a **client-facing schema management service** that exposed a single **self-service API** for creating and evolving schemas across **Delta Lake**, **Snowflake**, and **PostgreSQL**, replacing manual table creation and reducing onboarding dependency on support teams.
- Built **Housekeeper**, an **Argo Workflows** optimization service for **Delta Lake** tables, to identify tables worth compacting/Z-ORDERing and improve data skipping, scan efficiency, and downstream query performance under constrained compute budgets.
- Engineered **containerized Spark workloads on Kubernetes**, orchestrated through **AWS Lambda**, **S3**, and **Argo Workflows**; tuned pod specifications, resource requests, retries, and workflow templates to improve reliability of batch data processing jobs.
- Owned a **customer-facing cost and observability platform** for multi-tenant Kubernetes workloads, correlating CPU/memory usage, **Spark job cost**, query performance, and data scanned to support **billing**, chargeback, debugging, and platform optimization.
- Improved **production observability** and release workflows by building **Grafana/Prometheus/Datadog dashboards**, tightening alerting, restructuring **CI/CD pipelines**, and supporting **Terraform/IAM** changes across environments.
- Built **internal AI agents** for release engineering and developer workflows using **MCP**, **Anthropic API**, and **AWS Bedrock**, integrating with GitLab, Jira, and Slack to automate release checks, status lookups, and routine engineering actions.
- Helped adapt backend services to **cell-based AWS architecture**, reducing blast radius and improving reliability through cell-aware service behavior, deployment changes, **disaster recovery exercises**, and pod motion validation.
- Drove **product-led onboarding automation** for new client setup, reducing manual provisioning from roughly **3 weeks to 3-4 hours** by automating cross-application setup flows and Kubernetes namespace deployment through internal infrastructure tooling.
- Led **Spring Boot upgrades** and backend refactors across platform services, resolving dependency conflicts, compatibility issues, and legacy provisioning paths while keeping production systems stable.

**Arcesium — Software Engineer** | Gurugram, India | Jan 2024 – Jun 2024
- Built and deployed a **Spark resource recommendation service** that generated driver/executor CPU and memory configurations from **Prometheus metrics** and Spark event log analysis to reduce **OOM failures** and improve cluster cost efficiency.
- Designed the recommendation framework to support **plug-and-play tuning algorithms**, including statistical heuristics and optimization-based approaches, while remaining **query-agnostic** and usable across different Spark workloads.
- Served resource recommendations through a **backend API** consumed by downstream job schedulers, reducing **Spark job failure rates by approximately 15%** under variable workload patterns.

**Arcesium — Software Engineer** | Gurugram, India | May 2023 – Jul 2023
- Built **Java/Spring backend modules** for a client reporting workflow, including a **low-latency preview path** that generated report reviews from live user input without triggering the heavier server-side report generation flow.
- Implemented **request throttling** and **memory profiling** improvements to protect resource-intensive reporting paths and improve backend reliability under interactive usage.

## PROJECTS

**Container Runtime (C)** | C, Linux Namespaces, cgroups
- Built a lightweight **container runtime in C** using **Linux namespaces** and **cgroups** to launch isolated processes with PID, mount, network, filesystem, and resource isolation primitives similar to a minimal Docker runtime.

**Indoor Navigation System** | Python, TensorFlow, OpenCV, YOLOv5, AWS IoT
- Built a **real-time indoor navigation system** for visually impaired users with camera-based scene understanding and audio step-by-step guidance.
- Applied transfer learning with **ResNet50/VGG16** and **YOLOv5**, integrated **AWS IoT** for sensor data streaming, and deployed a Python inference pipeline optimized for low-latency feedback.

## EDUCATION

**Netaji Subhas University of Technology** | B.Tech, Computer Science | GPA: 8.5 | Nov 2020 – Aug 2024

## SKILLS

Languages: Java, Kotlin, C, Python, JavaScript, SQL
Backend & Distributed Systems: Spring Boot, Microservices, REST APIs, System Design, Apache Spark, Apache Kafka, Airflow, Hadoop
Cloud & Infrastructure: AWS (Lambda, S3, IAM, Bedrock), Docker, Kubernetes, Linux, Terraform, Snowflake, Databricks
Databases & DevOps: PostgreSQL, MySQL, MongoDB, Redis, GitLab CI, Jenkins, GitHub Actions, Prometheus, Grafana, Datadog, Git
