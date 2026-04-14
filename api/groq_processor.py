import os
import re
import requests
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize the Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_url(url: str) -> str:
    """Visits a URL and extracts the readable text for the LLM."""
    print(f"🔗 Scraping website: {url}")
    try:
        # Get the Jina Key from your environment variables
        jina_key = os.getenv("JINA_API_KEY", "")
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        if jina_key:
            headers['Authorization'] = f'Bearer {jina_key}'
            
        # Jina Reader API cleanly extracts text from websites for LLMs
        response = requests.get(f"https://r.jina.ai/{url}", headers=headers, timeout=60)
        
        if response.status_code == 200:
            return f"\n--- SCRAPED WEBSITE CONTENT ---\n{response.text[:3000]}\n-------------------------------\n"
        else:
            print(f"⚠️ Jina API Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"⚠️ Failed to scrape URL: {e}")
    return ""

def process_job_message(raw_text: str) -> str:
    # Using your specific reasoning models hosted on Groq
    models = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-safeguard-20b"
    ]

    # 1️⃣ URL DETECTION & "ONLY URL" LOGIC
    urls = re.findall(r'(https?://[^\s]+)', raw_text)
    scraped_content = ""
    is_only_url = False
    
    if urls:
        # Check if the entire message is literally just the URL (ignoring spaces)
        if raw_text.strip() == urls[0]:
            is_only_url = True
            print("👀 Message is ONLY a link! Relying entirely on the web scraper.")
            
        scraped_content = extract_text_from_url(urls[0])
        
        # Safety net: If it was ONLY a link, but the website blocked our scraper
        if is_only_url and not scraped_content:
            return "Error: Message contained only a link, and the website blocked our scraper from reading it."

    # 2️⃣ THE BULLETPROOF PROMPT
    prompt = f"""
    You are a professional technical recruiter AI filtering IT jobs/internships for college students and recent grads.

    Analyze the provided data. If the original message was just a link, rely entirely on the SCRAPED WEBSITE CONTENT.

    🚨 STRICT FILTERING RULES (ABORT IF FAILED) 🚨
    If the data violates ANY of these rules, respond EXACTLY with: "Error: Pipeline failed to process job description."
    1. Maximum Experience: If the job EXPLICITLY demands strictly MORE than 2 years of experience (e.g., "3+ years", "Senior"), abort.
    2. Invalid Links: If the apply link goes to a LinkedIn , WhatsApp group, or Telegram channel, abort. (Direct career pages, Google Forms, and HR emails are perfectly valid).

    📝 FORMATTING RULES 📝
    If it passes, format it into a clean layout for WhatsApp/Telegram.
    - Extract: Role, Company, Eligible Batches, Experience Required, and Application Link / Email.
    - ⚠️ CRITICAL: If an HR email is provided for applying (e.g., hr@company.com), you MUST extract it and display it as "How to Apply: [Email]". Do not say "Not Mentioned".
    - ⚠️ CRITICAL: If the RAW NOTIFICATION MESSAGE contains a URL, or is entirely a URL, you MUST use that exact URL as the "Application Link". NEVER say "Not Mentioned" if a URL is present in the raw message.
    - ⚠️ CRITICAL FORMATTING: Do NOT use asterisks (*) or markdown for bolding. It breaks the platform UI. You MUST use plain text with the exact emojis shown below:
    - 💼 Role: [Extract]
    🏢 Company: [Extract]
    🎓 Eligible Batches: [Extract]
    ⏳ Experience Required: [Extract]
    🔗 How to Apply: [Extract link or HR email]
    
    🛑 ANTI-HALLUCINATION RULES 🛑
    - Do NOT guess or assume the Eligible Batch. If it is not explicitly stated in the text, you MUST write "Not Mentioned". Do NOT default to "2025-2028".
    - Do NOT guess the Experience Required. If it is not explicitly stated, you MUST write "Not Mentioned". Do NOT default to "0-2 years".

    At the very bottom, append this exact text:
    
    "For more off campus hiring updates, you can also join our communities: 

    WhatsApp Community: https://whatsapp.com/channel/0029VbCV0MJ7DAWuhgumFH2B

    Telegram Community: https://t.me/offcampusnoncorejobs

    Connect with me (insta): https://www.instagram.com/mahtab2ahmad1?igsh=MWhueXU1bHU1Z3R1ag==

    Connect with me (linkedin): https://www.linkedin.com/in/mahtab007/

    Regards,
    Mahtab Ahmad"

    RAW NOTIFICATION MESSAGE:
    {raw_text}
    
    {scraped_content}
    """

    for model in models:
        try:
            print(f"🧠 Processing with reasoning model: {model}...")
            
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2, # Extremely strict temperature
                max_completion_tokens=2000,
                top_p=1,
                reasoning_effort="medium", # 🧠 Required for gpt-oss models
                stream=True,
            )

            final_formatted_text = ""
            for chunk in completion:
                final_formatted_text += chunk.choices[0].delta.content or ""
            
            if final_formatted_text:
                return final_formatted_text

        except Exception as e:
            print(f"❌ Model {model} failed: {e}")
            continue

    return "Error: Pipeline failed to process job description."