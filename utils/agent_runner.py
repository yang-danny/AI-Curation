import json
from datetime import datetime
from typing import Dict, Any, Optional, Sequence

from google.adk.runners import InMemoryRunner
from google.genai import types


DEFAULT_RESULT_KEYS: Sequence[str] = (
    'generated_content',
    'social_media_report',
    'curated_content',
    'final_content',
    'blog_post',
    'news_summaries',
    'gathered_posts',
    'gathered_news',
    'analysis',
    'output',
    'result',
    'response',
)


def _normalize_response_payload(payload: Any, result_keys: Sequence[str]) -> Dict[str, Any]:
    """Normalize various payload types into a dict keyed by RESULT_KEYS."""
    if isinstance(payload, dict):
        for key in result_keys:
            if key in payload:
                return {key: payload[key]}
        return payload

    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, dict):
                return _normalize_response_payload(parsed, result_keys)
        except json.JSONDecodeError:
            pass
        return {'output': payload}

    return {'output': str(payload)}


def _extract_payload_from_event(event) -> Optional[Any]:
    """Attempt to pull model output from an ADK event."""
    if getattr(event, 'content', None) and event.content.parts:
        texts = [
            part.text
            for part in event.content.parts
            if getattr(part, 'text', None) and not getattr(part, 'thought', False)
        ]
        if texts:
            return ''.join(texts)

    actions = getattr(event, 'actions', None)
    if actions:
        if getattr(actions, 'state_delta', None):
            return actions.state_delta
        agent_state = getattr(actions, 'agent_state', None)
        if isinstance(agent_state, dict):
            outputs = agent_state.get('outputs')
            if outputs:
                return outputs

    return None


async def run_agent_with_runner(
    agent,
    agent_name: str,
    state: Optional[Dict[str, Any]] = None,
    result_keys: Sequence[str] = DEFAULT_RESULT_KEYS,
) -> Dict[str, Any]:
    """
    Execute a google.adk Agent using the InMemoryRunner and return normalized output.

    Args:
        agent: ADK Agent instance to execute.
        agent_name: Friendly name used for logging and runner naming.
        state: Optional initial state passed to the agent.
        result_keys: Keys to probe when extracting output from session state.
    """
    base_state = {
        "timestamp": datetime.now().isoformat(),
    }
    if state:
        base_state.update(state)

    runner = InMemoryRunner(
        agent=agent,
        app_name=agent_name.replace(" ", "_")
    )

    user_id = "cli_user"
    session_id = f"{agent_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id,
        state=base_state,
    )

    message_content = types.Content(
        role='user',
        parts=[types.Part(text=json.dumps(base_state))]
    )

    events_async_generator = runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message_content
    )

    final_response: Dict[str, Any] = {}

    async for event in events_async_generator:
        if event.is_final_response():
            payload = _extract_payload_from_event(event)
            if payload is not None:
                final_response = _normalize_response_payload(payload, result_keys)
                break

    if not final_response:
        session = await runner.session_service.get_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
        )
        if session and getattr(session, "state", None):
            for key in result_keys:
                if key in session.state:
                    final_response = {key: session.state[key]}
                    break
            if not final_response:
                final_response = {"session_state": session.state}

    if final_response:
        return final_response

    raise RuntimeError(f"{agent_name} did not return any output.")

