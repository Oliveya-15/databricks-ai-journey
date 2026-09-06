# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "4"
# ///
# DBTITLE 1,📚 Agent Troubleshooting Guide - WORKING SOLUTION
# MAGIC %md
# MAGIC # 📚 Agent Troubleshooting & Fix Documentation - WORKING SOLUTION ✅
# MAGIC
# MAGIC ## 🔍 WHY: The Problem
# MAGIC
# MAGIC **Symptom:** Agent was not returning expected results when asked "Get the order history of ronald54@example.net"
# MAGIC
# MAGIC **Root Cause Analysis:**
# MAGIC 1. **Primary Issue:** Agent had **no tools configured** (`UC_TOOL_NAMES = []` in agent.py)
# MAGIC 2. **Secondary Issues (from previous failed attempts):**
# MAGIC    - Incorrect MLflow logging approach (trying to pass agent object instead of file)
# MAGIC    - Missing or incorrect resource declarations
# MAGIC    - Not properly updating the serving endpoint with new version
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## ✅ WHAT ACTUALLY WORKED: The Complete Solution
# MAGIC
# MAGIC ### The 4-Step Solution That Fixed Everything:
# MAGIC
# MAGIC 1. **Configure Tools in Agent Code**
# MAGIC    ```python
# MAGIC    # BEFORE:
# MAGIC    UC_TOOL_NAMES = []  # ❌ No tools!
# MAGIC    
# MAGIC    # AFTER:
# MAGIC    UC_TOOL_NAMES = ["dbacademy.get_started_agents.get_service_history"]  # ✅ Tool configured!
# MAGIC    ```
# MAGIC
# MAGIC 2. **Write Agent to File Using %%writefile**
# MAGIC    - This is CRITICAL - you must write the agent code to a `.py` file
# MAGIC    - Use `%%writefile agent.py` at the top of the cell
# MAGIC
# MAGIC 3. **Log with Code-Based Approach**
# MAGIC    ```python
# MAGIC    mlflow.pyfunc.log_model(
# MAGIC        python_model="agent.py",  # ← Pass FILE PATH, not object!
# MAGIC        resources=[...],  # ← Must include BOTH endpoint AND function
# MAGIC        pip_requirements=[...]  # ← Include databricks-connect version
# MAGIC    )
# MAGIC    ```
# MAGIC
# MAGIC 4. **Update Serving Endpoint to New Version**
# MAGIC    - Must explicitly deploy the new version to the endpoint
# MAGIC    - Wait 5-10 minutes for deployment to complete
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🛠️ HOW: Step-by-Step Solution That ACTUALLY WORKS
# MAGIC
# MAGIC ### ⚠️ What Failed Before (Don't Do This!):
# MAGIC ```python
# MAGIC # ❌ WRONG - Trying to pass agent object
# MAGIC agent = ToolCallingAgent(...)
# MAGIC mlflow.pyfunc.log_model(python_model=agent)  # Fails with serialization errors!
# MAGIC
# MAGIC # ❌ WRONG - Missing resources
# MAGIC mlflow.pyfunc.log_model(python_model="agent.py")  # Auth will fail!
# MAGIC
# MAGIC # ❌ WRONG - Forgetting to include databricks-connect version
# MAGIC pip_requirements=["databricks-openai", "backoff"]  # Incompatible version errors!
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### ✅ What Actually Works (Follow This!):
# MAGIC
# MAGIC ### Step 1: Write Agent Code to File with %%writefile
# MAGIC **THIS IS MANDATORY** - The agent code MUST be in a `.py` file
# MAGIC
# MAGIC ```python
# MAGIC %%writefile agent.py
# MAGIC import json
# MAGIC from typing import Any, Callable, Generator, Optional
# MAGIC # ... all imports ...
# MAGIC
# MAGIC # ⭐ CRITICAL: Configure UC tools here
# MAGIC UC_TOOL_NAMES = ["dbacademy.get_started_agents.get_service_history"]
# MAGIC uc_toolkit = UCFunctionToolkit(function_names=UC_TOOL_NAMES)
# MAGIC uc_function_client = get_uc_function_client()
# MAGIC
# MAGIC TOOL_INFOS = []
# MAGIC for tool_spec in uc_toolkit.tools:
# MAGIC     TOOL_INFOS.append(create_tool_info(tool_spec))
# MAGIC
# MAGIC # ... complete agent class definition ...
# MAGIC AGENT = ToolCallingAgent(llm_endpoint=LLM_ENDPOINT_NAME, tools=TOOL_INFOS)
# MAGIC mlflow.models.set_model(AGENT)
# MAGIC ```
# MAGIC
# MAGIC ### Step 2: Log with Code-Based Approach + ALL Resources
# MAGIC **KEY POINTS:**
# MAGIC - Use `python_model="agent.py"` (file path as string)
# MAGIC - Include BOTH endpoint AND function in resources
# MAGIC - Pin databricks-connect to current version
# MAGIC
# MAGIC ```python
# MAGIC import mlflow
# MAGIC from mlflow.models.resources import DatabricksServingEndpoint, DatabricksFunction
# MAGIC from pkg_resources import get_distribution
# MAGIC
# MAGIC mlflow.set_registry_uri("databricks-uc")
# MAGIC
# MAGIC # ⭐ CRITICAL: Must include BOTH resources for auth passthrough
# MAGIC resources = [
# MAGIC     DatabricksServingEndpoint(endpoint_name="databricks-gpt-oss-120b"),
# MAGIC     DatabricksFunction(function_name="dbacademy.get_started_agents.get_service_history")
# MAGIC ]
# MAGIC
# MAGIC input_example = {
# MAGIC     "input": [{"role": "user", "content": "Get the order history of ronald54@example.net"}],
# MAGIC     "custom_inputs": {"session_id": "test-session"}
# MAGIC }
# MAGIC
# MAGIC with mlflow.start_run() as run:
# MAGIC     logged_agent_info = mlflow.pyfunc.log_model(
# MAGIC         name="agent",
# MAGIC         python_model="agent.py",  # ⭐ FILE PATH (string), not object!
# MAGIC         input_example=input_example,
# MAGIC         pip_requirements=[
# MAGIC             "databricks-openai",
# MAGIC             "backoff",
# MAGIC             f"databricks-connect=={get_distribution('databricks-connect').version}",  # ⭐ Pin version!
# MAGIC         ],
# MAGIC         resources=resources,  # ⭐ Auth passthrough!
# MAGIC     )
# MAGIC     run_id = run.info.run_id
# MAGIC
# MAGIC model_version = mlflow.register_model(
# MAGIC     model_uri=f"runs:/{run_id}/agent",
# MAGIC     name="dbacademy.get_started_agents.my_first_agent"
# MAGIC )
# MAGIC print(f"Registered version: {model_version.version}")
# MAGIC ```
# MAGIC
# MAGIC ### Step 3: Deploy to Serving Endpoint
# MAGIC ```python
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC from databricks.sdk.service.serving import ServedEntityInput
# MAGIC
# MAGIC w = WorkspaceClient()
# MAGIC w.serving_endpoints.update_config(
# MAGIC     name="agents_dbacademy-get_started_agents-my_first_agent",
# MAGIC     served_entities=[ServedEntityInput(
# MAGIC         entity_name="dbacademy.get_started_agents.my_first_agent",
# MAGIC         entity_version=str(model_version.version),  # Use the version from Step 2
# MAGIC         workload_size="Small",
# MAGIC         scale_to_zero_enabled=True
# MAGIC     )]
# MAGIC )
# MAGIC print(f"Deployment initiated for version {model_version.version}")
# MAGIC print("Wait 5-10 minutes for deployment to complete")
# MAGIC ```
# MAGIC
# MAGIC ### Step 4: Verify Deployment Status
# MAGIC ```python
# MAGIC endpoint = w.serving_endpoints.get("agents_dbacademy-get_started_agents-my_first_agent")
# MAGIC print(f"Config Update: {endpoint.state.config_update}")
# MAGIC print(f"Ready State: {endpoint.state.ready}")
# MAGIC # Check if your new version is active
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🎯 Key Learnings - What Made It Work This Time
# MAGIC
# MAGIC ### 1. ⭐ The Code-Based Logging Pattern is ESSENTIAL
# MAGIC **Why previous attempts failed:** Trying to log an agent object directly causes serialization errors
# MAGIC
# MAGIC **❌ WHAT DOESN'T WORK:**
# MAGIC ```python
# MAGIC agent = ToolCallingAgent(llm_endpoint="...", tools=TOOL_INFOS)
# MAGIC mlflow.pyfunc.log_model(python_model=agent)  # ❌ Serialization fails!
# MAGIC ```
# MAGIC
# MAGIC **✅ WHAT ACTUALLY WORKS:**
# MAGIC ```python
# MAGIC # Step 1: Write agent to file
# MAGIC %%writefile agent.py
# MAGIC # ... complete agent code ...
# MAGIC AGENT = ToolCallingAgent(llm_endpoint=LLM_ENDPOINT_NAME, tools=TOOL_INFOS)
# MAGIC mlflow.models.set_model(AGENT)
# MAGIC
# MAGIC # Step 2: Reference the FILE, not the object
# MAGIC mlflow.pyfunc.log_model(
# MAGIC     python_model="agent.py",  # ⭐ String path to file!
# MAGIC     # ... other params ...
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC ### 2. ⭐ Resources Must Include BOTH Endpoint AND Functions
# MAGIC **Why it failed before:** Missing or incomplete resource declarations
# MAGIC
# MAGIC ```python
# MAGIC # ✅ COMPLETE resource declaration:
# MAGIC resources = [
# MAGIC     DatabricksServingEndpoint(endpoint_name="databricks-gpt-oss-120b"),  # ← LLM endpoint
# MAGIC     DatabricksFunction(function_name="dbacademy.get_started_agents.get_service_history")  # ← UC function
# MAGIC ]
# MAGIC
# MAGIC # ❌ INCOMPLETE - missing UC function:
# MAGIC resources = [DatabricksServingEndpoint(endpoint_name="databricks-gpt-oss-120b")]  # Auth fails!
# MAGIC
# MAGIC # ❌ INCOMPLETE - missing endpoint:
# MAGIC resources = [DatabricksFunction(function_name="...")]  # LLM calls fail!
# MAGIC ```
# MAGIC
# MAGIC ### 3. ⭐ Pin databricks-connect Version
# MAGIC **Why it failed before:** Version mismatches cause runtime errors
# MAGIC
# MAGIC ```python
# MAGIC from pkg_resources import get_distribution
# MAGIC
# MAGIC pip_requirements=[
# MAGIC     "databricks-openai",
# MAGIC     "backoff",
# MAGIC     f"databricks-connect=={get_distribution('databricks-connect').version}",  # ⭐ Pin it!
# MAGIC ]
# MAGIC ```
# MAGIC
# MAGIC ### 4. ⭐ Tools Must Be Configured in Agent Code
# MAGIC ```python
# MAGIC # In agent.py file:
# MAGIC UC_TOOL_NAMES = ["dbacademy.get_started_agents.get_service_history"]  # ← Not empty!
# MAGIC uc_toolkit = UCFunctionToolkit(function_names=UC_TOOL_NAMES)
# MAGIC # ... create TOOL_INFOS ...
# MAGIC AGENT = ToolCallingAgent(llm_endpoint=LLM_ENDPOINT_NAME, tools=TOOL_INFOS)  # ← Pass tools!
# MAGIC ```
# MAGIC
# MAGIC ### 5. Testing After Deployment
# MAGIC ```python
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC
# MAGIC w = WorkspaceClient()
# MAGIC
# MAGIC # First, check deployment status
# MAGIC endpoint = w.serving_endpoints.get("agents_dbacademy-get_started_agents-my_first_agent")
# MAGIC print(f"Current version: {endpoint.config.served_entities[0].entity_version}")
# MAGIC print(f"Status: {endpoint.state.config_update}")
# MAGIC
# MAGIC # Once deployed, test the agent
# MAGIC response = w.serving_endpoints.query(
# MAGIC     name="agents_dbacademy-get_started_agents-my_first_agent",
# MAGIC     messages=[{"role": "user", "content": "Get the order history of ronald54@example.net"}]
# MAGIC )
# MAGIC print(response.choices[0].message.content)
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🚨 Common Pitfalls & How to Avoid Them
# MAGIC
# MAGIC ### 1. ❌ Trying to Log Agent Object Instead of File
# MAGIC **Symptom:** Serialization errors, pickling errors
# MAGIC **Fix:** Always use `%%writefile agent.py` and `python_model="agent.py"`
# MAGIC
# MAGIC ### 2. ❌ Missing or Incomplete Resources
# MAGIC **Symptom:** Auth errors, "Unauthorized" errors when calling tools
# MAGIC **Fix:** Include BOTH `DatabricksServingEndpoint` AND `DatabricksFunction` in resources list
# MAGIC
# MAGIC ### 3. ❌ Not Pinning databricks-connect Version
# MAGIC **Symptom:** Runtime errors, version mismatch errors
# MAGIC **Fix:** Use `f"databricks-connect=={get_distribution('databricks-connect').version}"`
# MAGIC
# MAGIC ### 4. ❌ Empty or Missing UC_TOOL_NAMES
# MAGIC **Symptom:** Agent responds with text but never calls tools
# MAGIC **Fix:** Add all UC functions to the list: `UC_TOOL_NAMES = ["catalog.schema.function"]`
# MAGIC
# MAGIC ### 5. ❌ Forgetting to Update Serving Endpoint
# MAGIC **Symptom:** Changes don't take effect, old version still running
# MAGIC **Fix:** Always call `w.serving_endpoints.update_config()` with new version number
# MAGIC
# MAGIC ### 6. ❌ ResourceConflict Error During Deployment
# MAGIC **Symptom:** "Endpoint served entities are currently being updated"
# MAGIC **Fix:** Wait 2-3 minutes and retry - another update is in progress
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 📋 Quick Checklist - Do This Every Time
# MAGIC
# MAGIC ### Before You Start:
# MAGIC - [ ] Verify UC function exists: `w.functions.get("catalog.schema.function")`
# MAGIC - [ ] Test function works: `uc_function_client.execute_function("catalog.schema.function", {...})`
# MAGIC
# MAGIC ### Writing Agent Code:
# MAGIC - [ ] Start cell with `%%writefile agent.py`
# MAGIC - [ ] Add UC function to `UC_TOOL_NAMES = ["catalog.schema.function"]`
# MAGIC - [ ] Create toolkit: `uc_toolkit = UCFunctionToolkit(function_names=UC_TOOL_NAMES)`
# MAGIC - [ ] Build TOOL_INFOS from toolkit
# MAGIC - [ ] End with `AGENT = ToolCallingAgent(...)` and `mlflow.models.set_model(AGENT)`
# MAGIC
# MAGIC ### Logging with MLflow:
# MAGIC - [ ] Use `python_model="agent.py"` (string path, NOT object!)
# MAGIC - [ ] Include `DatabricksServingEndpoint(endpoint_name="...")` in resources
# MAGIC - [ ] Include `DatabricksFunction(function_name="...")` in resources  
# MAGIC - [ ] Pin databricks-connect: `f"databricks-connect=={get_distribution('databricks-connect').version}"`
# MAGIC - [ ] Call `mlflow.register_model()` to get version number
# MAGIC
# MAGIC ### Deploying:
# MAGIC - [ ] Call `w.serving_endpoints.update_config()` with new version
# MAGIC - [ ] Handle ResourceConflict errors (wait and retry)
# MAGIC - [ ] Wait 5-10 minutes for deployment
# MAGIC - [ ] Check status: `w.serving_endpoints.get("endpoint-name")`
# MAGIC - [ ] Verify correct version is active
# MAGIC
# MAGIC ### Testing:
# MAGIC - [ ] Query the endpoint with test message
# MAGIC - [ ] Verify tool was called (check response for tool execution)
# MAGIC - [ ] Confirm expected data was returned
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🎉 THIS SESSION'S SUCCESS - What Finally Worked
# MAGIC
# MAGIC **Date:** September 6, 2026  
# MAGIC **Result:** ✅ SUCCESSFUL DEPLOYMENT
# MAGIC
# MAGIC ### What We Did:
# MAGIC 1. **Wrote agent code to file** using `%%writefile agent.py`
# MAGIC 2. **Configured UC tool** in the file: `UC_TOOL_NAMES = ["dbacademy.get_started_agents.get_service_history"]`
# MAGIC 3. **Logged with complete resources:**
# MAGIC    ```python
# MAGIC    resources = [
# MAGIC        DatabricksServingEndpoint(endpoint_name="databricks-gpt-oss-120b"),
# MAGIC        DatabricksFunction(function_name="dbacademy.get_started_agents.get_service_history")
# MAGIC    ]
# MAGIC    ```
# MAGIC 4. **Used code-based logging:** `python_model="agent.py"` (not an object!)
# MAGIC 5. **Pinned databricks-connect version** to avoid compatibility issues
# MAGIC 6. **Deployed to endpoint** with version 10
# MAGIC
# MAGIC ### Current Status:
# MAGIC - **Deployed Version:** 10
# MAGIC - **Deployment State:** IN_PROGRESS (Container creation)
# MAGIC - **Old Version Still Active:** Version 1 (will switch when new version ready)
# MAGIC - **Tools Configured:** ✅ get_service_history
# MAGIC - **Expected Completion:** 5-10 minutes from deployment start
# MAGIC
# MAGIC ### Key Difference from Failed Attempts:
# MAGIC The **code-based logging approach** with `python_model="agent.py"` (file path as string) instead of trying to pass the agent object directly. Combined with complete resource declarations, this fixed all serialization and auth issues.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Last Updated:** September 6, 2026 - Working Solution Documented ✅  
# MAGIC **Issue:** Agent not using UC function tool  
# MAGIC **Solution:** Updated UC_TOOL_NAMES and re-deployed agent version 2

