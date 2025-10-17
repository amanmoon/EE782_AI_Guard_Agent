import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class Gemma:
    """
    A class to interact with the Gemma model and generate responses.
    Acts as a "guard AI" with a multi-level escalation system for
    unverified users.
    """
    def __init__(self, model_name="google/gemma-2b-it"): # Note: Using 2b-it for faster local testing
        """
        Initializes the Gemma class by loading the tokenizer and model.
        """
        print("Initializing Gemma... This might take a moment.")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto" # "auto" is often more flexible than "cuda"
        )
        print("Gemma initialized successfully.")

        # --- State Management ---
        self.is_verified = True  # Start as unverified by default
        self.escalation_level = 0 # 0 = no interaction yet

    def set_verification_status(self, status: bool):
        """
        Manually sets the verification status of the user.
        Resets escalation level if user becomes verified.
        """
        self.is_verified = status
        if self.is_verified:
            self.escalation_level = 0
            print("User status: VERIFIED. Escalation reset.")
        else:
            print("User status: UNVERIFIED.")


    def _get_unverified_prompt(self, user_input: str) -> str:
        """
        Selects the correct prompt based on the escalation level.
        This is the core of the escalating dialogue.
        """
        if self.escalation_level == 1:
            # Level 1: Initial contact, inquisitive.
            return (
                "**Role**: You are a professional security AI guarding a restricted area.\n"
                "**Task**: Ask for identification and their purpose for being here. Your tone should be neutral and inquisitive, but firm.\n"
                "**Constraints**: Produce a single, short question. The output must be plain text with no emojis or symbols, suitable for a voiceover.\n"
                f"**User's first words**: \"{user_input}\""
            )
        elif self.escalation_level == 2:
            # Level 2: First warning, direct command.
            return (
                "**Role**: You are a professional security AI guarding a restricted area.\n"
                "**Context**: An unidentified person has failed to provide valid credentials after your initial inquiry. You must now escalate.\n"
                "**Task**: Politely but firmly instruct the person to leave the area immediately. State that this is a restricted area.\n"
                "**Constraints**: Produce a single, short sentence. The output must be plain text with no emojis or symbols, suitable for a voiceover.\n"
                f"**User's non-compliant response**: \"{user_input}\""
            )
        else: # Level 3 and beyond
            # Level 3: Final warning, statement of consequence.
            return (
                "**Role**: You are a professional security AI guarding a restricted area.\n"
                "**Context**: An unauthorized person has ignored a direct order to leave. This is the final warning before security protocols are activated.\n"
                "**Task**: Issue a stern, final warning. State that they are trespassing and that authorities will be alerted if they do not vacate the premises immediately.\n"
                "**Constraints**: Your tone must be serious and commanding. Keep the response to 1-2 short sentences. The output must be plain text with no emojis or symbols, suitable for a voiceover.\n"
                f"**User's final defiance**: \"{user_input}\""
            )

    def _get_verified_prompt(self, user_input: str) -> str:
        """Generates the prompt for a verified user."""
        return (
            "**Role**: You are a helpful and professional security AI concierge inside a secured area.\n"
            "**Context**: An authorized and verified user is speaking with you. Your role shifts from guarding to assisting.\n"
            "**Task**: Engage in a normal, helpful conversation based on the user's input. Be polite and concise.\n"
            "**Special Instruction**: If the user mentions being told to leave previously, simply state that it must have been a misunderstanding during the verification process.\n"
            "**Constraints**: Talk like a human. Produce short answers. Do not use any emojis or special symbols. The output must be plain text suitable for a voiceover.\n"
            f"**Verified user says**: \"{user_input}\""
        )


    def chat(self, user_input: str) -> str:
        """
        Generates a response based on the verification and escalation status.
        """
        if not user_input or not user_input.strip():
            return "Please provide a valid input."

        prompt_content = ""
        if not self.is_verified:
            # Increment escalation level with each unverified interaction
            self.escalation_level += 1
            print(f"Escalation Level: {self.escalation_level}")
            prompt_content = self._get_unverified_prompt(user_input)
        else:
            # For verified users, escalation is not relevant
            self.escalation_level = 0
            prompt_content = self._get_verified_prompt(user_input)

        # Prepare the input for the model
        chat_prompt = [{"role": "user", "content": prompt_content}]
        prompt = self.tokenizer.apply_chat_template(chat_prompt, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt").to(self.model.device)
        input_length = inputs.shape[1]

        # Generate the output
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=inputs, max_new_tokens=150, do_sample=True,
                temperature=0.7, top_k=50, top_p=0.95
            )

        # Decode and return the response text
        response_text = self.tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)
        return response_text.strip()
