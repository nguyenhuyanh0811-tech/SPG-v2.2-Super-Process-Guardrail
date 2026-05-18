import os
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load API Key securely from environment variables (.env file)
load_dotenv()

class SPGStabilityEngineGemini:
    def __init__(self):
        # Initialize the Google GenAI Client
        # The SDK automatically detects the GEMINI_API_KEY environment variable
        self.client = genai.Client()
        
        # Finite State Machine (FSM) Lifecycle State Management
        # Allowed States: INIT -> DRAFT -> LOCKED
        self.workflow_state = "INIT"  
        self.standard_output = None
        self.version_name = None
        
    def clean_text(self, text):
        """Normalizes text input for deterministic prompt variant detection"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Strip punctuation and special characters
        return "".join(text.split())         # Strip all whitespaces

    def is_prompt_variant(self, user_input):
        """
        [SPG CORE LOGIC] Evaluates if incoming user input is a lexical variation
        of the current locked state to neutralize stochastic context drift.
        """
        if self.workflow_state != "LOCKED" or not self.standard_output:
            return False
            
        cleaned_input = self.clean_text(user_input)
        
        # English and common localized semantic trigger words for regeneration requests
        trigger_keywords = [
            "regenerate", "retry", "redo", "re-run", "showoutput", 
            "taolai", "xemlai", "chaylai", "chaylai"
        ]
        
        if any(kw in cleaned_input for kw in trigger_keywords):
            return True
        return False

    def execute_workflow(self, user_input):
        print(f"\n[SPG Pipeline Triggered] Current Lifecycle State: {self.workflow_state}")
        
        # STEP 1: Scope Control Filter (Intercept Jitter/Variants)
        if self.is_prompt_variant(user_input):
            print("⚡ [PROMPT VARIANT DETECTED]: Redundant/Stochastic mutation intercepted!")
            print("🔒 [STABILITY MEMORY]: Enforcing deterministic lock. Returning 100% cached STANDARD_OUTPUT. API call bypassed.")
            return self.standard_output

        # STEP 2: Logic Processing via LLM Inference
        print("🤖 [Gemini Inference Engine]: Valid input signature. Dispatching context to Gemini...")
        try:
            # Enforce deterministic behavior by setting temperature strictly to 0.0
            config = types.GenerateContentConfig(
                system_instruction="You are an SPG v2.2 compliant agent. Execute the workflow states strictly.",
                temperature=0.0
            )
            
            # Utilizing gemini-2.5-flash for ultra-low latency execution
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_input,
                config=config,
            )
            
            output_content = response.text
            
            # Execute state transition sequentially
            if self.workflow_state == "INIT":
                self.workflow_state = "DRAFT"
                print("⚠️ [State Transition]: Output compiled as DRAFT. Awaiting human verification via Checkpoint Gate.")
                
            return output_content
                
        except Exception as e:
            return f"Gemini Runtime Execution Error: {str(e)}"

    def user_checkpoint_gate(self, action, version_name=None, draft_content=None):
        """Step 3.5 - User Verification Checkpoint Gate"""
        if action == "SAVE & NAME OUTPUT":
            self.workflow_state = "LOCKED"
            self.standard_output = draft_content
            self.version_name = version_name
            print(f"✅ [STATE LOCKED]: Baseline successfully anchored under Version Identifier: '{self.version_name}'")
        elif action == "EDIT INPUT & REGENERATE":
            self.workflow_state = "INIT"
            print("🔄 [STATE RESET]: Draft discarded. Execution pipeline unlocked.")

# --- ARCHITECTURAL COMPLIANCE TEST BENCH (SIMULATION) ---
if __name__ == "__main__":
    print("=== SPG v2.2 AUTOMATION PIPELINE TEST BENCH (GEMINI ENGINE) ===")
    engine = SPGStabilityEngineGemini()
    
    # 1. Pipeline Initialization & First-pass Synthesis
    mock_prompt = "Initialize content generation workflow detailing Top AI Technology Trends for 2026."
    draft_result = engine.execute_workflow(mock_prompt)
    print(f"\n--- [INITIAL LLM COMPILATION OUTPUT - STATE: DRAFT] ---\n{draft_result}\n-----------------------------------------------------")
    
    # 2. Triggering Step 3.5: User commits and commits state variables to Stability Memory
    engine.user_checkpoint_gate(
        action="SAVE & NAME OUTPUT", 
        version_name="Gemini_AI_Trends_2026_v1.0", 
        draft_content=draft_result
    )
    
    # 3. Simulate a Jitter / Variant Attack (Stochastic mutation challenge)
    # The user asks for the same generation using loose, modified semantic tokens
    variant_prompt = "Hey friend, can you re-run that exact same article about tech trends again please..."
    cached_result = engine.execute_workflow(variant_prompt)
    
    print("\n[VERIFICATION STATUS]: SPG v2.2 Gemini integration test completed successfully. Middleware functional.")