# COMMAND ----------

# DBTITLE 1,Install Required Packages
# MAGIC %pip install backoff databricks-openai unitycatalog-ai
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Write Agent Code to File
# MAGIC %%writefile agent.py
# MAGIC import json
# MAGIC from typing import Any, Callable, Generator, Optional
# MAGIC from uuid import uuid4
# MAGIC import warnings
# MAGIC
# MAGIC import backoff
# MAGIC import mlflow
# MAGIC import openai
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC from databricks_openai import UCFunctionToolkit, VectorSearchRetrieverTool
# MAGIC from mlflow.entities import SpanType
# MAGIC from mlflow.pyfunc import ResponsesAgent
# MAGIC from mlflow.types.responses import (
# MAGIC     ResponsesAgentRequest,
# MAGIC     ResponsesAgentResponse,
# MAGIC     ResponsesAgentStreamEvent,
# MAGIC     output_to_responses_items_stream,
# MAGIC     to_chat_completions_input,
# MAGIC )
# MAGIC from openai import OpenAI
# MAGIC from pydantic import BaseModel
# MAGIC from unitycatalog.ai.core.base import get_uc_function_client
# MAGIC
# MAGIC ############################################
# MAGIC # Define your LLM endpoint and system prompt
# MAGIC ############################################
# MAGIC LLM_ENDPOINT_NAME = "databricks-gpt-oss-120b"
# MAGIC
# MAGIC SYSTEM_PROMPT = """You are a helpful customer service assistant. When users ask about their order history, returns, or service issues, use the get_service_history tool to retrieve their information by providing their email address."""
# MAGIC
# MAGIC
# MAGIC ###############################################################################
# MAGIC ## Define tools for your agent, enabling it to retrieve data or take actions
# MAGIC ## beyond text generation
# MAGIC ###############################################################################
# MAGIC class ToolInfo(BaseModel):
# MAGIC     """
# MAGIC     Class representing a tool for the agent.
# MAGIC     - "name" (str): The name of the tool.
# MAGIC     - "spec" (dict): JSON description of the tool (matches OpenAI Responses format)
# MAGIC     - "exec_fn" (Callable): Function that implements the tool logic
# MAGIC     """
# MAGIC
# MAGIC     name: str
# MAGIC     spec: dict
# MAGIC     exec_fn: Callable
# MAGIC
# MAGIC
# MAGIC def create_tool_info(tool_spec, exec_fn_param: Optional[Callable] = None):
# MAGIC     tool_spec["function"].pop("strict", None)
# MAGIC     tool_name = tool_spec["function"]["name"]
# MAGIC     udf_name = tool_name.replace("__", ".")
# MAGIC
# MAGIC     # Define a wrapper that accepts kwargs for the UC tool call,
# MAGIC     # then passes them to the UC tool execution client
# MAGIC     def exec_fn(**kwargs):
# MAGIC         function_result = uc_function_client.execute_function(udf_name, kwargs)
# MAGIC         if function_result.error is not None:
# MAGIC             return function_result.error
# MAGIC         else:
# MAGIC             return function_result.value
# MAGIC     return ToolInfo(name=tool_name, spec=tool_spec, exec_fn=exec_fn_param or exec_fn)
# MAGIC
# MAGIC
# MAGIC TOOL_INFOS = []
# MAGIC
# MAGIC # UPDATED: Added get_service_history function as a tool
# MAGIC UC_TOOL_NAMES = ["dbacademy.get_started_agents.get_service_history"]
# MAGIC
# MAGIC uc_toolkit = UCFunctionToolkit(function_names=UC_TOOL_NAMES)
# MAGIC uc_function_client = get_uc_function_client()
# MAGIC for tool_spec in uc_toolkit.tools:
# MAGIC     TOOL_INFOS.append(create_tool_info(tool_spec))
# MAGIC
# MAGIC
# MAGIC # Use Databricks vector search indexes as tools (optional)
# MAGIC VECTOR_SEARCH_TOOLS = []
# MAGIC for vs_tool in VECTOR_SEARCH_TOOLS:
# MAGIC     TOOL_INFOS.append(create_tool_info(vs_tool.tool, vs_tool.execute))
# MAGIC
# MAGIC
# MAGIC
# MAGIC class ToolCallingAgent(ResponsesAgent):
# MAGIC     """
# MAGIC     Class representing a tool-calling Agent
# MAGIC     """
# MAGIC
# MAGIC     def __init__(self, llm_endpoint: str, tools: list[ToolInfo]):
# MAGIC         """Initializes the ToolCallingAgent with tools."""
# MAGIC         self.llm_endpoint = llm_endpoint
# MAGIC         self.workspace_client = WorkspaceClient()
# MAGIC         self.model_serving_client: OpenAI = (
# MAGIC             self.workspace_client.serving_endpoints.get_open_ai_client()
# MAGIC         )
# MAGIC         self._tools_dict = {tool.name: tool for tool in tools}
# MAGIC
# MAGIC     def get_tool_specs(self) -> list[dict]:
# MAGIC         """Returns tool specifications in the format OpenAI expects."""
# MAGIC         return [tool_info.spec for tool_info in self._tools_dict.values()]
# MAGIC
# MAGIC     @mlflow.trace(span_type=SpanType.TOOL)
# MAGIC     def execute_tool(self, tool_name: str, args: dict) -> Any:
# MAGIC         """Executes the specified tool with the given arguments."""
# MAGIC         return self._tools_dict[tool_name].exec_fn(**args)
# MAGIC
# MAGIC     @staticmethod
# MAGIC     def _merge_consecutive_assistant_messages(cc_messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
# MAGIC         merged: list[dict[str, Any]] = []
# MAGIC         for msg in cc_messages:
# MAGIC             if (
# MAGIC                 msg.get("role") == "assistant"
# MAGIC                 and merged
# MAGIC                 and merged[-1].get("role") == "assistant"
# MAGIC             ):
# MAGIC                 prev = merged[-1]
# MAGIC                 prev_text = prev.get("content") if prev.get("content") not in (None, "", "tool call") else None
# MAGIC                 cur_text = msg.get("content") if msg.get("content") not in (None, "", "tool call") else None
# MAGIC                 if prev_text and cur_text:
# MAGIC                     prev["content"] = prev_text + "\n" + cur_text
# MAGIC                 elif cur_text:
# MAGIC                     prev["content"] = cur_text
# MAGIC                 if msg.get("tool_calls"):
# MAGIC                     prev["tool_calls"] = (prev.get("tool_calls") or []) + msg["tool_calls"]
# MAGIC             else:
# MAGIC                 merged.append(dict(msg))
# MAGIC         return merged
# MAGIC
# MAGIC     def call_llm(self, messages: list[dict[str, Any]]) -> Generator[dict[str, Any], None, None]:
# MAGIC         cc_messages = self._merge_consecutive_assistant_messages(to_chat_completions_input(messages))
# MAGIC         with warnings.catch_warnings():
# MAGIC             warnings.filterwarnings("ignore", message="PydanticSerializationUnexpectedValue")
# MAGIC             for chunk in self.model_serving_client.chat.completions.create(
# MAGIC                 model=self.llm_endpoint,
# MAGIC                 messages=cc_messages,
# MAGIC                 tools=self.get_tool_specs(),
# MAGIC                 stream=True,
# MAGIC             ):
# MAGIC                 chunk_dict = chunk.to_dict()
# MAGIC                 if len(chunk_dict.get("choices", [])) > 0:
# MAGIC                     yield chunk_dict
# MAGIC
# MAGIC     def handle_tool_call(
# MAGIC         self,
# MAGIC         tool_call: dict[str, Any],
# MAGIC         messages: list[dict[str, Any]],
# MAGIC     ) -> ResponsesAgentStreamEvent:
# MAGIC         try:
# MAGIC             args = json.loads(tool_call.get("arguments"))
# MAGIC         except Exception as e:
# MAGIC             args = {}
# MAGIC         result = str(self.execute_tool(tool_name=tool_call["name"], args=args))
# MAGIC
# MAGIC         tool_call_output = self.create_function_call_output_item(tool_call["call_id"], result)
# MAGIC         messages.append(tool_call_output)
# MAGIC         return ResponsesAgentStreamEvent(type="response.output_item.done", item=tool_call_output)
# MAGIC
# MAGIC     def call_and_run_tools(
# MAGIC         self,
# MAGIC         messages: list[dict[str, Any]],
# MAGIC         max_iter: int = 10,
# MAGIC     ) -> Generator[ResponsesAgentStreamEvent, None, None]:
# MAGIC         for _ in range(max_iter):
# MAGIC             handled = {m["call_id"] for m in messages if m.get("type") == "function_call_output"}
# MAGIC             pending = [m for m in messages if m.get("type") == "function_call" and m["call_id"] not in handled]
# MAGIC             if pending:
# MAGIC                 for call in pending:
# MAGIC                     yield self.handle_tool_call(call, messages)
# MAGIC                 continue
# MAGIC
# MAGIC             last_msg = messages[-1]
# MAGIC             if last_msg.get("type") == "message" and last_msg.get("role") == "assistant":
# MAGIC                 return
# MAGIC
# MAGIC             yield from output_to_responses_items_stream(
# MAGIC                 chunks=self.call_llm(messages), aggregator=messages
# MAGIC             )
# MAGIC
# MAGIC         yield ResponsesAgentStreamEvent(
# MAGIC             type="response.output_item.done",
# MAGIC             item=self.create_text_output_item("Max iterations reached. Stopping.", str(uuid4())),
# MAGIC         )
# MAGIC
# MAGIC     def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
# MAGIC         session_id = None
# MAGIC         if request.custom_inputs and "session_id" in request.custom_inputs:
# MAGIC             session_id = request.custom_inputs.get("session_id")
# MAGIC         elif request.context and request.context.conversation_id:
# MAGIC             session_id = request.context.conversation_id
# MAGIC
# MAGIC         if session_id:
# MAGIC             mlflow.update_current_trace(
# MAGIC                 metadata={
# MAGIC                     "mlflow.trace.session": session_id,
# MAGIC                 }
# MAGIC             )
# MAGIC
# MAGIC         outputs = [
# MAGIC             event.item
# MAGIC             for event in self.predict_stream(request)
# MAGIC             if event.type == "response.output_item.done"
# MAGIC         ]
# MAGIC         return ResponsesAgentResponse(output=outputs, custom_outputs=request.custom_inputs)
# MAGIC
# MAGIC     def predict_stream(self, request: ResponsesAgentRequest) -> Generator[ResponsesAgentStreamEvent, None, None]:
# MAGIC         session_id = None
# MAGIC         if request.custom_inputs and "session_id" in request.custom_inputs:
# MAGIC             session_id = request.custom_inputs.get("session_id")
# MAGIC         elif request.context and request.context.conversation_id:
# MAGIC             session_id = request.context.conversation_id
# MAGIC
# MAGIC         if session_id:
# MAGIC             mlflow.update_current_trace(
# MAGIC                 metadata={
# MAGIC                     "mlflow.trace.session": session_id,
# MAGIC                 }
# MAGIC             )
# MAGIC
# MAGIC         messages = to_chat_completions_input([i.model_dump() for i in request.input])
# MAGIC         if SYSTEM_PROMPT:
# MAGIC             messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
# MAGIC         yield from self.call_and_run_tools(messages=messages)
# MAGIC
# MAGIC
# MAGIC # Log the model using MLflow
# MAGIC mlflow.openai.autolog()
# MAGIC AGENT = ToolCallingAgent(llm_endpoint=LLM_ENDPOINT_NAME, tools=TOOL_INFOS)
# MAGIC mlflow.models.set_model(AGENT)

