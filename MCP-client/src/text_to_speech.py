import re
import asyncio
import azure.cognitiveservices.speech as speechsdk
import concurrent.futures
from app import app_state
from dotenv import load_dotenv
load_dotenv()

async def text_to_speech(text, speech_key, speech_region, ws_manager=None, voice_name='en-US-JennyNeural'):
    if not text.strip():
        raise ValueError("Text is empty. Cannot synthesize speech.")

    # Initialize events if they don't exist
    if app_state.pause_event is None:
        app_state.pause_event = asyncio.Event()
    if app_state.stop_event is None:
        app_state.stop_event = asyncio.Event()
    
    app_state.pause_event.clear()
    app_state.stop_event.clear()

    def escape_xml(t):
        return (t.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

    safe_text = escape_xml(text)
    parts = re.split(r'([.?!,;])', safe_text)
    parts = [p.strip() for p in parts if p.strip()]

    emphasis_keywords = [
        "Model Context Protocol", "MCP", "open standard", "real-time", "structured information",
        "effective AI deployment", "decision-making", "modularity", "data integration challenges",
        "universal remote", "standardizes communication", "efficiency", "scalability",
        "client-server model", "MCP Host", "MCP Client", "MCP Server",
        "enterprise AI assistants", "productivity", "insights", "GraphQL support",
        "SDKs", "workflows", "automating tasks", "market leadership",
        "industry standard", "best practices", "AI integration", "secure data handling"
    ]

    low_pitch_slow_keywords = [
        "Anthropic", "security", "privacy", "sensitive data", "confidential", "data integrity",
        "TLS encryption", "OAuth 2", "Role-Based Access Control", "RBAC",
        "client profiles", "financial reports", "backbone", "contextual data",
        "reliable communication", "secure architecture", "trust", "compliance"
    ]

    pitch_cycle = ['+3%', '0%', '-5%', '0%']
    rate_cycle = ['+8%', '+5%', '0%', '+5%']
    cycle_len = len(pitch_cycle)
    idx = 0
    
    ssml_body = ""

    for part in parts:
        for kw in emphasis_keywords:
            part = re.sub(fr"\b({re.escape(kw)})\b",
                        r"<emphasis level='moderate'>\1</emphasis>",
                        part, flags=re.IGNORECASE)
        for kw in low_pitch_slow_keywords:
            part = re.sub(fr"\b({re.escape(kw)})\b",
                        r"<prosody pitch='-5%' rate='0%'>\1</prosody>",
                        part, flags=re.IGNORECASE)

        pitch = pitch_cycle[idx % cycle_len]
        rate = rate_cycle[idx % cycle_len]

        ssml_body += f"<prosody pitch='{pitch}' rate='{rate}'>{part}</prosody>"

        # if part.endswith(('.', '?', '!')):
        #     ssml_body += "<break time='400ms'/> "
        # elif part.endswith((',', ';')):
        if part.endswith((',', ';')):
            ssml_body += "<break time='200ms'/> "
        else:
            ssml_body += " "

        idx += 1

    ssml = f"""
    <speak version='1.0' 
            xmlns='http://www.w3.org/2001/10/synthesis' 
            xmlns:mstts='http://www.w3.org/2001/mstts' 
            xml:lang='en-US'>
        <voice name='{voice_name}'>
        <mstts:express-as style='cheerful' styledegree='2'>
            {ssml_body.strip()}
        </mstts:express-as>
        </voice>
    </speak>
    """

    # Azure config
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_synthesis_voice_name = voice_name
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    app_state.synthesizer = synthesizer

    loop = asyncio.get_running_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    if ws_manager:
        await ws_manager.emit("talking")

    print("📣 Starting speech synthesis with pause/resume support...")

    # Run synthesis
    synthesis_future = loop.run_in_executor(
        executor,
        lambda: synthesizer.speak_ssml_async(ssml).get()
    )

    stop_future = asyncio.create_task(app_state.stop_event.wait())
    pause_future = asyncio.create_task(app_state.pause_event.wait())

    done, pending = await asyncio.wait(
        [synthesis_future, stop_future, pause_future],
        return_when=asyncio.FIRST_COMPLETED
    )

    # Handle pause
    if pause_future in done and app_state.pause_event.is_set():
        print("⏸️ Paused by user.")
        synthesizer.stop_speaking()

        if ws_manager:
            await ws_manager.emit("not_talking")

        app_state.pause_event.clear()

        # Wait for resume or stop
        resume_future = asyncio.create_task(app_state.pause_event.wait())
        stop_while_paused = asyncio.create_task(app_state.stop_event.wait())

        done_resume, _ = await asyncio.wait(
            [resume_future, stop_while_paused],
            return_when=asyncio.FIRST_COMPLETED
        )

        if stop_while_paused in done_resume and app_state.stop_event.is_set():
            print("🛑 Stopped while paused.")
            if ws_manager:
                await ws_manager.emit("not_talking")
            raise Exception("Speech stopped during pause")
        else:
            print("▶️ Resumed")
            # if ws_manager:
            #     await ws_manager.emit("talking")
            return await text_to_speech(text, speech_key, speech_region, ws_manager, voice_name)

    # Handle stop
    if stop_future in done and app_state.stop_event.is_set():
        print("🛑 Interrupted")
        synthesizer.stop_speaking()
        if ws_manager:
            await ws_manager.emit("not_talking")
        raise Exception("Speech interrupted by stop")

    # Handle synthesis result
    try:
        result = await synthesis_future
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("✅ Synthesis completed")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            raise Exception(f"Speech canceled: Reason={cancellation.reason}, Details={cancellation.error_details}")
    finally:
        if ws_manager:
            await ws_manager.emit("not_talking")