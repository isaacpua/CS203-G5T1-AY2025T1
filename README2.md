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
| Advanced Tariff Search & Filtering | Provides a fast and flexible search system. Users can search by tariff ID or description, and filter by reporter or partner country using text-based search. |
| Detailed Tariff Information | Users can view comprehensive information about each tariff, including description, category, ad valorem rate, specific per-unit rate, and applicable trade programs. |
| Tariff Management (Admin) | Allows administrators to create new tariffs, edit existing ones, and delete tariffs that are no longer needed. |

---

## 📁 Data Interaction, Management & Visualization

| Area | Description |
|------|-------------|
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


## Installation

To run the TARIFIC platform locally, simply start the development infrastructure using Docker.

```bash
cd infra
docker compose -f docker-compose.dev.yml up -d