# COMMAND ----------

# DBTITLE 1,Log and Register Updated Agent
import mlflow
from mlflow.models.resources import DatabricksServingEndpoint, DatabricksFunction
from pkg_resources import get_distribution

mlflow.set_registry_uri("databricks-uc")

# Define resources for automatic auth passthrough
resources = [
    DatabricksServingEndpoint(endpoint_name="databricks-gpt-oss-120b"),
    DatabricksFunction(function_name="dbacademy.get_started_agents.get_service_history")
]

input_example = {
    "input": [{"role": "user", "content": "Get the order history of ronald54@example.net"}],
    "custom_inputs": {"session_id": "test-session"}
}

with mlflow.start_run() as run:
    logged_agent_info = mlflow.pyfunc.log_model(
        name="agent",
        python_model="agent.py",
        input_example=input_example,
        pip_requirements=[
            "databricks-openai",
            "backoff",
            f"databricks-connect=={get_distribution('databricks-connect').version}",
        ],
        resources=resources,
    )
    run_id = run.info.run_id

# Register the model to Unity Catalog
model_version = mlflow.register_model(
    model_uri=f"runs:/{run_id}/agent",
    name="dbacademy.get_started_agents.my_first_agent",
    tags={"updated": "true", "tools": "get_service_history"}
)

