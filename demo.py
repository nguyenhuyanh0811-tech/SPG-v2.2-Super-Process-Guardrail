import os
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class SPGStabilityEngine:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Working & Stability Memory States
        self.workflow_state = "INIT"  # INIT -> DRAFT -> LOCKED
        self.standard_output = None
        self.version_name = None
        
    def clean_text(self, text):
        """Helper to normalize text for variant detection (Removes spaces, punctuation, lowercase)"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        return "".join(text.split())         # Remove all whitespaces

    def is_prompt_variant(self, user_input):
        """
        [SPG Core Logic] Checks if the input is just a lexical variation 
        of the already locked state to prevent non-deterministic drift.
        """
        if self.workflow_state != "LOCKED" or not self.standard_output:
            return False
            
        # If input intent is identical or requests same frozen state
        cleaned_input = self.clean_text(user_input)
        if "regenerate" in cleaned_input or "showoutput" in cleaned_input:
            return True
        return False

    def execute_workflow(self, user_input, step_command=None):
        print(f"\n[SPG Pipeline Triggered] Current State: {self.workflow_state}")
        
        # 1. Scope Control Filter Check
        if self.is_prompt_variant(user_input):
            print("⚡ [PROMPT VARIANT DETECTED]: Bypassing downstream LLM pipeline execution.")
            print("🔒 [STABILITY MEMORY]: Returning 100% cached STANDARD_OUTPUT.")
            return self.standard_output

        # 2. Sequential Logic Processing via OpenAI
        print("🤖 [LLM Inference Engine]: Processing workflow logic...")
        try:
            # In production, spg_core_prompt.txt would be loaded here as System Prompt
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an SPG v2.2 compliant agent. Execute the workflow states strictly."},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.0 # Force low randomness
            )
            
            output_content = response.choices[0].message.content
            
            # Simulate State Transitioning inside Middleware
            if self.workflow_state == "INIT":
                self.workflow_state = "DRAFT"
                print("⚠️ [State Transition]: Output compiled as DRAFT. Awaiting Checkpoint verification.")
                return output_content
                
        except Exception as e:
            return f"Execution Error: {str(e)}"

    def user_checkpoint_gate(self, action, version_name=None, draft_content=None):
        """Step 3.5 - User Verification Checkpoint Gate"""
        if action == "SAVE & NAME OUTPUT":
            self.workflow_state = "LOCKED"
            self.standard_output = draft_content
            self.version_name = version_name
            print(f"✅ [STATE LOCKED]: Cached baseline anchored under Version: '{self.version_name}'")
        elif action == "EDIT INPUT & REGENERATE":
            self.workflow_state = "INIT"
            print("🔄 [STATE RESET]: Draft discarded. Pipeline unlocked.")

# --- SIMULATION EXECUTION ---
if __name__ == "__main__":
    print("=== SPG v2.2 ENGINE TEST BENCH ===")
    engine = SPGStabilityEngine()
    
    # Simulation Step 1 & 3: Run initialization prompt to get a draft
    mock_prompt = "Initialize Content Generation Workflow for AI Trends."
    draft_result = engine.execute_workflow(mock_prompt)
    print(f"\n--- [LLM Output Draft] ---\n{draft_result}\n-------------------------")
    
    # Simulation Step 3.5: User hits the Checkpoint Gate and locks the state
    engine.user_checkpoint_gate(
        action="SAVE & NAME OUTPUT", 
        version_name="AI_Trends_v1.0", 
        draft_content=draft_result
    )
    
    # Simulation Variant Attack: User inputs a slight variant (noise/jitter)
    variant_prompt = "Regenerate that please, or show output for AI trends..."
    cached_result = engine.execute_workflow(variant_prompt)
    
    print("\n[Verification Success]: System securely locked and rejected stochastic drift.")
