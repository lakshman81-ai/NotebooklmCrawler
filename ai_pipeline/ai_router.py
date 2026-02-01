from ai_pipeline.notebooklm import run_notebooklm
from ai_pipeline.deepseek import run_deepseek
import os
import logging

logger = logging.getLogger(__name__)

def notebooklm_available():
    # Mock check - in real world check API keys or service status
    return os.getenv("NOTEBOOKLM_AVAILABLE", "true").lower() == "true"

def deepseek_available():
    return os.getenv("DEEPSEEK_AVAILABLE", "true").lower() == "true"

async def run_ai(chunks, context, page):
    """
    Routes execution based on available AI backends.
    """
    logger.info("AI Router decision point")
    
    discovery_method = (context or {}).get('discovery_method', 'auto').lower()

    if notebooklm_available():
        if discovery_method == 'notebooklm':
            logger.info("Routing to NotebookLM Source Discovery Flow")
            return await run_notebooklm([], context, page)
        
        logger.info("Routing to Mode A (Two-Stage: NotebookLM -> DeepSeek)")
        evidence = await run_notebooklm(chunks, context, page)
        return run_deepseek(evidence, context)

    elif deepseek_available():
        logger.info("Routing to Mode B (Fallback: DeepSeek only)")
        return run_deepseek(chunks, context)

    else:
        logger.error("No AI backend available")
        raise RuntimeError("No AI backend available")