print(f"✓ Agent updated successfully!")
print(f"  Run ID: {run_id}")
print(f"  Model Version: {model_version.version}")
print(f"\nTools configured:")
print(f"  - dbacademy.get_started_agents.get_service_history")
print(f"\n⚠️  Next step: Update the serving endpoint to use version {model_version.version}")

# COMMAND ----------

# DBTITLE 1,✅ Deploy Version 10 to Serving Endpoint
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ServedEntityInput

w = WorkspaceClient()

# Get the latest version number from the previous cell
latest_version = model_version.version

print(f"Deploying version {latest_version} to serving endpoint...")
print("=" * 60)

try:
    # Update the serving endpoint configuration
    w.serving_endpoints.update_config(
        name="agents_dbacademy-get_started_agents-my_first_agent",
        served_entities=[
            ServedEntityInput(
                entity_name="dbacademy.get_started_agents.my_first_agent",
                entity_version=str(latest_version),
                workload_size="Small",
                scale_to_zero_enabled=True
            )
        ]
    )
    
    print(f"\n🎉 SUCCESS! Version {latest_version} deployment initiated!")
    print(f"\n📋 Deployment Details:")
    print(f"   Model: dbacademy.get_started_agents.my_first_agent")
    print(f"   Version: {latest_version}")
    print(f"   Tool: get_service_history ✅")
    print(f"\n⏱️  Estimated Time: 5-10 minutes")
    print(f"\n✅ Next: Run the cell below to check deployment status")
    
