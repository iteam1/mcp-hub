# 🌐 The Interaction Lifecycle

In the previous section, we discussed the lifecycle of a single interaction between a **Client** (💻) and a **Server** (🌐). Now, let’s examine the full lifecycle of a complete interaction under the **MCP protocol**.

The MCP protocol defines a structured sequence of stages:

## 🔹 Initialization

1. The **Client** connects to the **Server**.
2. They exchange protocol versions and capabilities.
3. The **Server** responds with its supported protocol version and capabilities.

```
💻 → initialize → 🌐  
💻 ← response   ← 🌐  
💻 → initialized → 🌐  
```

* The **Client** confirms that initialization is complete via a notification message.

## 🔹 Discovery

1. The **Client** requests a list of available capabilities.
2. The **Server** responds with the available tools.

```
💻 → tools/list → 🌐  
💻 ← response    ← 🌐  
```

* This process may be repeated for each tool, resource, or prompt type.

## 🔹 Execution

1. The **Client** invokes a capability based on its current needs.
2. The **Server** may send an optional progress notification.
3. The **Server** returns a response.

```
💻 → tools/call → 🌐  
💻 ← notification (optional progress) ← 🌐  
💻 ← response                       ← 🌐  
```

## 🔹 Termination

1. The **Client** gracefully shuts down the connection.
2. The **Server** acknowledges the shutdown.
3. The **Client** sends a final exit message.

```
💻 → shutdown → 🌐  
💻 ← response ← 🌐  
💻 → exit     → 🌐  
```

* The interaction lifecycle concludes with the **Client**’s `exit` message.

Got it! Here's a clean, well-formatted version of your content with clear headings, a table, and bullet points for clarity:

---

# How Capabilities Work Together

Let’s look at how these capabilities work together to enable complex interactions. In the table below, we’ve outlined the capabilities, who controls them, the direction of control, and some other details.

| **Capability** | **Controlled By** | **Direction**            | **Side Effects**  | **Approval Needed**   | **Typical Use Cases**                   |
| -------------- | ----------------- | ------------------------ | ----------------- | --------------------- | --------------------------------------- |
| Tools          | Model (LLM)       | Client → Server          | Yes (potentially) | Yes                   | Actions, API calls, data manipulation   |
| Resources      | Application       | Client → Server          | No (read-only)    | Typically no          | Data retrieval, context gathering       |
| Prompts        | User              | Server → Client          | No                | No (selected by user) | Guided workflows, specialized templates |
| Sampling       | Server            | Server → Client → Server | Indirectly        | Yes                   | Multi-step tasks, agentic behaviors     |

---

These capabilities are designed to work together in complementary ways:

* A user might select a **Prompt** to start a specialized workflow.
* The **Prompt** might include context from **Resources**.
* During processing, the AI model might call **Tools** to perform specific actions.
* For complex operations, the **Server** might use **Sampling** to request additional LLM processing.

The distinction between these primitives provides a clear structure for MCP interactions, enabling AI models to access information, perform actions, and engage in complex workflows while maintaining appropriate control boundaries.

# MCP SDK Overview

Both SDKs provide similar core functionality, following the MCP protocol specification we discussed earlier. They handle:

* Protocol-level communication
* Capability registration and discovery
* Message serialization/deserialization
* Connection management
* Error handling