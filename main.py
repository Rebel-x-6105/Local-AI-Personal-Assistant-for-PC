import sys
import re
from pydantic import ValidationError
from app.startup import print_startup_banner, print_shutdown_message, get_time_based_greeting
from app.assistant import JarvisAssistant
from app.logger import logger
from voice.text_to_speech import TextToSpeechManager
from voice.speech_to_text import SpeechToTextManager

def remove_system_brackets(text: str) -> str:
    """Removes bracketed system notifications (e.g. [System Alert]) from speech output."""
    # Strip matches like [System Alert] or [System Diagnostic: ...]
    cleaned = re.sub(r'\[System[^\]]*\]', '', text)
    # Strip generic metadata brackets like [DONE] or [System Error]
    cleaned = re.sub(r'\[[^\]]*\]', '', cleaned)
    return cleaned.strip()

def main() -> None:
    """Main execution entry point for the JARVIS terminal assistant."""
    # 1. Config Verification Phase
    try:
        from app.config import get_settings
        settings = get_settings()
    except ValidationError as val_err:
        print("\n========================================================")
        print("                  SYSTEM BOOT FAILURE                  ")
        print("========================================================")
        print("Configuration validation failed. Please check your .env file.")
        print("\nIdentified Errors:")
        for err in val_err.errors():
            field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
            print(f" - [{field_path}]: {err.get('msg')}")
        print("\nSetup Checklist:")
        print(" 1. Ensure a '.env' file exists in the root folder.")
        print(" 2. Confirm 'OPENAI_API_KEY' is populated with a valid key.")
        print("========================================================\n")
        sys.exit(1)
    except Exception as exc:
        print(f"\nCritical Boot Failure: {exc}")
        sys.exit(1)

    user_name = settings.jarvis_user_name

    # Initialize voice services if enabled
    tts_manager = None
    stt_manager = None
    settings_voice_enabled = False

    if settings.voice_enabled:
        try:
            tts_manager = TextToSpeechManager()
            stt_manager = SpeechToTextManager()
            settings_voice_enabled = True
            logger.info("Speech recognition and synthesis modules loaded successfully.")
        except Exception as voice_err:
            logger.error(f"Failed to load audio input/output modules: {voice_err}")
            print("\n[System Warning] Microphone or audio devices could not be loaded.")
            print("Falling back to text-only mode.\n")
            settings_voice_enabled = False

    # 2. Booting Phase
    print_startup_banner(user_name)

    try:
        assistant = JarvisAssistant()
    except Exception as exc:
        logger.critical(f"Failed to load JARVIS engine: {exc}", exc_info=True)
        print(f"AI Engine load failed. Please see logs/jarvis.log for details.")
        sys.exit(1)

    # Synthesize the boot greeting aloud
    if settings_voice_enabled and tts_manager:
        greeting_text = f"{get_time_based_greeting(user_name)} How may I assist you today?"
        tts_manager.speak(greeting_text)

    # 3. Dialogue Loop Phase
    try:
        while True:
            # Use dynamic labels depending on if voice capture is online
            prompt_label = "You (Press Enter to speak, or type): " if settings_voice_enabled else "You: "
            
            try:
                user_input = input(prompt_label).strip()
            except (KeyboardInterrupt, EOFError):
                # Clean exit on Ctrl+C or Ctrl+D
                print()
                break

            # Handle empty prompt inputs
            if not user_input:
                if settings_voice_enabled and stt_manager:
                    try:
                        # Capture voice input via sounddevice/VAD
                        user_input = stt_manager.listen_and_recognize()
                        if not user_input:
                            # Silence or timeout: loop back to prompt
                            continue
                        print(f"You (Voice): {user_input}")
                    except Exception as stt_err:
                        logger.error(f"Speech acquisition failed: {stt_err}")
                        print("[System Alert] Voice module error. Falling back to keyboard typing.")
                        continue
                else:
                    # In text-only mode, ignore blank submissions
                    continue

            # Process exit keywords
            if user_input.lower() in ("exit", "quit", "bye", "stop", "goodbye"):
                break

            # Streams response text token by token to the console
            print("Jarvis: ", end="", flush=True)
            response_chunks = []
            sentence_buffer = ""
            try:
                for chunk in assistant.handle_user_input_stream(user_input):
                    print(chunk, end="", flush=True)
                    response_chunks.append(chunk)

                    if settings_voice_enabled and tts_manager:
                        sentence_buffer += chunk
                        # Split by sentence endings (.!? followed by space, or newline)
                        # Avoid splitting on common honorifics (Mr, Ms, Mrs, Dr, Sr, Jr)
                        sentences = re.split(
                            r'(?<!\bMr)(?<!\bMs)(?<!\bMrs)(?<!\bDr)(?<!\bSr)(?<!\bJr)(?<=[.!?])\s+|\n',
                            sentence_buffer
                        )
                        if len(sentences) > 1:
                            # Speak all completed sentences
                            for sentence in sentences[:-1]:
                                clean_sentence = remove_system_brackets(sentence)
                                if clean_sentence.strip():
                                    tts_manager.speak(clean_sentence)
                            # Keep the last incomplete sentence in the buffer
                            sentence_buffer = sentences[-1]
            except Exception as stream_err:
                logger.error(f"Error streaming dialogue turn: {stream_err}", exc_info=True)
                print(f"\n[System Error] Dialogue stream broke down. Error: {stream_err}")
            
            # Print spacing for the next interaction
            print("\n")

            # Speak any remaining text left in the buffer after streaming completes
            if settings_voice_enabled and tts_manager and sentence_buffer.strip():
                clean_sentence = remove_system_brackets(sentence_buffer)
                if clean_sentence.strip():
                    tts_manager.speak(clean_sentence)

    except Exception as runtime_err:
        logger.critical(f"Uncaught session crash: {runtime_err}", exc_info=True)
        print(f"\n[System Crash] Core system failure: {runtime_err}")
    finally:
        # 4. Shutdown Phase
        try:
            assistant.shutdown()
        except Exception as shutdown_err:
            logger.error(f"Error during shutdown routine: {shutdown_err}")
        
        # Say goodbye aloud before closing down
        if settings_voice_enabled and tts_manager:
            shutdown_greeting = f"Powering down system modules. Have a pleasant day, {user_name}."
            try:
                tts_manager.speak(shutdown_greeting)
            except Exception:
                pass
        
        print_shutdown_message(user_name)

if __name__ == "__main__":
    main()
