# 🧠 Intelligent Index System

## Overview

The **Intelligent Index System** is a modular, LLM/Agentic/RAG-driven platform designed to intelligently ingest, analyze, and manage high-volume streaming data in real time. It transforms unstructured and structured content—such as log files—into actionable insights through prompt-based extraction, contextual memory retrieval, and human-in-the-loop refinement.

The system leverages a multi-memory architecture—**Short-Term Memory (STM)**, **Episodic Memory**, and **Long-Term Memory (LTM)**—to incrementally learn and evolve based on expert feedback, enabling highly relevant and continuously improving outputs.

---

## 🚀 Usage

The Intelligent Index System API exposes three main endpoints to interact with your LangGraph workflow:

1. `/invoke` – for graph invocation (initial + human feedback)  
2. `/retrieve-short-term` – to retrieve short-term memory (STM) reports  
3. `/retrieve` – to search over stored and summarized data

---

### 1. 🔁 Invoke Endpoint

This endpoint starts a new graph invocation or resumes a paused (human-interrupt) graph based on the request payload.

#### 🟢 A. Initial Invocation

Use this when you want to start processing **new log data**.

**Endpoint:**
```
POST /invoke
```

**Payload Example:**
```json
{
  "namespace": "log_data",
  "data": [
    {
      "date": "2025-05-01T06:12:34Z",
      "content": "INFO [2025-05-01 06:12:34] [thermostat.controller] Living Room temperature set to 22°C by user 'emma' via mobile app.\nDEBUG [2025-05-01 06:12:35] [thermostat.sensor] Current temp: 20.6°C. Target: 22°C. Heating ON.\nINFO [2025-05-01 06:13:01] [event.log] Thermostat reached desired temperature in 2m 18s."
    },
    {
      "date": "2025-05-01T07:45:22Z",
      "content": "WARN [2025-05-01 07:45:22] [security.camera] Motion detected at Front Door.\nINFO [2025-05-01 07:45:22] [camera.snapshot] Image saved to /storage/security/front_door/2025-05-01_074522.jpg.\nDEBUG [2025-05-01 07:45:23] [notification.service] Push alert sent to homeowner's device."
    }
  ]
}
```

**Curl Example:**
```bash
curl -X POST "http://localhost:8000/invoke" \
     -H "Content-Type: application/json" \
     -d '{
           "namespace": "log_data",
           "data": [
             {
               "date": "2025-05-01T06:12:34Z",
               "content": "INFO [2025-05-01 06:12:34] [thermostat.controller] Living Room temperature set to 22°C by user '\''emma'\'' via mobile app."
             },
             {
               "date": "2025-05-01T07:45:22Z",
               "content": "WARN [2025-05-01 07:45:22] [security.camera] Motion detected at Front Door."
             }
           ]
         }'
```

**Response:**
- `"status": "final"` – if the graph completes without requiring feedback
- `"status": "waiting"` – if the graph pauses for human input (with a `"human_interrupt"` message)

---

#### 🟡 B. Human Resume Invocation

When the graph pauses for human input, resume it by sending either an approval or feedback.

**Endpoint:**
```
POST /invoke
```

**Payload – Feedback Example:**
```json
{
  "namespace": "log_data",
  "feedback": "I don't want recommendations"
}
```

**Payload – Approval Example:**
```json
{
  "namespace": "log_data",
  "approve": "True"
}
```

**Curl Examples:**
```bash
curl -X POST "http://localhost:8000/invoke" \
     -H "Content-Type: application/json" \
     -d '{
           "namespace": "log_data",
           "feedback": "I don'\''t want recommendations"
         }'

curl -X POST "http://localhost:8000/invoke" \
     -H "Content-Type: application/json" \
     -d '{
           "namespace": "log_data",
           "approve": "True"
         }'
```

**Response:**
- `"status": "final"` – if graph resumes and completes
- `"status": "waiting"` – if additional feedback is still needed

---

### 2. 📄 Retrieve Short-Term Report

Retrieves the **Short-Term Memory (STM)** report for a given namespace.

**Endpoint:**
```
GET /retrieve-short-term
```

**Query Parameter:**
```
namespace=log_data
```

**Curl Example:**
```bash
curl "http://localhost:8000/retrieve-short-term?namespace=log_data"
```

**Response Example:**
```json
{
  "namespace": "log_data",
  "short_term_report": "Your aggregated short-term memory report details..."
}
```

---

### 3. 🔍 Retrieve Information

Perform a **semantic search** over processed and summarized data.

**Endpoint:**
```
GET /retrieve
```

**Query Parameter:**
```
query=What did emma set the temperature to
```

