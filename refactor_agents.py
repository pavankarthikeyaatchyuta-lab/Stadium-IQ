import os
import re

agent_dir = "backend/agents"
for filename in os.listdir(agent_dir):
    if filename.endswith(".py") and filename not in ["__init__.py", "gemini_utils.py", "sustainability_agent.py"]:
        filepath = os.path.join(agent_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replacements
        content = content.replace('model_name="gemini-1.5-flash"', "model_name=GEMINI_MODEL")
        
        # Imports
        content = content.replace(
            "from backend.agents.gemini_utils import generate_gemini_text",
            "from backend.agents.gemini_utils import generate_gemini_text_async\nfrom backend.config import GEMINI_MODEL"
        )
        
        # Async methods
        content = re.sub(r'def (answer|analyze|get_priorities|simulate|navigate)\(', r'async def \1(', content)
        
        # Await gemini
        content = content.replace("= generate_gemini_text(", "= await generate_gemini_text_async(")
        
        # Add docstrings if missing (simple generic ones for the file)
        if '"""' not in content[:20]:
            content = f'"""\nAgent module for StadiumIQ: {filename}.\n"""\n' + content
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

print("Agents updated to async and config.")
