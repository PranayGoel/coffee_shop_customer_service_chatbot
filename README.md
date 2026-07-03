
# Coffee Shop Customer Service Chatbot 🚀☕️

> **Fork note:** This is a fork of [abdullahtarek/coffee_shop_customer_service_chatbot](https://github.com/abdullahtarek/coffee_shop_customer_service_chatbot). The original multi-agent chatbot, tutorial, and app design are by **Abdullah Tarek** — full credit for the baseline. Everything below "What I added" is mine; the original documentation follows unchanged further down.

## 🧠 What I added: you don't need my GPU to try this

The chatbot only ran behind a self-hosted Llama-3.1-8B deployment on RunPod — real GPU cost, deployment fiddliness, and a genuine barrier to anyone (a recruiter, an interviewer, or a fresh contributor) actually trying it. OpenAI, Google Gemini, DeepSeek, and OpenRouter are all reachable through the *identical* `openai` SDK client shape this codebase already used — switching providers is a config change, not a rewrite.

- **`llm_client.py`** — provider-agnostic client (`LLM_PROVIDER=openai|gemini|deepseek|openrouter`, or the original `runpod` default — existing `.env` files keep working unchanged). One config abstraction, not per-provider branches. **`openrouter` is the recommended provider for trying this at zero cost**: `openai/gpt-oss-20b:free` was confirmed via a live query of OpenRouter's own `/api/v1/models` endpoint (not just docs) to support both structured outputs and tool calling together on the free tier, with no card required — unlike Gemini's compat layer (documented "beta", with a confirmed bug on its 2.0-series models specifically — see [googleapis/python-genai#1586](https://github.com/googleapis/python-genai/issues/1586)) or Groq (whose docs explicitly disallow combining strict JSON schema with tool calling in one request).
- **`structured_output.py`** — migrated `RouterAgent` (the highest-frequency call — it runs on *every* turn) from "prompt the model to output JSON, then `json.loads()` it and hope" to real schema-guaranteed structured output (`response_format={"type":"json_schema",...}`) on providers that support it (OpenAI, Gemini, OpenRouter), with a validated fallback for providers that don't (DeepSeek's compat layer is JSON-mode-only, not schema-guaranteed, per their docs). Scoped to the router only this round — the other agents' prompts use idiosyncratic keys (`"step number"`, `"chain of thought"`) and migrating them without a live endpoint to test against risked a regression I couldn't verify; documented as a natural next step.
- **`response_cache.py`** — repeated identical questions to `DetailsAgent` ("what are your hours") skip the embedding call, the Pinecone query, and the chat completion entirely.
- **`eval_harness.py` + `eval_dataset.py`** — ~35 hand-labeled routing examples, run against whichever provider is configured, reporting accuracy, latency, and an estimated $ cost per provider — the actual "which cheap provider is worth using" answer, not just "does routing work."
- **`AgentController` dependency injection** — `router_agent`/`agent_dict` can be injected directly, so the dispatch logic is testable without live credentials or network access.
- **Startup config validation** — `llm_client.validate_startup_config()` checks every required env var up front and lists everything missing in one clear message, instead of a confusing crash deep inside the OpenAI/Pinecone SDK on whichever call happens to run first.
- **`python_code/finetuning/`** — an authored (not executed — no GPU here) QLoRA fine-tuning pipeline for the router, adapted from Unsloth's official Llama-3.1-8B recipe. The data-generation script *is* runnable and verified (242 labeled examples, zero external deps); the training notebook is ready to run on a free Colab T4.

**Verification — the actually-important part:** `llm_client.py`, `structured_output.py`, `response_cache.py`, `eval_harness.py`, and `AgentController`'s dispatch logic are covered by a real, executed test suite (40 tests, `python3 -m unittest discover -s python_code/api/tests -t python_code/api`, all passing — see below). The tests use dependency-injected fakes (`tests/fakes.py` duck-types the OpenAI SDK client shape). I do now have a genuine free-tier key (Gemini, via AI Studio) and confirmed its *native* API works, but haven't yet completed a clean end-to-end run through the OpenAI-*compatible* endpoint specifically — everything here is built and structurally verified; real accuracy/latency/cost numbers against a live model are the next step, and OpenRouter's `openai/gpt-oss-20b:free` is the lowest-friction path to get them.

Also fixed along the way: a real bug in `AgentController.get_response`'s fallback dispatch — `dict.get(key, default)` evaluates `default` eagerly even when `key` is present, so `self.agent_dict.get(chosen_agent, self.agent_dict["details_agent"])` required `"details_agent"` to always exist even for a perfectly valid, present `chosen_agent`. Found by writing a dispatch test with a minimal `agent_dict`, not by inspection.

## 🧪 Tests

Runs with **zero pip installs** — this network blocks PyPI entirely, so tests use dependency-injected fakes and Python's stdlib `unittest` rather than requiring `openai`/`pytest` to be installed:
```
python3 -m unittest discover -s python_code/api/tests -t python_code/api
```

---

Welcome to the Coffee Shop Customer Service Chatbot project! This repository contains the code, resources, and instructions to build an AI-powered chatbot designed to enhance customer experiences in a coffee shop app. Leveraging the power of LLMs (Large Language models), Natural Language Processing (NLP), and RunPod's infrastructure, this chatbot can assist with taking orders, answering detailed menu queries, and providing personalized product recommendations—all within a React Native mobile app.

# 🎯 Project Overview
The goal of this project is to create a smart, **agent-based chatbot** that can:
* Handle real-time customer interactions with the chatbot including orders.
* Answer questions about menu items, including ingredients and allergens through a **Retreival augmented Generation (RAG) system**.
* Provide personalized product recommendations through a **market basket analysis recommendation engine**.
* Guide customers through a seamless order process, ensuring accurate and structured order details.
* Block irrelevant or harmful queries using a Guard Agent for safe and relevant interactions.

## 🔧 What You'll Learn
Through this project, you will gain hands-on experience in:
* Deploying your personal LLM with RunPod
* Deploying an agent-based system with specialized agents like Order Taking, Details, and Guard agents.
* Setting up a vector database for storing coffee shop menu and product information.
* Implementing Retrieval-Augmented Generation (RAG) for detailed and accurate responses.
* Training and deploying a recommendation engine.
* Building a React Native app that integrates this powerful chatbot.

## 🧠 Chatbot Agent Architecture
![Coffee Shop Agent Architecture](./images/chatbot_agent_architecture.jpg)

The chatbot in this project is designed using a modular agent-based architecture, where each agent is responsible for a specific task, ensuring a seamless and efficient interaction between the user and the coffee shop’s services. This architecture enables the chatbot to perform complex actions by delegating tasks to specialized agents, making the system highly flexible, scalable, and easy to extend.

### 🤖 Key Agents in the System:
1. **Guard Agent:**
This agent acts as the first line of defense. It monitors all incoming user queries and ensures that only relevant and safe messages are processed by the other agents. It blocks inappropriate, harmful, or irrelevant queries, protecting the system and ensuring smooth conversations with users.
2. **Order Taking Agent:**
This agent is responsible for guiding customers through the order placement process. It uses chain-of-thought prompt engineering to simulate human-like reasoning, ensuring the order is accurately structured and all customer preferences are captured. It ensures that the chatbot gathers all necessary order details in a logical, step-by-step process, enhancing the reliability of the final order.
3. **Details Agent (RAG System):**
Powered by a Retrieval-Augmented Generation (RAG) system, the Details Agent answers specific customer questions about the coffee shop, including menu details, ingredients, allergens, and other frequently asked questions. It retrieves relevant data stored in the vector database and combines it with language generation capabilities to provide clear and precise responses.
4. **Recommendation Agent:**
This agent handles personalized product recommendations by working with the market basket recommendation engine. Triggered by the Order Taking Agent, it analyzes the user's current order or preferences and suggests complementary items. This agent aims to boost upselling opportunities or help users discover new products they might like.
5. **Classification Agent:**
This is the decision-making agent. It classifies incoming user queries and determines which agent is best suited to handle the task. By categorizing user intents, it ensures that queries are routed efficiently, whether the user is asking for recommendations, placing an order, or inquiring about specific menu details.

### ⚙️ How the Agents Work Together
The agents work collaboratively in a pipeline architecture to process user inputs:

1. A customer query is received and first assessed by the Guard Agent.
2. If valid, the Classification Agent determines the intent behind the user query (e.g., placing an order, asking about a product, or requesting a recommendation).
3. The query is then forwarded to the appropriate agent:
    * The Order Taking Agent handles order-related queries.
        * Order Agent can forward the order to the recommendation agent to try and upsell the user near the end of their order.
    * The Details Agent fetches specific menu information.
    * The Recommendation Agent suggests complementary products.


## 📱 React Native Coffee Shop App
![Coffee Shop Agent Architecture](./images/mobile_app.png)

The React Native Coffee Shop App serves as the front-end interface for customers to interact with the AI-powered chatbot and explore the menu. Designed with a clean, intuitive user experience in mind, the app seamlessly integrates the chatbot for real-time customer service, enabling users to place orders, receive personalized product recommendations, and get detailed information about menu items.

### Key Features:
* **Landing Page:** A welcoming entry point to the coffee shop experience.
* **Home Page:** Displays featured menu items and product categories.
* **Item Details Page:** Provides detailed descriptions, including ingredients and allergens for each item.
* **Cart Page:** Allows users to review and modify their order before checkout.
* **Chatbot Interface:** Enables customers to interact directly with the AI chatbot for order assistance, recommendations, and queries.

# 📂 Directory Structure
```bash
├── coffee_shop_customer_service_chatbot
│   ├── coffee_shop_app_folder # Contains React Native app code   
│   ├── python_code
│       ├── API/               # Chatbot API for agent-based system
│       ├── dataset/           # Dataset for training recommendation engine    
│       ├── products/          # Product data (names, prices, descriptions, images)   
│       ├── build_vector_database.ipynb             # Builds vector database for RAG model   
│       ├── firebase_uploader.ipynb                 # Uploads products to Firebase    
│       ├── recommendation_engine_training.ipynb    # Trains recommendation engine 
```

## 🚀 Getting Started
Each folder has their own getting started section. So this way we can deploy the front end, backend and setup individually. 

## 🔗 Refrence Links
* [RunPod](https://rebrand.ly/Runpod-Abdullah): RunPod Official Site - Infrastructure for deploying and scaling machine learning models.
* [Kaggle Dataset]([https://www.kaggle.com/datasets/ylchang/](https://www.kaggle.com/datasets/ylchang/coffee-shop-sample-data-1113)): Source of the dataset used for training the recommendation engine.
* [Figma app design](https://www.figma.com/design/PKEMJtsntUgQcN5xAIelkx/Coffee-Shop-Mobile-App-Design-(Community)?node-id=421-1221&node-type=FRAME&t=bakGV2g59KQ7cPBi-0): - The design mockups for the coffee shop app, providing a visual guide for the user interface and experience.
* [Hugging Face](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct): Hugging Face Models - Repository for Llama LLms, a state-of-the-art NLP model used in our chatbot.
* [Pinecone](https://docs.pinecone.io/guides/get-started/quickstart): Pinecone Documentation - Documentation for the vector database used in the project.
* [Firebase](https://firebase.google.com/docs): Firebase Documentation - Comprehensive guide for using Firebase to manage app data for the coffee shop app.