**Curl Example:**
```bash
curl "http://localhost:8000/retrieve?query=What+did+emma+set+the+temperature+to"
```

**Response Example:**
```json
{
  "query": "What did emma set the temperature to",
  "results": "Search results for query 'What did emma set the temperature to' would be implemented here."
}
```

---

### 🧪 Example Test Script

You can test all endpoints using the provided `src/test_app.py` script. It demonstrates:

- Invoking the graph (initial and human feedback)
- Retrieving STM reports
- Performing semantic search queries

This script helps simulate real-world workflows and validates system behavior end-to-end.

---

## 🧩 System Workflow

### 1. 🧠 Information Extraction Pipeline (via LangGraph)

Once a buffer flush is triggered, the **extraction pipeline** begins:

#### 🔍 Contextual Data Retrieval

- **Prompt Retrieval**  
  Retrieves a namespace-specific prompt via **LangMem**, continuously optimized through expert feedback.

- **Episodic Memory Retrieval**  
  Gathers relevant past expert interactions (corrections, emphasis, notes) to guide extraction accuracy and relevance.

- **Short-Term Memory Retrieval**  
  Fetches the existing STM report, which includes recent dated entries information and general knowledge.

#### 🧾 LLM Extraction Process

- Processes the buffered data using the namespace’s tailored prompt.
- Enhances extraction with episodic and short-term memory context.
- Outputs a **structured initial report** including:
  - Key events
  - General insights
  - Anomalies or trends

---

### 2. 👨‍🔬 Domain Expert Feedback Loop

- The generated report is reviewed by a **domain expert** via UI or interface.
- Experts:
  - Validate and edit extracted insights
  - Add domain-specific context
  - Flag errors or omissions
- Upon approval:
  - **Episodic memory is updated** with the interaction
  - **Prompt is refined** for improved future extractions

---

### 3. 📚 Memory Systems Update

#### 🧠 Short-Term Memory (STM)

- Updated in real time with approved insights
- Structured as:
  - **Dated Data**: Chronological events/facts
  - **Undated General Knowledge**: Persistent, timeless insights
- Stored in cloud-distributed **JSON files**
- Automatic summarization:
  - Daily → Weekly → Monthly → Quarterly → Yearly
  - Redundancy reduction, trend consolidation

**Example STM Report Format:**

```markdown
# Short-Term Memory Report

## Dated Data

### 2025-03-29
- User logins spiked between 8–10 PM
- Latency increased by 15% during peak hours

### Week of 2025-03-18
- Stable usage patterns
- Minor error spike on 2025-03-21

### February 2025
- Sustained EU engagement growth
- Three major system outages resolved

## Undated (General Knowledge)
- Peak activity between 12–2 PM local time
- Performance degrades beyond 5000 concurrent requests
- EU users maintain ~5% higher engagement than other regions
```

---

#### 🧠 Long-Term Memory (LTM) – *LightRAG*

Expert-refined reports are embedded into a **hybrid graph + vector store**:

- **Graph DB**: Captures relationships, causality, and metadata
- **Vector Store**: Enables semantic search and RAG-style retrieval

Provides deep contextual knowledge retrieval for agents and queries.

---

### 4. 🔎 Query-Time Retrieval

When an agent or user issues a query:

- **STM** offers immediate, high-resolution recent context
- **Episodic Memory** prioritizes insights aligned with expert interaction history
- **LTM (LightRAG)** enables:
  - Semantic search for similar entries
  - Graph-based traversal of relationships and causes

The result is **context-rich, expert-aligned, and accurate responses**.

---

## ⚙️ Technical Stack

| Component                    | Technology                    |
|-----------------------------|-------------------------------|
| Workflow Orchestration      | LangGraph                     |
| Prompt Optimization / Memory| LangMem                       |
| Short-Term Memory           | Postgres                      |
| Long-Term Memory            | LightRAG (Graph + Vector DB)  |

---

## 🌟 Key Advantages

- ✅ **Adaptive Learning**: Prompts improve over time via expert feedback  
- ⚡ **High Performance**: Efficient memory management scales with data volume  
- 🧠 **Contextual Intelligence**: Multi-memory architecture yields precise, relevant insights  
- 🔄 **Human-in-the-Loop**: Experts continuously shape and refine model performance  
- 📈 **Scalable Knowledge**: Hybrid RAG architecture enables fast, semantic retrieval  

---

## 📌 Ideal Use Cases

- Log & telemetry analysis  
- Automated incident reporting  
- Continuous compliance documentation  
- Domain-specific knowledge synthesis  
- Agent-augmented monitoring systems  
