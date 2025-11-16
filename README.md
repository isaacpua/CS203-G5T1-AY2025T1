# TARIFIC – Trade Analytics, Research, Insights & Forecasting Information Center

![Analytics](https://img.shields.io/badge/Platform-Trade%20Intelligence-blue)
![Tariffs](https://img.shields.io/badge/Domain-International%20Tariffs-green)
![Dashboard](https://img.shields.io/badge/UI-Dashboard%20Driven-orange)
![AI](https://img.shields.io/badge/AI-Intelligent%20Insights-purple)

> **TARIFIC** is a modern tariff intelligence platform designed to simplify global trade analysis for consumers, businesses, and analysts.  
> It provides clear tariff lookup, step-by-step calculations, historical trend analysis, forecasting, curated news, and AI-powered insights — all in one unified experience.

---

## 🌍 Overview

Tariff systems across countries are complex, constantly changing, and often difficult to interpret. TARIFIC streamlines this process by offering:

- A dynamic and easy-to-use tariff calculator  
- Historical explorer dashboards to visualize tariff trends  
- AI-powered tools for article analysis and insights  
- Forecast projections for future tariff movements  
- Automated newsletters and mailing lists  
- Admin tools for managing users and tariffs  

The platform is designed with a strong focus on **clarity**, **usability**, and **business decision-support**.

---

# ⭐ TARIFIC Feature List

## 🔐 Core User & Admin Features

| Area | Description |
|------|-------------|
| Secure User Authentication | A robust login and registration system built around JWT ensures that only authorized users can access the application and its routes. |
| Role-Based Access Control | The application supports both admin and default user roles, allowing for different levels of access and functionality. |
| Profile Management | View account details, update username and password. |
| Admin User Management | A dedicated interface for administrators to manage all user accounts, including the ability to edit user roles or delete users entirely. |

---

## 📊 Calculator

| Area | Description |
|------|-------------|
| Dynamic Tariff Calculator | Search for specific tariffs, filter by origin and destination countries, and input values like “declared value” and “quantity” to get accurate calculations. |
| Calculation History | A dedicated page for users to review their past tariff calculations, separate from the main calculator interface. |

---

## 📁 Data Interaction, Management & Visualization

| Area | Description |
|------|-------------|
| Advanced Tariff Search & Filtering | Provides a fast and flexible search system. Users can search by tariff ID or description, and filter by reporter or partner country using text-based search. |
| Detailed Tariff Information | Users can view comprehensive information about each tariff, including description, category, ad valorem rate, specific per-unit rate, and applicable trade programs. |
| Tariff Management (Admin) | Allows administrators to create new tariffs, edit existing ones, and delete tariffs that are no longer needed. |
| Data Export | Users can export the entire tariff database as a CSV file for analysis, reporting, or record-keeping. |
| Historical Data Explorer | An interactive visualization tool that enables users to explore multi-year tariff trends. Filters include reporter country, partner country, item code, and date ranges. Pre-configured “Recommended” presets provide common exploration shortcuts. |
| Tariff Data Forecasting | A predictive analytics feature that forecasts tariff rates for the next three years using a regression model. Results are visualized in a dedicated Forecast page, helping users anticipate market changes and make informed decisions. |

---

## 📰 Decision-Support and Intelligence Tools

| Area | Description |
|------|-------------|
| Tariff Newsletter Service | A content-curation system that automatically collects and compiles the latest tariff-related news from public sources. Admins can preview and edit the newsletter before sending it out. |
| Tariff Mailing List | A complete mailing list management system integrated into the Newsletter page. Admins can add/remove recipients and dispatch curated newsletters with a single click using a secure email service. |
| Tariff Article Analysis | An AI-powered tool that processes external articles and reports to extract key tariff-related insights. It identifies countries, goods, sentiment, and important tariff changes, providing a concise summary and structured intelligence. |

## 📰 Model Context Protocol (MCP)

| Area | Description |
|------|-------------|
| MCP Tool Server | The centralized intelligence microservice powering TARIFIC’s advanced tools such as forecasting, article analysis, and agent-based workflows. |
| MCP Assistant (T.A.R.I.F.F. Agent) | A powerful agentic AI assistant that can understand natural language tasks, execute multi-step workflows, run backend tools, and deliver intelligent insights as if it were an assistant employee. |

---

## 🎨 UI/UX

| Area | Description |
|------|-------------|
| Mobile Responsive | A modern, flexible UI that adapts to tablet, desktop, and mobile screen sizes. |
| Light & Dark Mode | A thematic dual-mode interface: light mode shows a daytime farm scene, while dark mode features a nighttime farm environment. |
| Intuitive Navigation | A clean and consistent navigation layout enabling users to easily move between the Calculator, Dashboard, Explorer, Forecasts, Newsletter, Analyzer, and Assistant. |
| Protected Routes | Sensitive application pages and tools are protected, ensuring only authenticated and authorized users can access restricted features. |


## 🌟 Why TARIFIC Matters

TARIFIC empowers:

### **Businesses**
- Predict duty costs  
- Avoid overpayment  
- Stay updated with tariff news  
- Make informed sourcing decisions  

### **Analysts**
- Study historical trends  
- Compare tariff behavior across years  
- Build reports using clear data exports  

### **Administrators**
- Maintain accurate tariff data  
- Manage users and roles  
- Automate communications  

---

## 🏁 Conclusion

TARIFIC transforms scattered tariff information into a **centralized**, **visual**, and **intelligent** platform.  
Whether you’re calculating duties, forecasting trends, or analyzing policy news, TARIFIC delivers a complete suite of tools designed for clarity, insight, and business decision-making.

# System Architecture
![alt text](/docs/images/Architecture_Diagram.png)
## Frontend Architecture (infra/frontend)

The frontend is a static single-page application (SPA) hosted on Amazon S3 and served globally by Amazon CloudFront.

* **Hosting**: An **S3 bucket** (`aws_s3_bucket.spa`) is configured to host the static website files (like `index.html`, CSS, and JavaScript). This bucket is private and not directly accessible to the public.
* **Content Delivery (CDN)**: An **Amazon CloudFront distribution** (`aws_cloudfront_distribution.spa`) acts as the public entry point.
    * It serves the S3 bucket's content using an **Origin Access Identity (OAI)**, which ensures users can only access the files through CloudFront.
    * It handles **custom domains** (`tarific.rocks` and `www.tarific.rocks`) using an AWS Certificate Manager (ACM) certificate created in the `us-east-1` region, which is a requirement for CloudFront.
    * It's configured to route 403 (Access Denied) and 404 (Not Found) errors back to `/index.html`, allowing the client-side SPA router to handle these paths.
* **DNS**: **Amazon Route 53** is used for DNS. "A" records for both the root domain (`tarific.rocks`) and the `www` subdomain point to the CloudFront distribution.
* **API Routing**: The CloudFront distribution also acts as a reverse proxy, forwarding all API traffic to the backend Application Load Balancer (ALB). It has three specific path-based rules:
    * `/api/v1/*`
    * `/mcp/api/v1/*`
    * `/chat/*` (for WebSockets)


## Backend Architecture (infra/backend)

The backend consists of four microservices, defined in the `docker-compose.dev.yml` file, which are deployed as containers on an Amazon ECS (Elastic Container Service) cluster using the **EC2 launch type**.

* **Services**:
    1.  **tariff-backend**: The main API service.
    2.  **mcp-gateway-backend**: An API gateway service.
    3.  **mcp-chatbot-backend**: A WebSocket-based chat service.
    4.  **mcp-server-backend**: An internal-only service that the other services depend on.

### 1. Networking (VPC)

A custom **VPC** (`aws_vpc.main`) is created to house all backend resources.
* **Public Subnets**: Two public subnets are used for public-facing resources like the Application Load Balancer and NAT Gateways. They have a route table pointing to an **Internet Gateway** (`aws_internet_gateway.main`).
* **Private Subnets**: Two private subnets are used to securely host the ECS container instances. These instances do not have public IP addresses.
* **NAT Gateways**: A **NAT Gateway** (`aws_nat_gateway`) is deployed in each public subnet, allowing instances in the private subnets to access the internet (e.g., to pull container images or call external APIs) while remaining private.

### 2. Container Management (ECS)

* **ECR**: For each of the four backend services, an **ECR (Elastic Container Registry)** repository is created to store its Docker image.
* **ECS Cluster**: A single **ECS cluster** (`aws_ecs_cluster.main`) is created to manage the services.
* **Launch Templates & Auto Scaling**:
    * The cluster uses EC2 instances, not Fargate.
    * Two **Launch Templates** are defined: one for standard `t3.small` instances and another for a more powerful `m7i-flex.large` instance specifically for the `mcp-server`.
    * Each service has its own **Auto Scaling Group** (`aws_autoscaling_group`) and **ECS Capacity Provider** (`aws_ecs_capacity_provider`), allowing each service to scale its underlying EC2 instances independently.
* **Task Definitions**: Each of the four services has its own **ECS Task Definition**.
    * These definitions specify the ECR image to use, memory reservations, and port mappings.
    * Secrets (like `DB_URL`, `OPENAI_API_KEY`, etc.) are securely injected into the containers from **AWS Secrets Manager** (`aws_secretsmanager_secret.backend_env`).

### 3. Service Communication & Routing

* **Public Traffic (ALB)**: An **Application Load Balancer (ALB)** (`aws_lb.main`) serves as the public entry point for the backend.
    * It listens on HTTPS (port 443) using an ACM certificate for `api.tarific.rocks`.
    * It has **Target Groups** for the three public-facing services: `tariff-backend` (port 8080), `mcp-gateway` (port 8090), and `mcp-chatbot` (port 8001).
    * **Listener Rules** route traffic based on the URL path, matching the setup in CloudFront:
        * `/api/v1/*` -> `tariff` target group
        * `/mcp/api/v1/*` -> `mcp_gateway` target group
        * `/chat/*` -> `mcp_chatbot` target group
* **Internal Traffic (Service Discovery)**:
    * The `mcp-server-backend` is **not** exposed to the ALB.
    * It uses **AWS Cloud Map (Service Discovery)** to register itself at the internal DNS name `mcp-server.tarific.local`.
    * The `mcp-gateway` and `mcp-chatbot` task definitions are configured to find and communicate with it using this internal address instead of a public URL.
* **Security**:
    * An **ALB Security Group** (`aws_security_group.alb`) allows public HTTPS traffic (port 443) from the internet.
    * An **ECS Service Security Group** (`aws_security_group.ecs_service`) is applied to all container instances. It only allows inbound traffic from the ALB's security group and also allows containers within the group to communicate with each other (for internal service discovery).

### 4. DNS & Secrets

* **DNS**: An "A" record for `api.tarific.rocks` is created in the Route 53 hosted zone to point to the public-facing ALB.
* **Secrets**: Two secrets are created in **AWS Secrets Manager**:
    1.  `backend-env`: Stores key/value pairs for database credentials and API keys.
    2.  `mcp-token-json`: Stores the content of a `token.json` file needed by the `mcp-server`.
* **IAM**: IAM roles are correctly configured to give ECS tasks permission to pull ECR images, write logs, and read the specific secrets from Secrets Manager.


## 💻Tech Stack
### Cloud & DevOps

* AWS Services: Amazon ECS, AWS RDS (PostgreSQL), Amazon S3 (for static frontend hosting), Amazon CloudFront (CDN), Amazon ECR, Application Load Balancer (ALB), Route 53, and AWS Certificate Manager (ACM).
* Infrastructure as Code: Terraform.
* CI/CD: GitHub Actions for automated build and deployment pipelines.
* Containerization: Docker.

### Backend

* Architecture: A five-service microarchitecture.
* Frameworks & Languages:
    * Java 17 with Spring Boot 3.5.5 (for `tariff-backend`).
    * Python with FastAPI (for MCP-Server and `MCP-Gateway`).
* API Design: RESTful API principles.
* AI/ML: LangGraph, langchain, and openai libraries.
* Database: PostgreSQL with Spring Data JPA for data access.

### Frontend

* Framework: React.js (v19) with Vite.
* UI Components: shadcn-ui (using Radix UI).
* Styling: Tailwind CSS.
* Design: Responsive design that "works on both desktop and mobile devices".
* Real-time: socket.io-client for real-time communication (for the chatbot).

### Security & Performance

* Authentication: Spring Security with JSON Web Tokens (JWT) for stateless authentication.
* Network Security: Virtual Private Cloud (VPC) with Network Access Control.
* Application Security:
    * Data-in-transit encryption using HTTPS with SSL/TLS certificates.
    * Data-at-rest encryption for the RDS database.
    * Password salting and hashing.
    * Input validation (using Jakarta Validation API) to "shield against SQL injections and cross-site scripting".
* Performance: Amazon CloudFront (CDN) is used to cache and serve the frontend globally at low latency.

## Installation

To run the TARIFIC platform locally, simply start the development infrastructure using Docker.

```bash
cd infra
docker compose -f docker-compose.dev.yml up -d