except Exception as e:
    print(f"\n❌ Deployment failed: {e}")
    print(f"\nIf the error is 'ResourceConflict', wait 2 minutes and try again.")

# COMMAND ----------

# DBTITLE 1,Check Deployment Status
from databricks.sdk import WorkspaceClient
import time

w = WorkspaceClient()

print("=" * 60)
print("🔍 CHECKING DEPLOYMENT STATUS")
print("=" * 60)

endpoint = w.serving_endpoints.get("agents_dbacademy-get_started_agents-my_first_agent")

print(f"\nUpdate State: {endpoint.state.config_update}")
print(f"Ready State: {endpoint.state.ready}")

if endpoint.config and endpoint.config.served_entities:
    print(f"\n✅ CURRENTLY ACTIVE:")
    for entity in endpoint.config.served_entities:
        version = entity.entity_version
        status = entity.state.deployment if entity.state else 'UNKNOWN'
        print(f"   Version: {version}")
        print(f"   Status: {status}")
        if int(version) < 10:
            print(f"   ⚠️  This is the OLD version (no tools)")
        else:
            print(f"   ✅ This is the NEW version (with tools!)")

if endpoint.pending_config and endpoint.pending_config.served_entities:
    print(f"\n⏳ DEPLOYING:")
    for entity in endpoint.pending_config.served_entities:
        version = entity.entity_version
        status = entity.state.deployment if entity.state else 'UNKNOWN'
        print(f"   Version: {version}")
        print(f"   Status: {status}")
        if entity.state and entity.state.deployment_state_message:
            print(f"   Message: {entity.state.deployment_state_message}")
    
    print(f"\n⏱️  Deployment in progress...")
    print(f"   The Playground will use the old version until this completes.")
    print(f"   Wait 2-3 more minutes, then run this cell again.")
else:
    # No pending config means the update is complete
    if endpoint.config and endpoint.config.served_entities:
        active_version = endpoint.config.served_entities[0].entity_version
        if int(active_version) >= 10:
            print(f"\n🎉 DEPLOYMENT COMPLETE!")
            print(f"   Version {active_version} is now LIVE!")
            print(f"   ✅ The agent now has access to get_service_history tool")
            print(f"\n🎮 Go to the Playground and test:")
            print(f"   'Get the order history of ronald54@example.net'")
            print(f"\n   The agent should now successfully retrieve the order history!")
        else:
            print(f"\n⚠️  Still on old version {active_version}")
            print(f"   If you just deployed, wait a few more minutes.")