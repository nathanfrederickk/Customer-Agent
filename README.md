# **Multi-Agent Customer Service System**

## **🚀 Overview**

This project is a fully automated, AI-powered customer service agent designed to handle email inquiries for the Australian Temporary Graduate visa (subclass 485). It leverages a multi-agent workflow and a Retrieval-Augmented Generation (RAG) pipeline to provide accurate, context-aware answers, with a robust system for escalating complex queries to human agents.

The entire application is built on a serverless, event-driven architecture on AWS and is managed entirely through Infrastructure as Code (IaC) using the AWS CDK.

## **🏛️ Architecture**

The system is designed to be highly scalable, resilient, and cost-effective by decoupling its components into a clear, event-driven flow.

1. **Email Ingestion:**  
   * The process begins when a new email arrives in a designated Gmail inbox.  
   * **Gmail API Push Notifications** are configured to instantly send a notification to a **Google Pub/Sub** topic.  
   * The Pub/Sub topic pushes this notification to a public **AWS API Gateway** endpoint.  
2. **Initial Processing (The Front Door):**  
   * The API Gateway triggers a lightweight **Ingestion Lambda** function.  
   * This function's sole responsibilities are to fetch the full email content, save a clean version to an **Amazon RDS (PostgreSQL)** database, and place a job message (containing the email's thread\_id) onto an **Amazon SQS (Simple Queue Service)** queue.  
3. **Core AI Processing (The Brain):**  
   * The SQS queue acts as a reliable buffer and triggers the main **Agent Lambda** function.  
   * This powerful Lambda function runs a **LangGraph** workflow, which orchestrates a team of specialized AI agents:  
     * **Guardrail Agent:** The first agent to inspect the query. It checks for prompt injections, off-topic questions, and other malicious content. If the query is unsafe, it's immediately escalated.  
     * **Customer Agent (RAG):** If the query is safe, this agent takes over. It uses **LlamaIndex** to retrieve the most relevant context from a **ChromaDB** vector store (containing the visa knowledge base) and drafts a fact-based answer.  
     * **Manager Agent:** This final agent acts as a quality control layer. It reviews the drafted answer against the retrieved context and the original question, making a final decision to either send the reply or escalate to a human.  
4. **Action & Escalation:**  
   * If the Manager Agent approves the draft, the **Agent Lambda** uses the Gmail API to send the reply.  
   * If the Manager Agent rejects the draft, a message is sent to a separate **Escalation SQS queue**, where it can be picked up by a human support team.

## **✨ Key Features**

* **Multi-Agent System:** Utilizes a sophisticated workflow with specialized agents for security, drafting, and quality control, leading to more reliable and safer responses.  
* **Retrieval-Augmented Generation (RAG):** Ensures all answers are grounded in a specific knowledge base, preventing the AI from hallucinating or providing incorrect information.  
* **Fully Serverless & Event-Driven:** The entire architecture is built on AWS Lambda and SQS, meaning it scales automatically and you only pay for what you use.  
* **Infrastructure as Code (IaC):** The complete cloud environment is defined and managed using the AWS CDK, allowing for repeatable, version-controlled deployments.  
* **Containerized Logic:** The core AI logic is packaged into a Docker container, ensuring consistency between local development and the cloud environment.

## **🛠️ Tech Stack**

* **AI / LLM:** Google Gemini API, LangGraph, LlamaIndex  
* **Vector Database:** ChromaDB  
* **Cloud Platform:** AWS  
  * **Compute:** Lambda  
  * **Integration:** SQS, API Gateway  
  * **Database:** RDS (PostgreSQL)  
  * **Security:** Secrets Manager, IAM  
* **Infrastructure as Code:** AWS CDK (JavaScript)  
* **Containerization:** Docker