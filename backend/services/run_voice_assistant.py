"""
Standalone script to run the full voice assistant.
This provides system-wide voice control for your laptop.
"""

from voice_assistant import VoiceAssistant

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 VOICE ASSISTANT - FULL LAPTOP CONTROL")
    print("=" * 60)
    print("\nThis assistant can control:")
    print("  • Applications (launch any app)")
    print("  • File system (open folders, search files)")
    print("  • Windows (switch, list, manage)")
    print("  • System info (battery, CPU, memory)")
    print("  • Browser (all Chrome commands)")
    print("  • System actions (lock, sleep, shutdown)")
    print("\n" + "=" * 60)
    
    assistant = VoiceAssistant()
    
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        assistant.stop()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        assistant.stop()

