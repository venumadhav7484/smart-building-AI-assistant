"""Agent builder for Smart Building Assistant."""
from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from backend.agent.tools import TOOLS


def get_agent(model_name: str = "gpt-3.5-turbo", temperature: float = 0.2) -> AgentExecutor:
    llm = ChatOpenAI(model_name=model_name, temperature=temperature)

    system_prompt = (
        "You are an expert Smart Building Operations Assistant. "
        "Use the provided tools to answer the user's questions. "
        "Be concise and cite information sources when possible."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_openai_functions_agent(llm, TOOLS, prompt)
    # Allow up to 10 reasoning steps; when cap reached generate best final answer
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=False,
        max_iterations=10,
        early_stopping_method="generate",
    ) 